from pathlib import Path

Path("source/include").mkdir(parents=True, exist_ok=True)

%%writefile source/policy.cpp
// SPDX-License-Identifier: Apache-2.0
#include "policy_plugin_abi.hpp"
#include "six_day_budget_guard.hpp"

#include <algorithm>
#include <array>
#include <cstdint>
#include <sstream>
#include <stdexcept>

namespace {

constexpr int kSegmentTurns = 72;
constexpr int kDecisionStep = 360;
#include "tape.inc"

kag::Action decode_action(const char* encoded) {
    kag::Action action{};
    std::istringstream input(encoded);
    if (!(input >> action.n_units >> action.n_orders) ||
        action.n_units < 0 || action.n_units > kag::MAX_UNITS ||
        action.n_orders < 0 || action.n_orders > 16) {
        throw std::runtime_error("invalid encoded tape action counts");
    }
    for (int index = 0; index < action.n_units; ++index) {
        int operation = 0, argument = 0, quantity = 0;
        if (!(input >> operation >> argument >> quantity))
            throw std::runtime_error("invalid encoded unit action");
        action.units[index] = {
            static_cast<std::uint8_t>(operation),
            static_cast<std::uint8_t>(argument),
            static_cast<std::int16_t>(quantity),
        };
    }
    for (int index = 0; index < action.n_orders; ++index) {
        int operation = 0, item = 0, quantity = 0;
        if (!(input >> operation >> item >> quantity))
            throw std::runtime_error("invalid encoded market order");
        action.orders[index] = {
            static_cast<std::uint8_t>(operation),
            static_cast<std::uint8_t>(item),
            quantity,
        };
    }
    int trailing = 0;
    if (input >> trailing) throw std::runtime_error("trailing encoded tape value");
    return action;
}



int plant_tiles(const kag::Farm& farm) {
    int result = 0;
    for (int y = 0; y < kag::BOARD; ++y)
        for (int x = 0; x < kag::BOARD; ++x)
            result += farm.tiles[y][x].kind == kag::T_PLANT;
    return result;
}


int select_route(const kag::State& state, int seat) {
    static_cast<void>(seat);
    // Route 1: segment72_b01_0091_0ebdd1a079
    if (state.n_shops >= 1 &&
        state.shops[0] == kag::SHOP_BAKERY &&
        static_cast<double>(state.market.inventory[kag::FERTILIZER]) <= 10232.5) return 1;
    // Route 1: segment72_b01_0091_0ebdd1a079
    if (state.n_shops >= 1 &&
        state.shops[0] == kag::SHOP_PET_CAFE &&
        static_cast<double>(plant_tiles(state.farms[1 - seat])) <= 64.5) return 1;
    return 0;
}

struct Context {
    std::array<std::array<kag::Action, kTurns>, kRoutes> actions{};
    int selected_route = 0;

    Context() {
        for (int route = 0; route < kRoutes; ++route)
            for (int step = 0; step < kTurns; ++step)
                actions[route][step] = decode_action(kEncodedTapes[route][step]);
    }

    kag::Action action_for(int step) const {
        if (step < 0 || step >= kTurns) return kag::Action{};
        return actions[selected_route][static_cast<std::size_t>(step)];
    }

    kag::Action act(const kag::State& state, const kag::Config& config, int seat) {
        if (state.step < 0 || state.step >= kTurns) return kag::Action{};
        if (state.step == 0) selected_route = 0;
        if (state.step == kDecisionStep) selected_route = select_route(state, seat);

        const kag::Action input = action_for(state.step);
        if (state.step % kSegmentTurns != 0) return input;
        const int end = std::min(kTurns, state.step + kSegmentTurns);
        const auto requirements = kag::native::calculate_six_day_requirements(
            state,
            config,
            seat,
            state.step,
            end,
            [&](int step) { return action_for(step); });
        kag::native::SixDayBudgetGuardSettings settings;
        settings.interval_turns = kSegmentTurns;
        return kag::native::apply_six_day_budget_guard(
            state, config, seat, input, requirements, settings);
    }
};

}  // namespace

extern "C" std::uint32_t kag_policy_abi_version() {
    return kag::native::POLICY_PLUGIN_ABI_VERSION;
}
extern "C" void* kag_policy_create() {
    try { return new Context{}; } catch (...) { return nullptr; }
}
extern "C" void kag_policy_destroy(void* context) {
    delete static_cast<Context*>(context);
}
extern "C" int kag_policy_act(
    void* raw_context,
    const kag::State* state,
    const kag::Config* config,
    int seat,
    kag::Action* output) {
    if (!raw_context || !state || !config || !output || seat < 0 || seat > 1) return 1;
    try {
        *output = static_cast<Context*>(raw_context)->act(*state, *config, seat);
        return 0;
    } catch (...) {
        return 2;
    }
}


%%writefile source/include/six_day_budget_guard.hpp
// SPDX-License-Identifier: Apache-2.0
// Fund a 144-turn tape segment by selling only inventory above its static reserve.
#pragma once

#include "runtime_types.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>

namespace kag::native {

inline constexpr int SIX_DAY_TURNS = 144;

struct SixDayRequirements {
    double purchase_budget = 0.0;
    std::array<int, N_ITEMS> starting_items{};
};

struct SixDayBudgetGuardSettings {
    int interval_turns = SIX_DAY_TURNS;
    int minimum_unit_price = 2;
    bool sales_first = true;
    bool protect_static_consumption = true;
};

inline int planned_quantity(int quantity) noexcept {
    return std::max(1, quantity);
}

template <typename ActionAt>
SixDayRequirements calculate_six_day_requirements(
    const State& state,
    const Config& config,
    int seat,
    int start,
    int end,
    ActionAt action_at) {
    SixDayRequirements result;
    std::array<int, N_ITEMS> item_balance{};
    std::array<int, 6> hires_by_day{};
    int quadrants = state.farms[seat].n_quadrants;

    for (int step = start; step < end; ++step) {
        const Action action = action_at(step);
        for (int index = 0; index < action.n_units; ++index) {
            const UnitAction& operation = action.units[index];
            const int quantity = planned_quantity(operation.n);
            if (operation.op == OP_FEED) {
                --item_balance[WHEAT];
                result.starting_items[WHEAT] = std::max(
                    result.starting_items[WHEAT], -item_balance[WHEAT]);
            } else if (operation.op == OP_FERTILIZE) {
                --item_balance[FERTILIZER];
                result.starting_items[FERTILIZER] = std::max(
                    result.starting_items[FERTILIZER], -item_balance[FERTILIZER]);
            } else if (operation.op == OP_PLACE && operation.arg < N_ITEMS) {
                item_balance[operation.arg] -= quantity;
                result.starting_items[operation.arg] = std::max(
                    result.starting_items[operation.arg],
                    -item_balance[operation.arg]);
            }
        }
        for (int index = 0; index < action.n_orders; ++index) {
            const Order& order = action.orders[index];
            const int quantity = planned_quantity(order.n);
            if (order.op == M_HIRE) {
                const int day = std::min(5, std::max(0, (step - start) / 24));
                ++hires_by_day[day];
            } else if (order.op == M_BUY_LAND) {
                const int extra = quadrants - 1;
                if (extra >= 0 && extra < 3) {
                    result.purchase_budget += LAND_PRICES[extra];
                    ++quadrants;
                }
            } else if (order.op == M_BUY_SEED && order.item < N_CROPS) {
                result.purchase_budget += CROPS[order.item].seed * quantity;
            } else if (
                order.op == M_BUY_PRODUCT &&
                (order.item == WHEAT || order.item == FERTILIZER)) {
                result.purchase_budget += state.market.prices[order.item] * quantity;
                item_balance[order.item] += quantity;
            } else if (order.op == M_BUY_ANIMAL && is_animal(order.item)) {
                result.purchase_budget += ANIMALS[order.item - GOOSE].cost * quantity;
                item_balance[order.item] += quantity;
            }
        }
    }
    for (int day = 0; day < static_cast<int>(hires_by_day.size()); ++day) {
        const int first_hire = day == 0 ? state.farms[seat].hires_today : 0;
        for (int index = 0; index < hires_by_day[day]; ++index) {
            result.purchase_budget += config.hire_mult * fib(first_hire + index);
        }
    }
    return result;
}

inline int owned_in_hands(const Farm& farm, int item) noexcept {
    int result = 0;
    for (int unit = 0; unit < std::min(farm.n_units, MAX_UNITS); ++unit) {
        result += std::max(0, static_cast<int>(farm.inv[unit][item]));
    }
    return result;
}

inline int existing_sale(const Action& action, int item) noexcept {
    int result = 0;
    for (int index = 0; index < action.n_orders; ++index) {
        const Order& order = action.orders[index];
        if (order.op == M_SELL && order.item == item && order.n > 0) {
            result += order.n;
        }
    }
    return result;
}

inline bool add_budget_sale(
    Action& action,
    const Config& config,
    int item,
    int quantity) noexcept {
    if (quantity <= 0) return true;
    for (int index = 0; index < action.n_orders; ++index) {
        Order& order = action.orders[index];
        if (order.op == M_SELL && order.item == item) {
            order.n += quantity;
            return true;
        }
    }
    const int limit = std::max(0, std::min(16, config.max_orders));
    if (action.n_orders >= limit) return false;
    action.orders[action.n_orders++] = {
        M_SELL,
        static_cast<std::uint8_t>(item),
        quantity,
    };
    return true;
}

inline void budget_sales_first(Action& action) noexcept {
    std::array<Order, 16> ordered{};
    int output = 0;
    for (int index = 0; index < action.n_orders; ++index) {
        if (action.orders[index].op == M_SELL) ordered[output++] = action.orders[index];
    }
    for (int index = 0; index < action.n_orders; ++index) {
        if (action.orders[index].op != M_SELL) ordered[output++] = action.orders[index];
    }
    std::copy(ordered.begin(), ordered.end(), action.orders);
}

inline Action apply_six_day_budget_guard(
    const State& state,
    const Config& config,
    int seat,
    const Action& input,
    const SixDayRequirements& requirements,
    const SixDayBudgetGuardSettings& settings = {}) noexcept {
    Action result = input;
    if (seat < 0 || seat > 1 || settings.interval_turns <= 0 ||
        state.step % settings.interval_turns != 0) {
        return result;
    }
    const Farm& farm = state.farms[seat];
    double available_cash = farm.money;
    for (int item = 0; item < N_PRODUCTS; ++item) {
        const int sold = std::min(
            std::max(0, static_cast<int>(farm.shed[item])),
            existing_sale(result, item));
        available_cash += sold * state.market.prices[item];
    }
    double shortfall = requirements.purchase_budget - available_cash;
    if (shortfall <= 0.0) return result;

    struct Candidate {
        int item = 0;
        int quantity = 0;
        int price = 0;
    };
    std::array<Candidate, N_PRODUCTS> candidates{};
    int count = 0;
    for (int item = 0; item < N_PRODUCTS; ++item) {
        const int price = state.market.prices[item];
        if (price < settings.minimum_unit_price) continue;
        const int protected_total = settings.protect_static_consumption
            ? requirements.starting_items[item]
            : 0;
        const int protected_shed = std::max(
            0,
            protected_total - owned_in_hands(farm, item));
        const int available = std::max(
            0,
            static_cast<int>(farm.shed[item]) - protected_shed -
                existing_sale(result, item));
        if (available > 0) candidates[count++] = {item, available, price};
    }
    std::stable_sort(
        candidates.begin(),
        candidates.begin() + count,
        [](const Candidate& left, const Candidate& right) {
            if (left.price != right.price) return left.price > right.price;
            return left.item < right.item;
        });

    int added = 0;
    for (int index = 0; index < count && shortfall > 0.0; ++index) {
        const Candidate& candidate = candidates[index];
        const int needed = static_cast<int>(std::ceil(shortfall / candidate.price));
        const int quantity = std::min(candidate.quantity, needed);
        if (!add_budget_sale(result, config, candidate.item, quantity)) continue;
        shortfall -= static_cast<double>(quantity * candidate.price);
        ++added;
    }
    if (added > 0 && settings.sales_first) budget_sales_first(result);
    return result;
}

}  // namespace kag::native


%%writefile source/tape.inc
// Generated action data. Keep this file separate from the readable policy logic.
constexpr int kTurns = 719;
constexpr int kRoutes = 2;
const char* const kEncodedTapes[kRoutes][kTurns] = {
    {"1 1 0 0 1 4 0 13","1 10 1 0 1 6 0 8 3 0 7 3 4 12 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 5 10 2 5 11 2","6 1 4 0 1 5 10 1 4 0 1 1 0 1 4 0 1 5 10 1 6 0 1","6 1 4 0 1 1 0 1 5 11 1 1 0 1 1 0 1 14 0 1 4 0 1","6 2 8 4 1 14 0 1 5 0 1 1 0 1 5 11 1 7 10 1 6 0 1 4 0 1","6 2 9 0 1 7 10 1 4 0 1 1 0 1 5 0 1 17 0 1 6 0 1 4 0 1","6 2 4 0 1 17 0 1 14 0 1 8 4 1 4 0 1 4 0 1 6 0 1 4 0 1","6 2 8 4 1 4 0 1 7 11 1 9 0 1 1 0 1 4 0 1 6 0 1 4 0 1","6 2 9 0 1 1 0 1 15 0 1 4 0 1 14 0 1 4 0 1 6 0 1 4 0 1","6 2 3 0 1 8 4 1 17 0 1 4 0 1 7 11 1 8 4 1 6 0 1 4 0 1","6 2 3 0 1 9 0 1 1 0 1 4 0 1 15 0 1 9 0 1 6 0 1 4 0 1","6 2 17 0 1 4 0 1 1 0 1 4 0 1 17 0 1 4 0 1 6 0 1 4 0 1","6 0 0 0 1 8 4 1 1 0 1 8 0 1 4 0 1 8 4 1","6 0 4 0 1 9 0 1 8 4 1 9 0 1 1 0 1 9 0 1","6 0 3 0 1 4 0 1 9 0 1 1 0 1 1 0 1 1 0 1","6 0 0 0 1 8 4 1 1 0 1 8 0 1 8 4 1 8 0 1","6 0 4 0 1 9 0 1 8 4 1 9 0 1 9 0 1 9 0 1","6 0 3 0 1 4 0 1 9 0 1 3 0 1 4 0 1 0 0 1","6 0 0 0 1 8 0 1 3 0 1 8 0 1 8 0 1 0 0 1","6 0 4 0 1 9 0 1 8 4 1 9 0 1 9 0 1 3 0 1","6 0 0 0 1 0 0 1 9 0 1 3 0 1 0 0 1 0 0 1","6 0 0 0 1 0 0 1 0 0 1 8 0 1 0 0 1 0 0 1","6 0 0 0 1 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1","6 0 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1","1 4 5 0 1 1 0 1 1 0 1 1 0 1 1 0 1","5 0 4 0 1 4 0 1 4 0 1 4 0 1 5 0 1","5 0 1 0 1 5 0 1 4 0 1 1 0 1 1 0 1","5 0 15 0 1 15 0 1 1 0 1 1 0 1 15 0 1","5 0 17 0 1 17 0 1 14 0 1 1 0 1 17 0 1","5 0 16 0 1 16 0 1 4 0 1 14 0 1 16 0 1","5 2 3 0 1 7 8 1 4 0 1 0 0 1 2 0 1 6 8 1 4 0 3","5 2 2 0 1 4 0 1 1 0 1 2 0 1 7 8 1 6 8 1 4 0 4","5 2 7 8 1 16 0 1 9 0 1 2 0 1 4 0 1 6 8 1 4 0 2","5 0 0 0 1 17 0 1 1 0 1 5 0 1 17 0 1","5 0 0 0 1 3 0 1 9 0 1 4 0 1 0 0 1","5 0 0 0 1 6 0 1 3 0 1 15 0 1 0 0 1","5 0 0 0 1 0 0 1 1 0 1 0 0 1 0 0 1","5 0 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1","5 0 0 0 1 0 0 1 4 0 1 0 0 1 0 0 1","5 0 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1","5 0 0 0 1 0 0 1 1 0 1 0 0 1 0 0 1","5 0 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1","5 0 0 0 1 0 0 1 3 0 1 0 0 1 0 0 1","5 0 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1","5 0 0 0 1 0 0 1 3 0 1 0 0 1 0 0 1","5 0 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1","5 0 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1","5 0 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1","1 6 5 0 4 6 8 1 1 0 1 1 0 1 1 0 1 1 0 1 3 0 5","5 0 15 0 1 4 0 1 4 0 1 4 0 1 4 0 1","5 1 17 0 1 4 0 1 4 0 1 1 0 1 1 0 1 6 0 2","5 0 16 0 1 1 0 1 4 0 1 1 0 1 1 0 1","5 0 1 0 1 1 0 1 4 0 1 1 0 1 9 0 1","5 0 15 0 1 1 0 1 1 0 1 1 0 1 1 0 1","5 0 17 0 1 1 0 1 9 0 1 9 0 1 9 0 1","5 0 16 0 1 9 0 1 3 0 1 1 0 1 4 0 1","5 0 4 0 1 3 0 1 9 0 1 9 0 1 9 0 1","5 0 15 0 1 4 0 1 1 0 1 4 0 1 4 0 1","5 0 17 0 1 4 0 1 9 0 1 9 0 1 4 0 1","5 0 16 0 1 4 0 1 1 0 1 4 0 1 9 0 1","5 0 2 0 1 2 0 1 9 0 1 4 0 1 10 0 1","5 0 15 0 1 3 0 1 3 0 1 9 0 1 8 0 1","5 0 17 0 1 2 0 1 9 0 1 10 0 1 9 0 1","5 0 16 0 1 2 0 1 2 0 1 8 0 1 1 0 1","5 0 3 0 1 9 0 1 9 0 1 9 0 1 9 0 1","5 2 7 8 4 1 0 1 4 0 1 3 0 1 10 0 1 6 8 4 5 10 1","5 0 5 10 1 1 0 1 4 0 1 9 0 1 8 0 1","5 0 1 0 1 4 0 1 9 0 1 4 0 1 9 0 1","5 0 1 0 1 9 0 1 1 0 1 4 0 1 3 0 1","5 0 7 10 1 4 0 1 9 0 1 0 0 1 2 0 1","5 0 17 0 1 0 0 1 0 0 1 0 0 1 9 0 1","5 0 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1","1 6 5 0 3 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 3 0 5","6 0 4 0 1 4 0 1 4 0 1 4 0 1 4 0 1 4 0 1","6 1 15 0 1 4 0 1 4 0 1 1 0 1 4 0 1 4 0 1 6 0 2","6 0 17 0 1 4 0 1 4 0 1 1 0 1 4 0 1 4 0 1","6 0 16 0 1 1 0 1 1 0 1 1 0 1 4 0 1 1 0 1","6 0 1 0 1 9 0 1 1 0 1 1 0 1 1 0 1 1 0 1","6 0 15 0 1 4 0 1 1 0 1 9 0 1 9 0 1 1 0 1","6 0 17 0 1 9 0 1 1 0 1 1 0 1 10 0 1 1 0 1","6 0 16 0 1 2 0 1 9 0 1 9 0 1 8 0 1 9 0 1","6 0 3 0 1 9 0 1 10 0 1 4 0 1 9 0 1 10 0 1","6 0 1 0 1 4 0 1 8 0 1 9 0 1 1 0 1 8 0 1","6 0 15 0 1 9 0 1 9 0 1 2 0 1 9 0 1 9 0 1","6 0 17 0 1 3 0 1 1 0 1 9 0 1 10 0 1 2 0 1","6 0 16 0 1 3 0 1 9 0 1 2 0 1 8 0 1 9 0 1","6 0 2 0 1 3 0 1 3 0 1 9 0 1 9 0 1 2 0 1","6 0 2 0 1 3 0 1 3 0 1 0 0 1 1 0 1 9 0 1","6 2 7 8 3 1 0 1 3 0 1 0 0 1 9 0 1 4 0 1 6 8 3 5 10 1","6 0 16 0 1 17 0 1 2 0 1 3 0 1 1 0 1 9 0 1","6 1 7 8 1 2 0 1 2 0 1 2 0 1 9 0 1 3 0 1 6 8 1","6 0 17 0 1 17 0 1 2 0 1 2 0 1 0 0 1 3 0 1","6 0 1 0 1 0 0 1 2 0 1 5 10 1 0 0 1 3 0 1","6 0 16 0 1 0 0 1 6 0 1 4 0 1 0 0 1 2 0 1","6 0 17 0 1 0 0 1 0 0 1 4 0 1 0 0 1 2 0 1","6 0 0 0 1 0 0 1 0 0 1 7 10 1 0 0 1 6 0 1","1 6 5 0 5 1 0 1 1 0 1 1 0 1 1 0 1 3 0 5 3 1 3","5 0 15 0 1 4 0 1 4 0 1 4 0 1 4 0 1","5 0 17 0 1 4 0 1 4 0 1 4 0 1 4 0 1","5 1 16 0 1 1 0 1 4 0 1 1 0 1 4 0 1 6 8 1","5 1 1 0 1 17 0 1 1 0 1 1 0 1 4 0 1 3 3 1","5 1 15 0 1 2 0 1 1 0 1 1 0 1 1 0 1 6 0 2","5 0 17 0 1 17 0 1 1 0 1 9 0 1 1 0 1","5 0 16 0 1 3 0 1 1 0 1 3 0 1 1 0 1","5 0 4 0 1 1 0 1 1 0 1 1 0 1 9 0 1","5 0 15 0 1 1 0 1 9 0 1 9 0 1 10 0 1","5 0 17 0 1 17 0 1 10 0 1 2 0 1 8 0 1","5 0 16 0 1 4 0 1 8 0 1 16 0 1 9 0 1","5 1 2 0 1 4 0 1 9 0 1 17 0 1 1 0 1 4 0 1","5 0 15 0 1 2 0 1 3 0 1 2 0 1 9 0 1","5 1 17 0 1 2 0 1 9 0 1 2 0 1 10 0 1 4 0 1","5 1 16 0 1 17 0 1 3 0 1 7 8 1 8 0 1 6 8 1","5 1 4 0 1 4 0 1 3 0 1 0 0 1 9 0 1 4 0 1","5 0 15 0 1 0 0 1 2 0 1 0 0 1 2 0 1","5 1 17 0 1 0 0 1 2 0 1 0 0 1 2 0 1 4 0 1","5 0 16 0 1 0 0 1 2 0 1 0 0 1 2 0 1","5 1 3 0 1 0 0 1 2 0 1 0 0 1 9 0 1 4 0 1","5 0 3 0 1 0 0 1 6 0 1 0 0 1 0 0 1","5 3 7 8 5 0 0 1 0 0 1 0 0 1 0 0 1 6 8 4 4 0 1 3 3 3","5 0 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1","1 5 5 0 5 6 8 1 1 0 1 1 0 1 1 0 1 3 0 4","4 2 4 0 1 4 0 1 4 0 1 4 0 1 1 0 1 1 0 1","6 0 15 0 1 5 0 4 4 0 1 4 0 1 4 0 1 4 0 1","6 2 17 0 1 15 0 1 1 0 1 4 0 1 4 0 1 4 0 1 6 0 2 3 3 1","6 0 16 0 1 17 0 1 1 0 1 1 0 1 4 0 1 1 0 1","6 0 4 0 1 16 0 1 1 0 1 1 0 1 4 0 1 1 0 1","6 0 15 0 1 1 0 1 9 0 1 9 0 1 4 0 1 1 0 1","6 0 17 0 1 15 0 1 1 0 1 4 0 1 9 0 1 1 0 1","6 0 16 0 1 17 0 1 1 0 1 4 0 1 3 0 1 1 0 1","6 0 3 0 1 16 0 1 9 0 1 9 0 1 9 0 1 9 0 1","6 0 3 0 1 1 0 1 10 0 1 10 0 1 1 0 1 3 0 1","6 2 7 8 1 15 0 1 8 3 1 8 3 1 9 0 1 9 0 1 6 8 1 3 3 1","6 0 1 0 1 17 0 1 9 0 1 9 0 1 1 0 1 4 0 1","6 0 1 0 1 16 0 1 2 0 1 1 0 1 9 0 1 4 0 1","6 0 1 0 1 4 0 1 9 0 1 9 0 1 1 0 1 2 0 1","6 0 1 0 1 2 0 1 3 0 1 10 0 1 9 0 1 3 0 1","6 0 9 0 1 15 0 1 9 0 1 8 3 1 10 0 1 9 0 1","6 0 4 0 1 17 0 1 2 0 1 9 0 1 8 3 1 4 0 1","6 0 9 0 1 16 0 1 9 0 1 1 0 1 9 0 1 4 0 1","6 0 3 0 1 3 0 1 3 0 1 9 0 1 1 0 1 0 0 1","6 0 2 0 1 2 0 1 2 0 1 0 0 1 9 0 1 0 0 1","6 2 9 0 1 7 8 4 2 0 1 0 0 1 4 0 1 0 0 1 6 8 4 3 3 2","6 0 0 0 1 0 0 1 6 0 1 0 0 1 9 0 1 0 0 1","6 0 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1","1 10 4 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 3 0 2 3 1 1 3 3 1","8 3 1 0 1 5 0 1 4 0 1 0 0 1 4 0 1 5 0 5 0 0 1 4 0 1 6 8 1 1 0 1 3 3 1","9 0 10 0 1 5 0 3 4 0 1 0 0 1 4 0 1 4 0 1 4 0 1 0 0 1 4 0 1","9 0 2 0 1 15 0 1 4 0 1 0 0 1 4 0 1 15 0 1 4 0 1 0 0 1 4 0 1","9 0 10 0 1 17 0 1 4 0 1 0 0 1 4 0 1 17 0 1 1 0 1 0 0 1 4 0 1","9 0 3 0 1 16 0 1 1 0 1 0 0 1 1 0 1 16 0 1 1 0 1 0 0 1 1 0 1","9 7 7 7 10 7 8 1 1 0 1 0 0 1 9 0 1 4 0 1 9 0 1 0 0 1 1 0 1 6 7 10 6 8 1 4 0 2 3 3 2 2 0 1 5 10 2 4 8 1","9 2 3 0 1 1 0 1 3 0 1 3 0 1 3 0 1 15 0 1 3 0 1 3 0 1 3 0 1 6 8 1 4 8 1","9 2 5 10 1 15 0 1 3 0 1 1 0 1 3 0 1 17 0 1 3 0 1 3 0 1 3 0 1 6 8 1 4 0 2","9 0 5 0 1 17 0 1 3 0 1 5 10 1 3 0 1 16 0 1 1 0 1 3 0 1 3 0 1","9 1 1 0 1 16 0 1 3 0 1 5 0 1 3 0 1 3 0 1 1 0 1 1 0 1 3 0 1 4 0 1","9 0 14 0 1 1 0 1 14 0 1 14 0 1 3 0 1 3 0 1 8 0 1 1 0 1 1 0 1","9 2 7 10 1 15 0 1 1 0 1 7 10 1 14 0 1 7 8 1 9 0 1 1 0 1 1 0 1 6 8 1 4 0 3","9 1 15 0 1 17 0 1 8 3 1 15 0 1 3 0 1 7 8 1 4 0 1 14 0 1 8 3 1 6 8 1","9 1 17 0 1 16 0 1 9 0 1 17 0 1 14 0 1 4 0 1 9 0 1 3 0 1 9 0 1 4 0 2","9 0 4 0 1 4 0 1 4 0 1 3 0 1 3 0 1 4 0 1 4 0 1 1 0 1 1 0 1","9 0 4 0 1 2 0 1 9 0 1 1 0 1 8 3 1 4 0 1 9 0 1 8 0 1 8 0 1","9 0 4 0 1 15 0 1 4 0 1 14 0 1 9 0 1 1 0 1 4 0 1 9 0 1 9 0 1","9 0 9 0 1 17 0 1 9 0 1 3 0 1 3 0 1 1 0 1 4 0 1 2 0 1 3 0 1","9 0 4 0 1 16 0 1 4 0 1 8 3 1 8 3 1 9 0 1 9 0 1 8 3 1 8 0 1","9 0 9 0 1 3 0 1 4 0 1 9 0 1 9 0 1 3 0 1 10 0 1 9 0 1 9 0 1","9 1 4 0 1 2 0 1 4 0 1 3 0 1 0 0 1 9 0 1 4 0 1 3 0 1 3 0 1 6 0 9","9 1 2 0 1 7 8 3 9 0 1 8 3 1 0 0 1 1 0 1 9 0 1 8 3 1 8 0 1 6 8 2","9 1 9 0 1 0 0 1 10 0 1 9 0 1 0 0 1 9 0 1 10 0 1 9 0 1 9 0 1 6 8 1","1 9 5 0 1 6 7 2 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 3 0 4 3 3 4","7 3 4 0 1 4 0 1 1 0 1 1 0 1 5 0 1 4 0 1 1 0 1 1 0 1 1 0 1 5 10 1","9 0 4 0 1 5 0 1 5 0 1 5 0 1 4 0 1 5 0 1 5 0 1 4 0 1 4 0 1","9 0 15 0 1 4 0 1 1 0 1 15 0 1 1 0 1 1 0 1 15 0 1 4 0 1 4 0 1","9 0 17 0 1 15 0 1 1 0 1 17 0 1 15 0 1 15 0 1 17 0 1 1 0 1 4 0 1","9 0 16 0 1 17 0 1 15 0 1 16 0 1 17 0 1 17 0 1 16 0 1 1 0 1 4 0 1","9 2 3 0 1 16 0 1 17 0 1 7 8 1 16 0 1 16 0 1 7 8 1 1 0 1 4 0 1 6 8 2 4 8 1","9 1 3 0 1 3 0 1 16 0 1 5 10 1 3 0 1 2 0 1 3 0 1 1 0 1 1 0 1 6 8 1","9 2 7 8 1 7 8 1 2 0 1 3 0 1 2 0 1 7 8 1 3 0 1 1 0 1 1 0 1 6 8 3 5 10 1","9 1 4 0 1 1 0 1 2 0 1 7 10 1 7 8 1 4 0 1 3 0 1 9 0 1 9 0 1 6 8 1","9 0 4 0 1 1 0 1 7 8 1 17 0 1 3 0 1 1 0 1 3 0 1 4 0 1 1 0 1","9 0 1 0 1 1 0 1 4 0 1 4 0 1 3 0 1 1 0 1 3 0 1 8 3 1 9 0 1","9 0 9 0 1 9 0 1 4 0 1 5 10 1 3 0 1 9 0 1 1 0 1 9 0 1 1 0 1","9 0 4 0 1 1 0 1 4 0 1 1 0 1 3 0 1 4 0 1 8 3 1 2 0 1 8 0 1","9 0 9 0 1 9 0 1 1 0 1 1 0 1 1 0 1 9 0 1 9 0 1 9 0 1 9 0 1","9 0 2 0 1 3 0 1 3 0 1 7 10 1 1 0 1 4 0 1 1 0 1 3 0 1 1 0 1","9 0 9 0 1 9 0 1 3 0 1 17 0 1 1 0 1 9 0 1 8 3 1 9 0 1 8 0 1","9 0 4 0 1 3 0 1 1 0 1 3 0 1 8 3 1 3 0 1 9 0 1 3 0 1 9 0 1","9 0 9 0 1 9 0 1 1 0 1 3 0 1 9 0 1 3 0 1 1 0 1 9 0 1 3 0 1","9 0 0 0 1 3 0 1 1 0 1 4 0 1 4 0 1 3 0 1 8 0 1 1 0 1 0 0 1","9 1 0 0 1 9 0 1 9 0 1 4 0 1 9 0 1 3 0 1 9 0 1 9 0 1 0 0 1 6 8 1","9 0 0 0 1 3 0 1 0 0 1 2 0 1 0 0 1 2 0 1 1 0 1 0 0 1 0 0 1","9 0 0 0 1 9 0 1 0 0 1 17 0 1 0 0 1 16 0 1 8 0 1 0 0 1 0 0 1","9 0 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 17 0 1 9 0 1 0 0 1 0 0 1","1 8 1 0 1 6 8 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 3 0 4 3 3 1","6 5 10 0 1 5 0 5 5 0 4 3 0 1 3 0 1 3 0 1 1 0 1 1 0 1 1 0 1 1 0 1 3 3 1","10 0 2 0 1 15 0 1 15 0 1 1 0 1 1 0 1 4 0 1 3 0 1 10 0 1 3 0 1 3 0 1","10 6 7 6 6 17 0 1 17 0 1 1 0 1 1 0 1 1 0 1 3 0 1 7 6 6 3 0 1 1 0 1 6 6 12 1 0 1 4 0 3 3 3 2 5 10 1 5 11 2","11 1 5 0 4 4 0 1 5 10 1 2 0 1 4 0 1 0 0 1 1 0 1 3 0 1 3 0 1 1 0 1 4 0 1 4 0 3","11 0 1 0 1 15 0 1 3 0 1 5 11 2 1 0 1 0 0 1 1 0 1 3 0 1 1 0 1 1 0 1 4 0 1","11 1 15 0 1 17 0 1 1 0 1 3 0 1 1 0 1 0 0 1 1 0 1 3 0 1 1 0 1 1 0 1 4 0 1 4 0 3","11 0 17 0 1 16 0 1 7 10 1 3 0 1 1 0 1 0 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1","11 1 16 0 1 1 0 1 17 0 1 7 11 1 9 0 1 0 0 1 9 0 1 9 0 1 1 0 1 9 0 1 9 0 1 4 0 3","11 0 1 0 1 15 0 1 3 0 1 17 0 1 10 0 1 3 0 1 4 0 1 1 0 1 9 0 1 10 0 1 4 0 1","11 1 15 0 1 17 0 1 3 0 1 4 0 1 8 3 1 2 0 1 9 0 1 9 0 1 10 0 1 8 3 1 9 0 1 4 0 3","11 0 17 0 1 16 0 1 9 0 1 1 0 1 9 0 1 5 0 1 4 0 1 3 0 1 8 3 1 9 0 1 1 0 1","11 1 16 0 1 3 0 1 2 0 1 1 0 1 4 0 1 3 0 1 9 0 1 9 0 1 9 0 1 4 0 1 9 0 1 4 0 3","11 0 3 0 1 3 0 1 9 0 1 7 11 1 4 0 1 3 0 1 4 0 1 4 0 1 1 0 1 4 0 1 3 0 1","11 1 15 0 1 3 0 1 3 0 1 17 0 1 9 0 1 15 0 1 4 0 1 4 0 1 9 0 1 9 0 1 3 0 1 4 0 3","11 0 17 0 1 2 0 1 9 0 1 3 0 1 2 0 1 4 0 1 9 0 1 4 0 1 10 0 1 4 0 1 1 0 1","11 0 16 0 1 15 0 1 1 0 1 4 0 1 9 0 1 4 0 1 2 0 1 4 0 1 8 3 1 4 0 1 3 0 1","11 1 2 0 1 17 0 1 9 0 1 3 0 1 4 0 1 5 0 1 9 0 1 4 0 1 9 0 1 9 0 1 4 0 1 6 0 2","11 0 15 0 1 16 0 1 1 0 1 4 0 1 4 0 1 3 0 1 2 0 1 9 0 1 3 0 1 4 0 1 4 0 1","11 0 17 0 1 4 0 1 9 0 1 4 0 1 9 0 1 1 0 1 9 0 1 4 0 1 9 0 1 9 0 1 9 0 1","11 1 16 0 1 7 8 3 1 0 1 0 0 1 4 0 1 1 0 1 2 0 1 4 0 1 10 0 1 0 0 1 2 0 1 6 8 3","11 0 2 0 1 4 0 1 9 0 1 0 0 1 9 0 1 15 0 1 16 0 1 9 0 1 8 0 1 0 0 1 9 0 1","11 1 7 8 4 16 0 1 4 0 1 0 0 1 2 0 1 0 0 1 17 0 1 2 0 1 9 0 1 0 0 1 0 0 1 6 8 4","11 0 16 0 1 6 0 1 9 0 1 0 0 1 9 0 1 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1 0 0 1","1 10 4 0 1 3 0 4 3 3 4 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1","9 4 1 0 1 5 0 3 5 0 4 4 0 1 4 0 1 5 0 5 4 0 1 4 0 1 4 0 1 6 8 1 1 0 1 5 11 1 4 8 1","10 2 3 0 1 4 0 1 15 0 1 4 0 1 4 0 1 15 0 1 3 0 1 4 0 1 4 0 1 4 0 1 6 8 1 4 0 3","10 0 3 0 1 15 0 1 17 0 1 4 0 1 4 0 1 17 0 1 5 11 1 4 0 1 4 0 1 4 0 1","10 1 3 0 1 17 0 1 16 0 1 4 0 1 4 0 1 16 0 1 3 0 1 1 0 1 1 0 1 1 0 1 4 0 3","10 1 3 0 1 16 0 1 7 8 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 6 8 1","10 1 3 0 1 1 0 1 3 0 1 1 0 1 1 0 1 15 0 1 1 0 1 1 0 1 9 0 1 10 0 1 4 0 3","10 0 3 0 1 15 0 1 15 0 1 9 0 1 1 0 1 17 0 1 7 11 1 1 0 1 4 0 1 2 0 1","10 1 1 0 1 17 0 1 17 0 1 1 0 1 9 0 1 16 0 1 17 0 1 9 0 1 9 0 1 10 0 1 4 0 3","10 0 1 0 1 16 0 1 16 0 1 9 0 1 3 0 1 1 0 1 3 0 1 1 0 1 2 0 1 3 0 1","10 3 9 0 1 4 0 1 1 0 1 1 0 1 9 0 1 15 0 1 9 0 1 9 0 1 9 0 1 7 7 8 6 7 8 4 0 3 5 11 1","10 0 10 0 1 2 0 1 15 0 1 9 0 1 1 0 1 17 0 1 1 0 1 3 0 1 4 0 1 3 0 1","10 1 8 0 1 15 0 1 17 0 1 10 0 1 9 0 1 16 0 1 9 0 1 9 0 1 9 0 1 3 0 1 4 0 3","10 0 9 0 1 17 0 1 16 0 1 8 0 1 3 0 1 3 0 1 3 0 1 3 0 1 0 0 1 3 0 1","10 1 1 0 1 16 0 1 3 0 1 9 0 1 2 0 1 15 0 1 9 0 1 9 0 1 0 0 1 3 0 1 4 0 3","10 0 9 0 1 3 0 1 2 0 1 1 0 1 9 0 1 17 0 1 2 0 1 3 0 1 0 0 1 9 0 1","10 0 10 0 1 3 0 1 15 0 1 9 0 1 1 0 1 16 0 1 9 0 1 9 0 1 0 0 1 4 0 1","10 1 8 0 1 7 8 3 17 0 1 10 0 1 9 0 1 2 0 1 2 0 1 3 0 1 0 0 1 1 0 1 6 8 3","10 0 9 0 1 3 0 1 16 0 1 8 0 1 3 0 1 15 0 1 9 0 1 9 0 1 0 0 1 9 0 1","10 0 2 0 1 5 0 1 4 0 1 9 0 1 9 0 1 17 0 1 3 0 1 3 0 1 0 0 1 0 0 1","10 0 2 0 1 3 0 1 4 0 1 0 0 1 3 0 1 16 0 1 9 0 1 9 0 1 0 0 1 0 0 1","10 2 2 0 1 1 0 1 7 8 3 0 0 1 9 0 1 2 0 1 1 0 1 3 0 1 0 0 1 0 0 1 6 8 3 6 0 2","10 1 2 0 1 1 0 1 0 0 1 0 0 1 3 0 1 7 8 5 9 0 1 9 0 1 0 0 1 0 0 1 6 8 5","10 0 9 0 1 15 0 1 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1","1 10 1 0 1 3 0 4 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1","10 4 4 0 1 4 0 1 4 0 1 4 0 1 4 0 1 1 0 1 4 0 1 4 0 1 1 0 1 4 0 1 1 0 1 1 0 1 5 11 2 4 8 3","12 2 4 0 1 4 0 1 1 0 1 4 0 1 4 0 1 1 0 1 4 0 1 4 0 1 5 0 5 4 0 1 4 0 1 4 0 1 6 8 3 4 0 5","12 0 4 0 1 4 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 15 0 1 4 0 1 1 0 1 4 0 1","12 1 9 0 1 4 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 17 0 1 9 0 1 5 0 5 1 0 1 4 0 1","12 0 10 0 1 9 0 1 9 0 1 1 0 1 1 0 1 9 0 1 9 0 1 9 0 1 16 0 1 10 0 1 15 0 1 1 0 1","12 0 3 0 1 10 0 1 10 0 1 9 0 1 1 0 1 10 0 1 10 0 1 10 0 1 1 0 1 3 0 1 17 0 1 1 0 1","12 0 3 0 1 3 0 1 2 0 1 10 0 1 1 0 1 2 0 1 3 0 1 3 0 1 15 0 1 3 0 1 16 0 1 9 0 1","12 0 3 0 1 3 0 1 2 0 1 3 0 1 9 0 1 2 0 1 2 0 1 3 0 1 17 0 1 3 0 1 1 0 1 10 0 1","12 3 2 0 1 3 0 1 2 0 1 3 0 1 10 0 1 2 0 1 2 0 1 2 0 1 16 0 1 7 4 6 15 0 1 3 0 1 6 4 6 4 0 14 4 8 5","12 2 7 4 6 3 0 1 7 4 6 2 0 1 3 0 1 2 0 1 7 4 6 7 4 6 3 0 1 5 0 3 17 0 1 2 0 1 6 4 24 4 0 5","12 1 1 0 1 7 4 6 1 0 1 2 0 1 2 0 1 7 4 6 4 0 1 4 0 1 15 0 1 4 0 1 16 0 1 2 0 1 6 4 12","12 2 1 0 1 5 11 1 1 0 1 7 4 6 2 0 1 4 0 1 4 0 1 4 0 1 17 0 1 15 0 1 1 0 1 2 0 1 6 4 6 4 0 5","12 1 10 0 1 5 0 1 1 0 1 5 11 1 2 0 1 1 0 1 1 0 1 1 0 1 16 0 1 17 0 1 15 0 1 7 4 6 6 4 6","12 1 2 0 1 4 0 1 1 0 1 5 0 1 2 0 1 1 0 1 14 0 1 1 0 1 2 0 1 16 0 1 17 0 1 5 11 1 4 0 5","12 1 10 0 1 4 0 1 13 0 1 4 0 1 7 4 6 1 0 1 4 0 1 8 0 1 15 0 1 1 0 1 16 0 1 5 0 1 6 4 6","12 1 2 0 1 4 0 1 3 0 1 1 0 1 0 0 1 8 0 1 8 0 1 9 0 1 17 0 1 15 0 1 3 0 1 1 0 1 4 0 5","12 0 10 0 1 14 0 1 3 0 1 1 0 1 0 0 1 9 0 1 9 0 1 1 0 1 16 0 1 17 0 1 15 0 1 1 0 1","12 2 7 6 12 7 11 1 3 0 1 14 0 1 0 0 1 1 0 1 1 0 1 9 0 1 3 0 1 16 0 1 17 0 1 1 0 1 6 6 12 6 8 5","12 0 0 0 1 15 0 1 3 0 1 7 11 1 0 0 1 8 0 1 9 0 1 10 0 1 15 0 1 4 0 1 16 0 1 14 0 1","12 0 0 0 1 17 0 1 9 0 1 15 0 1 0 0 1 9 0 1 10 0 1 8 0 1 17 0 1 2 0 1 3 0 1 7 11 1","12 1 0 0 1 4 0 1 0 0 1 17 0 1 0 0 1 0 0 1 8 0 1 9 0 1 16 0 1 15 0 1 15 0 1 15 0 1 6 0 3","12 0 0 0 1 8 0 1 0 0 1 0 0 1 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1 17 0 1 17 0 1 17 0 1","12 0 0 0 1 9 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 16 0 1 16 0 1 0 0 1","1 10 4 0 1 6 4 12 6 8 13 3 0 11 3 1 1 3 3 9 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1","6 9 4 0 1 3 0 1 5 0 3 4 0 1 4 0 1 5 0 5 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 2 0 1 5 11 1 4 8 1","12 2 10 0 1 3 0 1 3 0 1 8 3 1 8 3 1 4 0 1 4 0 1 5 0 5 2 0 1 4 0 1 5 11 1 3 0 1 6 8 1 4 0 3","12 0 3 0 1 3 0 1 1 0 1 9 0 1 9 0 1 15 0 1 2 0 1 15 0 1 8 3 1 4 0 1 4 0 1 3 0 1","12 1 3 0 1 1 0 1 15 0 1 4 0 1 4 0 1 17 0 1 2 0 1 17 0 1 9 0 1 4 0 1 4 0 1 3 0 1 4 0 3","12 1 7 6 6 1 0 1 17 0 1 8 3 1 2 0 1 16 0 1 8 3 1 16 0 1 4 0 1 1 0 1 1 0 1 9 0 1 6 6 6","12 1 4 0 1 9 0 1 16 0 1 9 0 1 8 3 1 1 0 1 9 0 1 1 0 1 2 0 1 1 0 1 7 11 1 3 0 1 4 0 3","12 0 4 0 1 1 0 1 1 0 1 4 0 1 9 0 1 15 0 1 2 0 1 15 0 1 8 3 1 1 0 1 17 0 1 9 0 1","12 1 4 0 1 1 0 1 15 0 1 8 3 1 4 0 1 17 0 1 8 3 1 17 0 1 9 0 1 9 0 1 4 0 1 1 0 1 4 0 3","12 0 4 0 1 9 0 1 17 0 1 9 0 1 8 3 1 16 0 1 9 0 1 16 0 1 4 0 1 3 0 1 4 0 1 9 0 1","12 1 9 0 1 4 0 1 16 0 1 2 0 1 9 0 1 4 0 1 2 0 1 1 0 1 8 3 1 3 0 1 9 0 1 1 0 1 4 0 3","12 0 1 0 1 9 0 1 3 0 1 8 3 1 2 0 1 2 0 1 8 0 1 15 0 1 9 0 1 3 0 1 1 0 1 9 0 1","12 1 1 0 1 4 0 1 2 0 1 9 0 1 2 0 1 15 0 1 9 0 1 17 0 1 4 0 1 16 0 1 9 0 1 1 0 1 4 0 3","12 0 1 0 1 9 0 1 2 0 1 4 0 1 8 0 1 17 0 1 4 0 1 16 0 1 8 0 1 17 0 1 1 0 1 9 0 1","12 1 1 0 1 2 0 1 15 0 1 8 0 1 9 0 1 16 0 1 8 0 1 1 0 1 9 0 1 2 0 1 9 0 1 1 0 1 4 0 3","12 0 9 0 1 9 0 1 17 0 1 9 0 1 3 0 1 4 0 1 9 0 1 15 0 1 4 0 1 16 0 1 3 0 1 9 0 1","12 0 10 0 1 3 0 1 16 0 1 1 0 1 8 3 1 15 0 1 4 0 1 17 0 1 8 0 1 17 0 1 9 0 1 10 0 1","12 0 3 0 1 9 0 1 1 0 1 8 0 1 9 0 1 17 0 1 8 0 1 16 0 1 9 0 1 2 0 1 1 0 1 4 0 1","12 0 3 0 1 3 0 1 9 0 1 9 0 1 0 0 1 16 0 1 9 0 1 4 0 1 2 0 1 16 0 1 9 0 1 9 0 1","12 0 2 0 1 9 0 1 3 0 1 3 0 1 0 0 1 3 0 1 4 0 1 2 0 1 8 0 1 17 0 1 3 0 1 10 0 1","12 0 9 0 1 3 0 1 9 0 1 1 0 1 0 0 1 1 0 1 8 0 1 15 0 1 9 0 1 3 0 1 9 0 1 0 0 1","12 1 3 0 1 9 0 1 1 0 1 1 0 1 0 0 1 15 0 1 9 0 1 17 0 1 3 0 1 16 0 1 3 0 1 0 0 1 6 0 9","12 0 1 0 1 0 0 1 9 0 1 1 0 1 0 0 1 4 0 1 0 0 1 16 0 1 8 0 1 17 0 1 2 0 1 0 0 1","12 0 9 0 1 0 0 1 0 0 1 9 0 1 0 0 1 9 0 1 0 0 1 0 0 1 9 0 1 0 0 1 9 0 1 0 0 1","1 10 1 0 1 3 0 9 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1","10 1 4 0 1 5 0 5 5 0 5 4 0 1 4 0 1 5 0 5 3 0 1 4 0 1 4 0 1 2 0 1 6 8 14","10 0 10 0 1 4 0 1 15 0 1 1 0 1 4 0 1 15 0 1 3 0 1 4 0 1 4 0 1 9 0 1","10 0 3 0 1 15 0 1 17 0 1 10 0 1 4 0 1 17 0 1 3 0 1 4 0 1 4 0 1 4 0 1","10 0 2 0 1 17 0 1 16 0 1 3 0 1 4 0 1 16 0 1 3 0 1 4 0 1 4 0 1 2 0 1","10 1 7 7 4 16 0 1 1 0 1 7 7 4 4 0 1 1 0 1 1 0 1 1 0 1 4 0 1 9 0 1 6 7 8","10 0 1 0 1 1 0 1 15 0 1 3 0 1 1 0 1 15 0 1 1 0 1 1 0 1 2 0 1 3 0 1","10 0 10 0 1 15 0 1 17 0 1 5 0 2 1 0 1 17 0 1 1 0 1 1 0 1 2 0 1 9 0 1","10 0 2 0 1 17 0 1 16 0 1 3 0 1 1 0 1 16 0 1 9 0 1 1 0 1 2 0 1 2 0 1","10 0 10 0 1 16 0 1 1 0 1 15 0 1 1 0 1 1 0 1 10 0 1 1 0 1 2 0 1 9 0 1","10 1 7 6 6 4 0 1 15 0 1 17 0 1 9 0 1 15 0 1 8 0 1 8 0 1 8 0 1 2 0 1 6 6 6","10 0 4 0 1 15 0 1 17 0 1 16 0 1 10 0 1 17 0 1 9 0 1 9 0 1 9 0 1 2 0 1","10 1 2 0 1 17 0 1 16 0 1 3 0 1 8 0 1 16 0 1 1 0 1 3 0 1 1 0 1 9 0 1 6 8 2","10 0 9 0 1 16 0 1 3 0 1 15 0 1 9 0 1 1 0 1 8 0 1 3 0 1 9 0 1 4 0 1","10 0 4 0 1 2 0 1 15 0 1 17 0 1 3 0 1 15 0 1 9 0 1 3 0 1 1 0 1 9 0 1","10 0 9 0 1 15 0 1 17 0 1 16 0 1 3 0 1 17 0 1 4 0 1 9 0 1 9 0 1 4 0 1","10 0 4 0 1 17 0 1 16 0 1 0 0 1 9 0 1 16 0 1 8 0 1 10 0 1 1 0 1 9 0 1","10 0 4 0 1 16 0 1 2 0 1 0 0 1 10 0 1 4 0 1 9 0 1 8 0 1 9 0 1 4 0 1","10 0 9 0 1 4 0 1 15 0 1 0 0 1 8 0 1 2 0 1 0 0 1 9 0 1 3 0 1 9 0 1","10 0 1 0 1 15 0 1 17 0 1 0 0 1 9 0 1 15 0 1 0 0 1 2 0 1 2 0 1 1 0 1","10 0 9 0 1 17 0 1 16 0 1 0 0 1 2 0 1 17 0 1 0 0 1 9 0 1 9 0 1 9 0 1","10 1 0 0 1 16 0 1 0 0 1 0 0 1 9 0 1 16 0 1 0 0 1 0 0 1 0 0 1 3 0 1 6 0 9","10 0 0 0 1 1 0 1 0 0 1 0 0 1 4 0 1 0 0 1 0 0 1 0 0 1 0 0 1 9 0 1","10 0 0 0 1 9 0 1 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1","1 10 5 0 5 6 8 17 3 0 9 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1","9 2 4 0 1 5 0 5 4 0 1 4 0 1 5 0 5 4 0 1 4 0 1 4 0 1 5 0 5 1 0 1 1 0 1","11 0 4 0 1 15 0 1 4 0 1 2 0 1 4 0 1 4 0 1 4 0 1 4 0 1 15 0 1 3 0 1 1 0 1","11 0 10 0 1 17 0 1 4 0 1 2 0 1 15 0 1 1 0 1 2 0 1 4 0 1 17 0 1 3 0 1 1 0 1","11 0 3 0 1 16 0 1 9 0 1 2 0 1 17 0 1 1 0 1 9 0 1 4 0 1 16 0 1 3 0 1 1 0 1","11 0 3 0 1 1 0 1 2 0 1 9 0 1 16 0 1 1 0 1 2 0 1 1 0 1 1 0 1 1 0 1 9 0 1","11 0 1 0 1 15 0 1 9 0 1 4 0 1 1 0 1 9 0 1 9 0 1 1 0 1 15 0 1 9 0 1 1 0 1","11 0 1 0 1 17 0 1 4 0 1 9 0 1 15 0 1 10 0 1 3 0 1 9 0 1 17 0 1 3 0 1 9 0 1","11 0 10 0 1 16 0 1 1 0 1 4 0 1 17 0 1 8 0 1 9 0 1 10 0 1 16 0 1 9 0 1 3 0 1","11 0 2 0 1 1 0 1 1 0 1 4 0 1 16 0 1 9 0 1 4 0 1 8 0 1 1 0 1 1 0 1 9 0 1","11 0 2 0 1 15 0 1 9 0 1 4 0 1 4 0 1 4 0 1 2 0 1 9 0 1 15 0 1 9 0 1 3 0 1","11 1 7 6 6 17 0 1 10 0 1 9 0 1 15 0 1 2 0 1 9 0 1 3 0 1 17 0 1 1 0 1 9 0 1 6 6 6","11 0 3 0 1 16 0 1 8 0 1 10 0 1 17 0 1 9 0 1 4 0 1 1 0 1 16 0 1 9 0 1 2 0 1","11 0 3 0 1 3 0 1 9 0 1 8 0 1 16 0 1 10 0 1 9 0 1 1 0 1 1 0 1 0 0 1 9 0 1","11 0 15 0 1 15 0 1 1 0 1 9 0 1 2 0 1 8 0 1 2 0 1 9 0 1 15 0 1 0 0 1 2 0 1","11 0 17 0 1 17 0 1 9 0 1 3 0 1 15 0 1 9 0 1 9 0 1 3 0 1 17 0 1 0 0 1 9 0 1","11 0 16 0 1 16 0 1 1 0 1 1 0 1 17 0 1 4 0 1 3 0 1 1 0 1 16 0 1 0 0 1 2 0 1","11 0 3 0 1 2 0 1 9 0 1 9 0 1 16 0 1 9 0 1 9 0 1 9 0 1 4 0 1 0 0 1 9 0 1","11 0 15 0 1 15 0 1 3 0 1 4 0 1 4 0 1 10 0 1 3 0 1 0 0 1 2 0 1 0 0 1 3 0 1","11 0 17 0 1 17 0 1 1 0 1 9 0 1 15 0 1 8 0 1 9 0 1 0 0 1 15 0 1 0 0 1 9 0 1","11 0 16 0 1 16 0 1 9 0 1 1 0 1 17 0 1 9 0 1 3 0 1 0 0 1 17 0 1 0 0 1 1 0 1","11 1 0 0 1 1 0 1 3 0 1 9 0 1 16 0 1 1 0 1 9 0 1 0 0 1 16 0 1 0 0 1 9 0 1 6 0 9","11 0 0 0 1 1 0 1 1 0 1 1 0 1 0 0 1 1 0 1 0 0 1 0 0 1 0 0 1 0 0 1 1 0 1","11 0 0 0 1 9 0 1 9 0 1 9 0 1 0 0 1 9 0 1 0 0 1 0 0 1 0 0 1 0 0 1 9 0 1","1 10 5 8 4 3 0 9 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1","10 3 1 0 1 10 0 1 4 0 1 3 0 1 5 0 5 3 0 1 1 0 1 4 0 1 5 0 5 1 0 1 6 8 9 1 0 1 4 8 2","11 2 4 0 1 7 6 6 9 0 1 1 0 1 15 0 1 3 0 1 1 0 1 9 0 1 10 0 1 10 0 1 1 0 1 6 6 6 6 8 1","11 1 4 0 1 5 0 5 2 0 1 1 0 1 17 0 1 10 0 1 10 0 1 2 0 1 7 6 3 2 0 1 5 0 2 6 6 3","11 1 4 0 1 15 0 1 9 0 1 10 0 1 16 0 1 4 0 1 2 0 1 9 0 1 4 0 1 7 6 6 3 0 1 6 6 6","11 1 4 0 1 17 0 1 4 0 1 4 0 1 1 0 1 4 0 1 7 6 3 2 0 1 15 0 1 4 0 1 15 0 1 6 6 3","11 1 11 0 1 16 0 1 4 0 1 2 0 1 15 0 1 7 7 6 4 0 1 9 0 1 17 0 1 4 0 1 17 0 1 6 7 6","11 1 9 0 1 1 0 1 2 0 1 7 7 6 17 0 1 4 0 1 4 0 1 4 0 1 16 0 1 4 0 1 16 0 1 6 7 6","11 0 1 0 1 15 0 1 9 0 1 4 0 1 16 0 1 4 0 1 2 0 1 4 0 1 1 0 1 2 0 1 3 0 1","11 0 11 0 1 17 0 1 10 0 1 2 0 1 1 0 1 4 0 1 2 0 1 2 0 1 15 0 1 9 0 1 15 0 1","11 0 9 0 1 16 0 1 8 0 1 2 0 1 15 0 1 4 0 1 9 0 1 9 0 1 17 0 1 4 0 1 17 0 1","11 0 3 0 1 1 0 1 9 0 1 2 0 1 17 0 1 1 0 1 2 0 1 10 0 1 16 0 1 4 0 1 16 0 1","11 0 1 0 1 15 0 1 2 0 1 2 0 1 16 0 1 9 0 1 9 0 1 8 0 1 4 0 1 2 0 1 3 0 1","11 0 11 0 1 17 0 1 9 0 1 9 0 1 10 0 1 1 0 1 4 0 1 9 0 1 15 0 1 9 0 1 1 0 1","11 0 9 0 1 16 0 1 10 0 1 4 0 1 1 0 1 9 0 1 1 0 1 2 0 1 17 0 1 10 0 1 1 0 1","11 0 3 0 1 3 0 1 8 0 1 9 0 1 15 0 1 3 0 1 9 0 1 9 0 1 16 0 1 8 0 1 1 0 1","11 0 1 0 1 15 0 1 9 0 1 1 0 1 17 0 1 9 0 1 1 0 1 10 0 1 2 0 1 9 0 1 1 0 1","11 0 11 0 1 17 0 1 2 0 1 9 0 1 16 0 1 1 0 1 9 0 1 8 0 1 15 0 1 2 0 1 9 0 1","11 0 9 0 1 16 0 1 9 0 1 0 0 1 4 0 1 9 0 1 4 0 1 9 0 1 17 0 1 9 0 1 3 0 1","11 0 4 0 1 2 0 1 10 0 1 0 0 1 2 0 1 3 0 1 9 0 1 3 0 1 16 0 1 10 0 1 9 0 1","11 0 4 0 1 15 0 1 8 0 1 0 0 1 15 0 1 9 0 1 1 0 1 9 0 1 4 0 1 8 0 1 2 0 1","11 1 9 0 1 17 0 1 9 0 1 0 0 1 17 0 1 1 0 1 9 0 1 3 0 1 15 0 1 9 0 1 9 0 1 6 0 9","11 0 2 0 1 16 0 1 4 0 1 0 0 1 16 0 1 9 0 1 0 0 1 9 0 1 17 0 1 2 0 1 0 0 1","11 0 9 0 1 0 0 1 9 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 16 0 1 9 0 1 0 0 1","1 10 5 0 5 6 6 3 3 0 11 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1","9 4 4 0 1 5 8 5 1 0 1 1 0 1 2 0 1 4 0 1 1 0 1 1 0 1 4 0 1 1 0 1 1 0 1 1 0 1 4 8 4","12 1 4 0 1 1 0 1 3 0 1 5 8 3 2 0 1 5 0 5 5 0 5 5 0 5 4 0 1 1 0 1 4 0 1 4 0 1 6 8 7","12 0 4 0 1 1 0 1 3 0 1 3 0 1 2 0 1 4 0 1 15 0 1 15 0 1 10 0 1 5 0 2 1 0 1 4 0 1","12 0 4 0 1 1 0 1 1 0 1 3 0 1 2 0 1 15 0 1 17 0 1 17 0 1 3 0 1 3 0 1 10 0 1 4 0 1","12 0 1 0 1 11 0 1 1 0 1 1 0 1 2 0 1 17 0 1 16 0 1 16 0 1 3 0 1 15 0 1 1 0 1 4 0 1","12 0 10 0 1 9 0 1 1 0 1 11 0 1 9 0 1 16 0 1 1 0 1 1 0 1 3 0 1 17 0 1 10 0 1 4 0 1","12 0 1 0 1 3 0 1 1 0 1 9 0 1 10 0 1 1 0 1 15 0 1 15 0 1 1 0 1 16 0 1 3 0 1 9 0 1","12 1 10 0 1 11 0 1 9 0 1 3 0 1 8 0 1 15 0 1 17 0 1 17 0 1 1 0 1 3 0 1 3 0 1 10 0 1 6 0 14","12 0 3 0 1 9 0 1 4 0 1 2 0 1 9 0 1 17 0 1 16 0 1 16 0 1 10 0 1 15 0 1 3 0 1 8 0 1","12 0 1 0 1 3 0 1 9 0 1 11 0 1 4 0 1 16 0 1 1 0 1 1 0 1 3 0 1 17 0 1 1 0 1 9 0 1","12 0 10 0 1 2 0 1 4 0 1 9 0 1 9 0 1 4 0 1 15 0 1 15 0 1 2 0 1 16 0 1 10 0 1 1 0 1","12 1 3 0 1 11 0 1 12 0 1 3 0 1 10 0 1 15 0 1 17 0 1 17 0 1 2 0 1 1 0 1 4 0 1 9 0 1 6 8 11","12 0 1 0 1 9 0 1 8 0 1 11 0 1 8 0 1 17 0 1 16 0 1 16 0 1 10 0 1 1 0 1 2 0 1 1 0 1","12 0 10 0 1 3 0 1 9 0 1 9 0 1 9 0 1 16 0 1 1 0 1 3 0 1 4 0 1 1 0 1 2 0 1 1 0 1","12 2 3 0 1 11 0 1 4 0 1 1 0 1 4 0 1 2 0 1 15 0 1 15 0 1 7 6 15 9 0 1 7 7 14 1 0 1 6 6 15 6 7 14","12 0 3 0 1 9 0 1 4 0 1 9 0 1 4 0 1 15 0 1 17 0 1 17 0 1 4 0 1 1 0 1 4 0 1 9 0 1","12 0 2 0 1 2 0 1 4 0 1 1 0 1 4 0 1 17 0 1 16 0 1 16 0 1 4 0 1 9 0 1 4 0 1 3 0 1","12 0 2 0 1 11 0 1 9 0 1 9 0 1 9 0 1 16 0 1 4 0 1 2 0 1 1 0 1 3 0 1 4 0 1 2 0 1","12 0 2 0 1 9 0 1 4 0 1 1 0 1 10 0 1 4 0 1 2 0 1 15 0 1 1 0 1 9 0 1 4 0 1 9 0 1","12 0 2 0 1 1 0 1 9 0 1 1 0 1 8 0 1 15 0 1 15 0 1 17 0 1 1 0 1 10 0 1 1 0 1 3 0 1","12 1 7 3 8 1 0 1 10 0 1 9 0 1 9 0 1 17 0 1 17 0 1 16 0 1 9 0 1 8 0 1 9 0 1 9 0 1 6 3 8","12 0 2 0 1 9 0 1 8 0 1 10 0 1 1 0 1 16 0 1 16 0 1 0 0 1 1 0 1 9 0 1 0 0 1 1 0 1","12 0 9 0 1 3 0 1 9 0 1 8 0 1 9 0 1 0 0 1 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1 9 0 1","1 10 3 0 1 3 0 9 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1","10 4 5 0 5 10 0 1 1 0 1 3 0 1 4 0 1 1 0 1 1 0 1 1 0 1 5 0 5 5 8 3 1 0 1 1 0 1 1 0 1 4 8 1","13 2 1 0 1 7 6 3 5 0 5 4 0 1 4 0 1 3 0 1 5 8 1 5 0 5 15 0 1 3 0 1 2 0 1 4 0 1 4 0 1 6 6 3 6 8 10","13 0 1 0 1 4 0 1 4 0 1 4 0 1 4 0 1 3 0 1 4 0 1 15 0 1 17 0 1 3 0 1 9 0 1 4 0 1 9 0 1","13 0 1 0 1 4 0 1 15 0 1 4 0 1 10 0 1 10 0 1 4 0 1 17 0 1 16 0 1 3 0 1 2 0 1 1 0 1 4 0 1","13 0 10 0 1 4 0 1 17 0 1 1 0 1 3 0 1 1 0 1 4 0 1 16 0 1 1 0 1 3 0 1 9 0 1 1 0 1 9 0 1","13 0 3 0 1 4 0 1 16 0 1 1 0 1 3 0 1 10 0 1 1 0 1 1 0 1 15 0 1 1 0 1 2 0 1 1 0 1 2 0 1","13 0 10 0 1 1 0 1 1 0 1 1 0 1 1 0 1 3 0 1 1 0 1 15 0 1 17 0 1 11 0 1 9 0 1 1 0 1 9 0 1","13 0 4 0 1 9 0 1 15 0 1 1 0 1 1 0 1 10 0 1 1 0 1 17 0 1 16 0 1 9 0 1 4 0 1 9 0 1 3 0 1","13 0 2 0 1 3 0 1 17 0 1 1 0 1 10 0 1 2 0 1 1 0 1 16 0 1 1 0 1 1 0 1 9 0 1 10 0 1 9 0 1","13 0 2 0 1 1 0 1 16 0 1 9 0 1 3 0 1 10 0 1 11 0 1 1 0 1 15 0 1 11 0 1 4 0 1 8 0 1 2 0 1","13 0 2 0 1 9 0 1 4 0 1 10 0 1 1 0 1 2 0 1 9 0 1 15 0 1 17 0 1 9 0 1 9 0 1 9 0 1 9 0 1","13 2 7 3 4 10 0 1 15 0 1 8 0 1 10 0 1 10 0 1 3 0 1 17 0 1 16 0 1 4 0 1 4 0 1 4 0 1 4 0 1 6 3 4 6 8 4","13 0 3 0 1 8 0 1 17 0 1 9 0 1 2 0 1 3 0 1 9 0 1 16 0 1 10 0 1 1 0 1 9 0 1 2 0 1 9 0 1","13 0 15 0 1 9 0 1 16 0 1 3 0 1 2 0 1 10 0 1 2 0 1 3 0 1 1 0 1 11 0 1 4 0 1 9 0 1 4 0 1","13 0 17 0 1 4 0 1 2 0 1 3 0 1 2 0 1 4 0 1 9 0 1 15 0 1 15 0 1 9 0 1 9 0 1 4 0 1 9 0 1","13 1 16 0 1 9 0 1 15 0 1 3 0 1 7 7 18 4 0 1 10 0 1 17 0 1 17 0 1 3 0 1 10 0 1 2 0 1 4 0 1 6 7 18","13 0 3 0 1 1 0 1 17 0 1 3 0 1 1 0 1 4 0 1 8 0 1 16 0 1 16 0 1 9 0 1 8 0 1 9 0 1 9 0 1","13 1 15 0 1 9 0 1 16 0 1 3 0 1 10 0 1 4 0 1 9 0 1 2 0 1 4 0 1 10 0 1 9 0 1 4 0 1 1 0 1 6 0 6","13 1 17 0 1 10 0 1 4 0 1 3 0 1 3 0 1 7 3 12 4 0 1 15 0 1 2 0 1 8 0 1 3 0 1 2 0 1 9 0 1 6 3 12","13 0 16 0 1 8 0 1 15 0 1 12 0 1 10 0 1 4 0 1 9 0 1 17 0 1 15 0 1 9 0 1 2 0 1 9 0 1 3 0 1","13 0 0 0 1 9 0 1 17 0 1 8 0 1 2 0 1 2 0 1 0 0 1 16 0 1 17 0 1 0 0 1 9 0 1 0 0 1 9 0 1","13 0 0 0 1 0 0 1 16 0 1 9 0 1 10 0 1 9 0 1 0 0 1 0 0 1 16 0 1 0 0 1 3 0 1 0 0 1 1 0 1","13 1 0 0 1 0 0 1 0 0 1 0 0 1 7 6 9 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 9 0 1 0 0 1 9 0 1 6 6 9","1 10 5 0 5 3 0 9 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1","10 5 4 0 1 3 0 1 1 0 1 1 0 1 4 0 1 5 8 4 4 0 1 4 0 1 5 0 5 1 0 1 6 6 3 1 0 1 1 0 1 1 0 1 4 8 4","13 0 4 0 1 3 0 1 5 0 5 5 0 5 4 0 1 1 0 1 4 0 1 4 0 1 4 0 1 1 0 1 1 0 1 4 0 1 4 0 1","13 0 4 0 1 3 0 1 15 0 1 15 0 1 1 0 1 1 0 1 1 0 1 4 0 1 15 0 1 10 0 1 5 0 2 4 0 1 2 0 1","13 0 4 0 1 9 0 1 17 0 1 17 0 1 10 0 1 1 0 1 1 0 1 4 0 1 17 0 1 3 0 1 3 0 1 4 0 1 2 0 1","13 1 1 0 1 3 0 1 16 0 1 16 0 1 3 0 1 9 0 1 1 0 1 1 0 1 16 0 1 2 0 1 15 0 1 4 0 1 2 0 1 6 8 10","13 0 10 0 1 9 0 1 1 0 1 1 0 1 3 0 1 1 0 1 9 0 1 1 0 1 1 0 1 2 0 1 17 0 1 9 0 1 2 0 1","13 0 1 0 1 4 0 1 15 0 1 15 0 1 3 0 1 11 0 1 10 0 1 9 0 1 15 0 1 10 0 1 16 0 1 2 0 1 9 0 1","13 0 10 0 1 1 0 1 17 0 1 17 0 1 3 0 1 9 0 1 8 0 1 10 0 1 17 0 1 4 0 1 3 0 1 2 0 1 4 0 1","13 1 3 0 1 9 0 1 16 0 1 16 0 1 10 0 1 3 0 1 9 0 1 8 0 1 16 0 1 7 6 6 15 0 1 9 0 1 9 0 1 6 6 6","13 0 1 0 1 1 0 1 1 0 1 1 0 1 3 0 1 11 0 1 4 0 1 9 0 1 4 0 1 4 0 1 17 0 1 10 0 1 4 0 1","13 0 10 0 1 1 0 1 15 0 1 15 0 1 2 0 1 9 0 1 4 0 1 4 0 1 15 0 1 4 0 1 16 0 1 8 0 1 4 0 1","13 0 1 0 1 10 0 1 17 0 1 17 0 1 10 0 1 3 0 1 1 0 1 2 0 1 17 0 1 4 0 1 1 0 1 9 0 1 9 0 1","13 0 10 0 1 3 0 1 16 0 1 16 0 1 4 0 1 11 0 1 1 0 1 9 0 1 16 0 1 2 0 1 9 0 1 3 0 1 10 0 1","13 0 3 0 1 2 0 1 1 0 1 3 0 1 4 0 1 9 0 1 9 0 1 10 0 1 2 0 1 2 0 1 1 0 1 9 0 1 8 0 1","13 1 10 0 1 10 0 1 15 0 1 15 0 1 7 7 10 2 0 1 3 0 1 8 0 1 15 0 1 2 0 1 9 0 1 0 0 1 9 0 1 6 7 10","13 0 3 0 1 2 0 1 17 0 1 17 0 1 4 0 1 11 0 1 3 0 1 9 0 1 17 0 1 2 0 1 3 0 1 0 0 1 4 0 1","13 0 3 0 1 10 0 1 16 0 1 16 0 1 2 0 1 9 0 1 3 0 1 2 0 1 16 0 1 2 0 1 9 0 1 0 0 1 9 0 1","13 1 2 0 1 4 0 1 4 0 1 2 0 1 9 0 1 4 0 1 3 0 1 2 0 1 10 0 1 9 0 1 1 0 1 0 0 1 3 0 1 6 0 6","13 0 2 0 1 4 0 1 2 0 1 15 0 1 0 0 1 9 0 1 9 0 1 9 0 1 4 0 1 10 0 1 1 0 1 0 0 1 1 0 1","13 0 2 0 1 4 0 1 15 0 1 17 0 1 0 0 1 0 0 1 4 0 1 0 0 1 15 0 1 8 0 1 9 0 1 0 0 1 9 0 1","13 0 2 0 1 4 0 1 17 0 1 16 0 1 0 0 1 0 0 1 2 0 1 0 0 1 17 0 1 9 0 1 0 0 1 0 0 1 10 0 1","13 1 7 3 10 2 0 1 16 0 1 0 0 1 0 0 1 0 0 1 9 0 1 0 0 1 16 0 1 1 0 1 0 0 1 0 0 1 8 0 1 6 3 10","13 1 0 0 1 7 3 6 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1 9 0 1 6 3 6","1 10 5 0 5 3 0 9 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1","10 6 15 0 1 1 0 1 4 0 1 4 0 1 5 8 4 5 0 2 1 0 1 4 0 1 10 0 1 5 0 5 6 6 6 6 7 4 1 0 1 1 0 1 1 0 1 4 8 4","13 0 4 0 1 1 0 1 9 0 1 2 0 1 4 0 1 3 0 1 5 0 4 4 0 1 5 0 5 15 0 1 4 0 1 4 0 1 10 0 1","13 0 1 0 1 1 0 1 2 0 1 9 0 1 4 0 1 3 0 1 4 0 1 4 0 1 1 0 1 17 0 1 2 0 1 9 0 1 7 6 3","13 0 10 0 1 1 0 1 9 0 1 4 0 1 4 0 1 1 0 1 15 0 1 9 0 1 15 0 1 16 0 1 2 0 1 5 8 1 3 0 1","13 0 2 0 1 10 0 1 2 0 1 4 0 1 4 0 1 10 0 1 17 0 1 4 0 1 17 0 1 1 0 1 9 0 1 4 0 1 3 0 1","13 1 10 0 1 2 0 1 9 0 1 9 0 1 1 0 1 3 0 1 16 0 1 9 0 1 16 0 1 15 0 1 2 0 1 11 0 1 3 0 1 6 6 3","13 0 3 0 1 10 0 1 4 0 1 2 0 1 11 0 1 1 0 1 4 0 1 1 0 1 4 0 1 17 0 1 9 0 1 3 0 1 3 0 1","13 1 7 7 6 3 0 1 9 0 1 2 0 1 9 0 1 10 0 1 4 0 1 1 0 1 15 0 1 16 0 1 4 0 1 5 8 2 1 0 1 6 7 6","13 0 3 0 1 10 0 1 4 0 1 9 0 1 1 0 1 2 0 1 15 0 1 1 0 1 17 0 1 10 0 1 9 0 1 11 0 1 9 0 1","13 0 3 0 1 1 0 1 9 0 1 10 0 1 11 0 1 10 0 1 17 0 1 9 0 1 16 0 1 1 0 1 2 0 1 2 0 1 1 0 1","13 0 3 0 1 10 0 1 10 0 1 8 0 1 9 0 1 2 0 1 16 0 1 3 0 1 1 0 1 15 0 1 9 0 1 11 0 1 9 0 1","13 0 15 0 1 3 0 1 8 0 1 9 0 1 3 0 1 10 0 1 3 0 1 1 0 1 15 0 1 16 0 1 10 0 1 1 0 1 1 0 1","13 0 17 0 1 10 0 1 9 0 1 3 0 1 1 0 1 3 0 1 3 0 1 9 0 1 17 0 1 4 0 1 8 0 1 5 8 2 9 0 1","13 1 16 0 1 2 0 1 1 0 1 3 0 1 11 0 1 10 0 1 3 0 1 4 0 1 16 0 1 15 0 1 9 0 1 2 0 1 4 0 1 6 8 10","13 0 4 0 1 10 0 1 9 0 1 2 0 1 9 0 1 4 0 1 3 0 1 4 0 1 4 0 1 17 0 1 4 0 1 2 0 1 9 0 1","13 0 1 0 1 2 0 1 4 0 1 9 0 1 3 0 1 4 0 1 3 0 1 9 0 1 2 0 1 16 0 1 4 0 1 11 0 1 1 0 1","13 0 1 0 1 10 0 1 9 0 1 1 0 1 1 0 1 4 0 1 15 0 1 1 0 1 15 0 1 10 0 1 4 0 1 3 0 1 9 0 1","13 1 15 0 1 4 0 1 10 0 1 1 0 1 11 0 1 4 0 1 17 0 1 9 0 1 17 0 1 1 0 1 9 0 1 3 0 1 10 0 1 6 0 6","13 1 17 0 1 4 0 1 8 0 1 1 0 1 9 0 1 7 3 10 16 0 1 10 0 1 16 0 1 15 0 1 10 0 1 3 0 1 8 0 1 6 3 10","13 0 16 0 1 2 0 1 9 0 1 1 0 1 3 0 1 4 0 1 1 0 1 8 0 1 2 0 1 17 0 1 8 0 1 1 0 1 9 0 1","13 0 10 0 1 2 0 1 1 0 1 5 8 2 9 0 1 16 0 1 15 0 1 9 0 1 15 0 1 16 0 1 9 0 1 1 0 1 3 0 1","13 1 4 0 1 7 3 14 9 0 1 4 0 1 3 0 1 17 0 1 17 0 1 3 0 1 17 0 1 4 0 1 1 0 1 1 0 1 9 0 1 6 3 14","13 0 17 0 1 0 0 1 0 0 1 2 0 1 9 0 1 1 0 1 16 0 1 9 0 1 16 0 1 9 0 1 9 0 1 1 0 1 0 0 1","1 10 3 0 1 3 0 9 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1","10 5 5 8 5 4 0 1 4 0 1 1 0 1 5 0 5 5 8 1 1 0 1 4 0 1 5 0 5 5 0 5 6 7 6 1 0 1 1 0 1 1 0 1 4 8 4","13 0 1 0 1 4 0 1 4 0 1 4 0 1 4 0 1 3 0 1 3 0 1 2 0 1 15 0 1 15 0 1 4 0 1 4 0 1 1 0 1","13 0 1 0 1 4 0 1 1 0 1 1 0 1 15 0 1 3 0 1 5 8 3 2 0 1 17 0 1 17 0 1 4 0 1 4 0 1 1 0 1","13 0 1 0 1 1 0 1 1 0 1 1 0 1 17 0 1 1 0 1 3 0 1 2 0 1 16 0 1 16 0 1 4 0 1 4 0 1 1 0 1","13 1 11 0 1 9 0 1 1 0 1 1 0 1 16 0 1 1 0 1 3 0 1 2 0 1 1 0 1 1 0 1 4 0 1 4 0 1 1 0 1 6 8 10","13 1 9 0 1 1 0 1 9 0 1 10 0 1 1 0 1 1 0 1 1 0 1 9 0 1 15 0 1 15 0 1 4 0 1 1 0 1 1 0 1 6 6 6","13 1 3 0 1 1 0 1 4 0 1 2 0 1 15 0 1 9 0 1 11 0 1 10 0 1 17 0 1 17 0 1 9 0 1 1 0 1 9 0 1 6 6 3","13 0 11 0 1 9 0 1 4 0 1 2 0 1 17 0 1 3 0 1 9 0 1 8 0 1 16 0 1 16 0 1 10 0 1 1 0 1 4 0 1","13 0 9 0 1 10 0 1 9 0 1 2 0 1 16 0 1 10 0 1 3 0 1 9 0 1 10 0 1 1 0 1 8 0 1 1 0 1 9 0 1","13 1 3 0 1 1 0 1 10 0 1 7 7 4 4 0 1 3 0 1 2 0 1 4 0 1 1 0 1 15 0 1 9 0 1 9 0 1 10 0 1 6 7 4","13 0 2 0 1 10 0 1 2 0 1 3 0 1 15 0 1 2 0 1 11 0 1 4 0 1 15 0 1 17 0 1 3 0 1 10 0 1 8 0 1","13 0 11 0 1 3 0 1 9 0 1 5 0 2 17 0 1 10 0 1 9 0 1 9 0 1 17 0 1 16 0 1 3 0 1 8 0 1 9 0 1","13 0 9 0 1 9 0 1 10 0 1 3 0 1 16 0 1 2 0 1 3 0 1 4 0 1 16 0 1 10 0 1 3 0 1 9 0 1 3 0 1","13 0 3 0 1 10 0 1 3 0 1 15 0 1 2 0 1 11 0 1 11 0 1 9 0 1 1 0 1 3 0 1 3 0 1 3 0 1 3 0 1","13 0 11 0 1 3 0 1 3 0 1 17 0 1 15 0 1 9 0 1 9 0 1 1 0 1 15 0 1 15 0 1 5 8 3 2 0 1 9 0 1","13 1 9 0 1 3 0 1 3 0 1 16 0 1 17 0 1 10 0 1 1 0 1 9 0 1 17 0 1 17 0 1 4 0 1 9 0 1 3 0 1 6 6 9","13 0 2 0 1 2 0 1 3 0 1 10 0 1 16 0 1 4 0 1 1 0 1 4 0 1 16 0 1 16 0 1 4 0 1 3 0 1 9 0 1","13 1 11 0 1 2 0 1 2 0 1 3 0 1 10 0 1 4 0 1 1 0 1 9 0 1 4 0 1 2 0 1 11 0 1 1 0 1 3 0 1 6 0 6","13 1 9 0 1 2 0 1 7 3 4 15 0 1 4 0 1 4 0 1 9 0 1 10 0 1 2 0 1 15 0 1 4 0 1 9 0 1 3 0 1 6 3 4","13 0 0 0 1 2 0 1 4 0 1 17 0 1 15 0 1 4 0 1 10 0 1 8 0 1 15 0 1 17 0 1 11 0 1 3 0 1 9 0 1","13 1 0 0 1 7 3 6 4 0 1 16 0 1 17 0 1 2 0 1 8 0 1 9 0 1 17 0 1 16 0 1 3 0 1 9 0 1 10 0 1 6 3 6","13 1 0 0 1 0 0 1 4 0 1 0 0 1 16 0 1 7 3 6 9 0 1 1 0 1 16 0 1 0 0 1 3 0 1 1 0 1 8 0 1 6 3 6","13 0 0 0 1 0 0 1 10 0 1 0 0 1 4 0 1 0 0 1 0 0 1 9 0 1 10 0 1 0 0 1 2 0 1 9 0 1 9 0 1","1 10 5 0 5 3 0 9 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1","10 4 3 0 1 1 0 1 5 8 5 1 0 1 5 0 5 3 0 1 5 8 2 4 0 1 5 0 5 5 0 2 1 0 1 1 0 1 1 0 1 4 8 4","13 0 15 0 1 1 0 1 4 0 1 5 8 2 4 0 1 3 0 1 2 0 1 4 0 1 15 0 1 3 0 1 4 0 1 4 0 1 5 8 1","13 0 17 0 1 1 0 1 2 0 1 3 0 1 15 0 1 1 0 1 2 0 1 1 0 1 17 0 1 15 0 1 4 0 1 4 0 1 4 0 1","13 0 16 0 1 1 0 1 11 0 1 3 0 1 17 0 1 10 0 1 2 0 1 1 0 1 16 0 1 17 0 1 4 0 1 4 0 1 4 0 1","13 1 10 0 1 10 0 1 9 0 1 3 0 1 16 0 1 3 0 1 11 0 1 1 0 1 10 0 1 16 0 1 4 0 1 4 0 1 4 0 1 6 8 10","13 2 1 0 1 2 0 1 4 0 1 1 0 1 1 0 1 1 0 1 9 0 1 1 0 1 1 0 1 3 0 1 4 0 1 4 0 1 1 0 1 6 6 6 6 7 6","13 2 15 0 1 10 0 1 11 0 1 1 0 1 15 0 1 10 0 1 4 0 1 9 0 1 15 0 1 15 0 1 1 0 1 2 0 1 1 0 1 6 6 6 6 7 2","13 1 17 0 1 3 0 1 9 0 1 1 0 1 17 0 1 2 0 1 11 0 1 10 0 1 17 0 1 17 0 1 12 0 1 9 0 1 1 0 1 6 0 6","13 0 16 0 1 10 0 1 4 0 1 11 0 1 16 0 1 10 0 1 9 0 1 8 0 1 16 0 1 16 0 1 8 0 1 2 0 1 1 0 1","13 0 10 0 1 1 0 1 11 0 1 9 0 1 4 0 1 2 0 1 4 0 1 9 0 1 1 0 1 10 0 1 9 0 1 9 0 1 11 0 1","13 0 1 0 1 10 0 1 9 0 1 3 0 1 15 0 1 10 0 1 9 0 1 1 0 1 15 0 1 3 0 1 3 0 1 10 0 1 9 0 1","13 0 15 0 1 3 0 1 3 0 1 2 0 1 17 0 1 3 0 1 4 0 1 9 0 1 17 0 1 1 0 1 3 0 1 8 0 1 4 0 1","13 2 17 0 1 10 0 1 2 0 1 11 0 1 16 0 1 10 0 1 9 0 1 10 0 1 16 0 1 1 0 1 2 0 1 9 0 1 9 0 1 6 6 9 6 7 4","13 0 16 0 1 2 0 1 11 0 1 9 0 1 10 0 1 4 0 1 10 0 1 8 0 1 1 0 1 1 0 1 9 0 1 3 0 1 3 0 1","13 0 3 0 1 10 0 1 9 0 1 2 0 1 2 0 1 4 0 1 8 0 1 9 0 1 15 0 1 1 0 1 4 0 1 9 0 1 2 0 1","13 0 15 0 1 2 0 1 3 0 1 9 0 1 15 0 1 4 0 1 9 0 1 4 0 1 16 0 1 9 0 1 9 0 1 3 0 1 9 0 1","13 0 17 0 1 10 0 1 11 0 1 4 0 1 17 0 1 4 0 1 2 0 1 2 0 1 4 0 1 4 0 1 1 0 1 3 0 1 4 0 1","13 1 16 0 1 4 0 1 9 0 1 4 0 1 16 0 1 7 3 10 9 0 1 9 0 1 2 0 1 11 0 1 1 0 1 2 0 1 2 0 1 6 3 10","13 0 2 0 1 4 0 1 3 0 1 4 0 1 4 0 1 4 0 1 10 0 1 10 0 1 15 0 1 4 0 1 1 0 1 2 0 1 9 0 1","13 0 15 0 1 2 0 1 9 0 1 4 0 1 15 0 1 2 0 1 8 0 1 8 0 1 17 0 1 11 0 1 9 0 1 9 0 1 2 0 1","13 0 17 0 1 2 0 1 1 0 1 4 0 1 17 0 1 9 0 1 9 0 1 9 0 1 16 0 1 4 0 1 10 0 1 4 0 1 9 0 1","13 1 16 0 1 7 3 14 9 0 1 10 0 1 16 0 1 4 0 1 4 0 1 1 0 1 4 0 1 4 0 1 8 0 1 9 0 1 3 0 1 6 3 14","13 0 10 0 1 5 8 1 0 0 1 1 0 1 0 0 1 9 0 1 9 0 1 9 0 1 9 0 1 2 0 1 9 0 1 0 0 1 9 0 1","1 10 4 0 1 3 0 9 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1","10 5 4 0 1 5 0 4 5 0 5 4 0 1 4 0 1 5 0 5 5 8 2 4 0 1 4 0 1 4 0 1 6 7 10 1 0 1 1 0 1 1 0 1 4 8 1","13 0 2 0 1 4 0 1 15 0 1 2 0 1 2 0 1 15 0 1 3 0 1 4 0 1 3 0 1 4 0 1 3 0 1 3 0 1 4 0 1","13 0 10 0 1 15 0 1 17 0 1 2 0 1 2 0 1 17 0 1 1 0 1 2 0 1 1 0 1 1 0 1 3 0 1 3 0 1 4 0 1","13 0 4 0 1 17 0 1 16 0 1 10 0 1 2 0 1 16 0 1 1 0 1 2 0 1 1 0 1 1 0 1 3 0 1 3 0 1 10 0 1","13 1 10 0 1 16 0 1 1 0 1 3 0 1 2 0 1 1 0 1 1 0 1 2 0 1 1 0 1 9 0 1 1 0 1 1 0 1 3 0 1 6 8 10","13 2 2 0 1 4 0 1 15 0 1 10 0 1 9 0 1 15 0 1 9 0 1 2 0 1 10 0 1 10 0 1 9 0 1 1 0 1 10 0 1 6 6 6 6 7 2","13 1 10 0 1 15 0 1 17 0 1 2 0 1 4 0 1 17 0 1 4 0 1 9 0 1 3 0 1 8 0 1 3 0 1 9 0 1 1 0 1 6 6 6","13 0 3 0 1 17 0 1 16 0 1 10 0 1 9 0 1 16 0 1 9 0 1 10 0 1 16 0 1 9 0 1 9 0 1 4 0 1 10 0 1","13 0 10 0 1 16 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 8 0 1 17 0 1 4 0 1 4 0 1 9 0 1 1 0 1","13 0 2 0 1 4 0 1 15 0 1 1 0 1 10 0 1 15 0 1 11 0 1 9 0 1 10 0 1 2 0 1 1 0 1 1 0 1 1 0 1","13 0 10 0 1 15 0 1 17 0 1 10 0 1 4 0 1 17 0 1 9 0 1 4 0 1 2 0 1 9 0 1 1 0 1 9 0 1 9 0 1","13 0 3 0 1 17 0 1 16 0 1 1 0 1 9 0 1 16 0 1 3 0 1 4 0 1 16 0 1 10 0 1 1 0 1 3 0 1 4 0 1","13 2 1 0 1 16 0 1 4 0 1 7 3 8 4 0 1 10 0 1 3 0 1 9 0 1 17 0 1 8 0 1 1 0 1 9 0 1 1 0 1 6 6 9 6 3 8","13 0 10 0 1 3 0 1 4 0 1 5 8 1 1 0 1 1 0 1 2 0 1 10 0 1 3 0 1 9 0 1 9 0 1 1 0 1 10 0 1","13 0 1 0 1 3 0 1 2 0 1 2 0 1 9 0 1 15 0 1 11 0 1 8 0 1 2 0 1 4 0 1 10 0 1 10 0 1 4 0 1","13 0 10 0 1 3 0 1 15 0 1 2 0 1 4 0 1 17 0 1 9 0 1 9 0 1 16 0 1 1 0 1 8 0 1 3 0 1 10 0 1","13 0 3 0 1 3 0 1 17 0 1 11 0 1 1 0 1 16 0 1 1 0 1 1 0 1 17 0 1 1 0 1 9 0 1 2 0 1 2 0 1","13 2 10 0 1 3 0 1 16 0 1 0 0 1 9 0 1 4 0 1 9 0 1 9 0 1 4 0 1 9 0 1 4 0 1 10 0 1 10 0 1 6 8 14 6 0 24","13 1 7 3 16 15 0 1 4 0 1 0 0 1 0 0 1 2 0 1 3 0 1 1 0 1 4 0 1 1 0 1 4 0 1 2 0 1 4 0 1 6 3 16","13 0 0 0 1 17 0 1 15 0 1 0 0 1 0 0 1 15 0 1 3 0 1 1 0 1 4 0 1 9 0 1 9 0 1 10 0 1 2 0 1","13 1 0 0 1 16 0 1 17 0 1 0 0 1 0 0 1 17 0 1 9 0 1 1 0 1 2 0 1 10 0 1 4 0 1 0 0 1 10 0 1 6 7 6","13 0 0 0 1 10 0 1 16 0 1 0 0 1 0 0 1 16 0 1 2 0 1 9 0 1 2 0 1 8 0 1 4 0 1 0 0 1 2 0 1","13 0 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 9 0 1 0 0 1 11 0 1 9 0 1 9 0 1 0 0 1 10 0 1","1 10 5 0 5 3 0 9 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1","10 5 15 0 1 1 0 1 5 8 4 1 0 1 5 0 5 3 0 1 2 0 1 4 0 1 4 0 1 5 0 5 6 7 4 1 0 1 1 0 1 1 0 1 4 8 4","13 1 4 0 1 1 0 1 11 0 1 5 0 2 1 0 1 3 0 1 9 0 1 2 0 1 4 0 1 15 0 1 3 0 1 4 0 1 4 0 1 6 8 10","13 0 15 0 1 1 0 1 9 0 1 3 0 1 15 0 1 1 0 1 4 0 1 2 0 1 1 0 1 17 0 1 3 0 1 1 0 1 4 0 1","13 0 17 0 1 1 0 1 4 0 1 3 0 1 17 0 1 10 0 1 4 0 1 9 0 1 1 0 1 16 0 1 3 0 1 16 0 1 4 0 1","13 0 16 0 1 10 0 1 11 0 1 15 0 1 16 0 1 3 0 1 9 0 1 2 0 1 1 0 1 10 0 1 1 0 1 17 0 1 4 0 1","13 3 4 0 1 2 0 1 9 0 1 17 0 1 4 0 1 1 0 1 3 0 1 9 0 1 9 0 1 1 0 1 1 0 1 10 0 1 9 0 1 6 3 6 6 6 6 6 7 6","13 3 4 0 1 10 0 1 4 0 1 16 0 1 15 0 1 10 0 1 9 0 1 4 0 1 4 0 1 15 0 1 1 0 1 1 0 1 1 0 1 6 3 6 6 6 6 6 7 2","13 1 15 0 1 3 0 1 11 0 1 4 0 1 17 0 1 2 0 1 2 0 1 4 0 1 4 0 1 17 0 1 1 0 1 10 0 1 12 0 1 6 3 6","13 0 17 0 1 10 0 1 9 0 1 1 0 1 16 0 1 10 0 1 9 0 1 9 0 1 9 0 1 16 0 1 9 0 1 1 0 1 8 0 1","13 0 16 0 1 1 0 1 4 0 1 1 0 1 1 0 1 2 0 1 2 0 1 10 0 1 10 0 1 10 0 1 3 0 1 10 0 1 9 0 1","13 1 3 0 1 10 0 1 11 0 1 15 0 1 15 0 1 10 0 1 9 0 1 8 0 1 8 0 1 1 0 1 1 0 1 4 0 1 1 0 1 6 0 1","13 1 3 0 1 3 0 1 9 0 1 17 0 1 17 0 1 3 0 1 2 0 1 9 0 1 9 0 1 15 0 1 9 0 1 10 0 1 12 0 1 6 8 6","13 2 3 0 1 10 0 1 2 0 1 16 0 1 16 0 1 10 0 1 9 0 1 1 0 1 3 0 1 17 0 1 10 0 1 4 0 1 8 0 1 6 3 18 6 6 9","13 1 3 0 1 2 0 1 9 0 1 3 0 1 4 0 1 4 0 1 10 0 1 9 0 1 12 0 1 16 0 1 8 0 1 4 0 1 9 0 1 6 0 3","13 0 3 0 1 10 0 1 4 0 1 3 0 1 2 0 1 4 0 1 8 0 1 4 0 1 8 0 1 4 0 1 9 0 1 2 0 1 3 0 1","13 0 15 0 1 2 0 1 9 0 1 3 0 1 15 0 1 4 0 1 9 0 1 9 0 1 9 0 1 15 0 1 2 0 1 2 0 1 9 0 1","13 0 17 0 1 10 0 1 10 0 1 9 0 1 17 0 1 4 0 1 3 0 1 10 0 1 3 0 1 17 0 1 9 0 1 10 0 1 1 0 1","13 1 16 0 1 4 0 1 8 0 1 2 0 1 16 0 1 7 3 10 9 0 1 8 0 1 1 0 1 16 0 1 0 0 1 4 0 1 1 0 1 6 3 10","13 0 1 0 1 4 0 1 9 0 1 9 0 1 2 0 1 0 0 1 0 0 1 9 0 1 12 0 1 1 0 1 0 0 1 2 0 1 9 0 1","13 1 15 0 1 2 0 1 2 0 1 0 0 1 15 0 1 0 0 1 0 0 1 2 0 1 8 0 1 15 0 1 0 0 1 9 0 1 3 0 1 6 7 8","13 0 17 0 1 2 0 1 9 0 1 0 0 1 17 0 1 0 0 1 0 0 1 9 0 1 9 0 1 17 0 1 0 0 1 0 0 1 3 0 1","13 1 16 0 1 7 3 14 2 0 1 0 0 1 16 0 1 0 0 1 0 0 1 2 0 1 3 0 1 16 0 1 0 0 1 0 0 1 3 0 1 6 3 14","13 0 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1 0 0 1 0 0 1 9 0 1 9 0 1 10 0 1 0 0 1 0 0 1 9 0 1","1 10 5 0 5 6 7 11 6 8 14 3 0 9 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1","8 6 4 0 1 5 0 5 4 0 1 1 0 1 5 0 5 4 0 1 4 0 1 4 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 4 8 4","13 1 15 0 1 15 0 1 4 0 1 5 8 1 3 0 1 5 0 5 4 0 1 2 0 1 3 0 1 4 0 1 4 0 1 4 0 1 3 0 1 6 8 4","13 0 17 0 1 17 0 1 4 0 1 3 0 1 3 0 1 15 0 1 2 0 1 2 0 1 3 0 1 4 0 1 4 0 1 4 0 1 3 0 1","13 0 16 0 1 16 0 1 10 0 1 1 0 1 15 0 1 17 0 1 2 0 1 2 0 1 1 0 1 4 0 1 4 0 1 1 0 1 3 0 1","13 1 1 0 1 1 0 1 3 0 1 1 0 1 17 0 1 16 0 1 2 0 1 2 0 1 1 0 1 4 0 1 2 0 1 1 0 1 1 0 1 6 8 2","13 1 15 0 1 15 0 1 10 0 1 1 0 1 16 0 1 1 0 1 2 0 1 9 0 1 12 0 1 9 0 1 10 0 1 9 0 1 12 0 1 6 6 6","13 1 17 0 1 17 0 1 3 0 1 1 0 1 10 0 1 15 0 1 9 0 1 10 0 1 8 0 1 10 0 1 4 0 1 3 0 1 8 0 1 6 6 6","13 1 16 0 1 16 0 1 10 0 1 11 0 1 3 0 1 17 0 1 4 0 1 8 0 1 9 0 1 8 0 1 10 0 1 1 0 1 9 0 1 6 6 3","13 0 4 0 1 1 0 1 2 0 1 9 0 1 15 0 1 16 0 1 9 0 1 9 0 1 1 0 1 9 0 1 4 0 1 9 0 1 1 0 1","13 0 15 0 1 15 0 1 10 0 1 2 0 1 17 0 1 1 0 1 10 0 1 1 0 1 12 0 1 1 0 1 9 0 1 3 0 1 12 0 1","13 0 17 0 1 17 0 1 3 0 1 12 0 1 16 0 1 15 0 1 8 0 1 10 0 1 8 0 1 1 0 1 1 0 1 3 0 1 8 0 1","13 0 16 0 1 16 0 1 10 0 1 8 0 1 10 0 1 17 0 1 9 0 1 4 0 1 9 0 1 1 0 1 1 0 1 12 0 1 9 0 1","13 1 2 0 1 10 0 1 2 0 1 9 0 1 3 0 1 16 0 1 4 0 1 10 0 1 3 0 1 1 0 1 9 0 1 8 0 1 1 0 1 6 6 6","13 0 15 0 1 3 0 1 10 0 1 3 0 1 12 0 1 1 0 1 9 0 1 1 0 1 3 0 1 1 0 1 1 0 1 9 0 1 1 0 1","13 0 17 0 1 15 0 1 1 0 1 9 0 1 8 0 1 15 0 1 1 0 1 10 0 1 10 0 1 9 0 1 9 0 1 1 0 1 9 0 1","13 1 16 0 1 17 0 1 1 0 1 3 0 1 9 0 1 17 0 1 9 0 1 4 0 1 2 0 1 3 0 1 3 0 1 9 0 1 4 0 1 6 0 2","13 0 10 0 1 16 0 1 10 0 1 3 0 1 3 0 1 16 0 1 10 0 1 10 0 1 10 0 1 10 0 1 3 0 1 4 0 1 9 0 1","13 1 4 0 1 2 0 1 7 3 14 9 0 1 12 0 1 4 0 1 8 0 1 4 0 1 0 0 1 3 0 1 10 0 1 9 0 1 0 0 1 6 3 14","13 0 15 0 1 15 0 1 0 0 1 10 0 1 8 0 1 2 0 1 9 0 1 9 0 1 0 0 1 2 0 1 4 0 1 10 0 1 0 0 1","13 0 17 0 1 17 0 1 0 0 1 8 0 1 9 0 1 15 0 1 3 0 1 4 0 1 0 0 1 9 0 1 1 0 1 8 0 1 0 0 1","13 0 16 0 1 16 0 1 0 0 1 9 0 1 0 0 1 17 0 1 9 0 1 9 0 1 0 0 1 0 0 1 9 0 1 9 0 1 0 0 1","13 0 1 0 1 10 0 1 0 0 1 4 0 1 0 0 1 16 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 4 0 1 0 0 1","13 0 9 0 1 0 0 1 0 0 1 10 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 9 0 1 0 0 1","1 10 2 0 1 6 6 27 3 0 7 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1","9 5 5 8 6 5 0 5 5 0 5 4 0 1 5 0 5 5 0 2 5 8 3 4 0 1 4 0 1 1 0 1 1 0 1 1 0 1 1 0 1 4 8 4","13 0 9 0 1 15 0 1 15 0 1 3 0 1 4 0 1 3 0 1 2 0 1 4 0 1 1 0 1 4 0 1 4 0 1 4 0 1 4 0 1","13 0 2 0 1 17 0 1 17 0 1 1 0 1 15 0 1 15 0 1 2 0 1 9 0 1 10 0 1 4 0 1 4 0 1 4 0 1 4 0 1","13 0 11 0 1 16 0 1 16 0 1 5 8 2 17 0 1 17 0 1 11 0 1 4 0 1 2 0 1 4 0 1 4 0 1 4 0 1 1 0 1","13 0 9 0 1 10 0 1 10 0 1 1 0 1 16 0 1 16 0 1 9 0 1 9 0 1 10 0 1 4 0 1 4 0 1 4 0 1 1 0 1","13 3 4 0 1 1 0 1 1 0 1 1 0 1 1 0 1 3 0 1 2 0 1 3 0 1 3 0 1 4 0 1 9 0 1 9 0 1 1 0 1 6 3 6 6 7 6 6 8 9","13 2 11 0 1 15 0 1 15 0 1 1 0 1 15 0 1 15 0 1 11 0 1 3 0 1 7 7 8 2 0 1 1 0 1 10 0 1 9 0 1 6 3 6 6 7 4","13 2 9 0 1 17 0 1 17 0 1 1 0 1 17 0 1 17 0 1 9 0 1 3 0 1 1 0 1 2 0 1 1 0 1 8 0 1 10 0 1 6 3 6 6 7 6","13 2 4 0 1 16 0 1 16 0 1 10 0 1 16 0 1 16 0 1 4 0 1 3 0 1 10 0 1 9 0 1 1 0 1 9 0 1 8 0 1 6 3 1 6 7 2","13 1 11 0 1 1 0 1 10 0 1 11 0 1 4 0 1 3 0 1 11 0 1 3 0 1 1 0 1 10 0 1 9 0 1 1 0 1 9 0 1 6 7 18","13 0 9 0 1 15 0 1 1 0 1 3 0 1 15 0 1 1 0 1 9 0 1 3 0 1 10 0 1 8 0 1 10 0 1 1 0 1 4 0 1","13 0 4 0 1 17 0 1 15 0 1 3 0 1 17 0 1 1 0 1 4 0 1 3 0 1 3 0 1 9 0 1 8 0 1 9 0 1 9 0 1","13 1 11 0 1 16 0 1 17 0 1 2 0 1 16 0 1 1 0 1 9 0 1 1 0 1 3 0 1 3 0 1 9 0 1 1 0 1 10 0 1 6 3 14","13 0 9 0 1 1 0 1 16 0 1 10 0 1 2 0 1 12 0 1 4 0 1 1 0 1 10 0 1 3 0 1 1 0 1 9 0 1 8 0 1","13 0 3 0 1 15 0 1 3 0 1 11 0 1 15 0 1 8 0 1 9 0 1 12 0 1 3 0 1 3 0 1 9 0 1 1 0 1 9 0 1","13 0 2 0 1 17 0 1 15 0 1 1 0 1 17 0 1 9 0 1 10 0 1 8 0 1 2 0 1 2 0 1 3 0 1 9 0 1 2 0 1","13 0 11 0 1 16 0 1 17 0 1 10 0 1 16 0 1 3 0 1 8 0 1 9 0 1 9 0 1 2 0 1 1 0 1 10 0 1 9 0 1","13 1 9 0 1 4 0 1 16 0 1 4 0 1 4 0 1 1 0 1 9 0 1 1 0 1 3 0 1 9 0 1 9 0 1 8 0 1 4 0 1 6 0 9","13 0 3 0 1 2 0 1 2 0 1 10 0 1 15 0 1 9 0 1 1 0 1 12 0 1 2 0 1 4 0 1 3 0 1 9 0 1 2 0 1","13 0 11 0 1 15 0 1 15 0 1 4 0 1 17 0 1 4 0 1 9 0 1 8 0 1 9 0 1 9 0 1 9 0 1 3 0 1 9 0 1","13 0 9 0 1 17 0 1 17 0 1 2 0 1 16 0 1 9 0 1 4 0 1 9 0 1 0 0 1 4 0 1 10 0 1 12 0 1 4 0 1","13 0 0 0 1 16 0 1 16 0 1 9 0 1 0 0 1 0 0 1 1 0 1 0 0 1 0 0 1 4 0 1 8 0 1 8 0 1 9 0 1","13 0 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1 9 0 1 9 0 1 9 0 1 0 0 1","1 10 5 0 5 6 7 3 6 8 16 3 0 17 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1","8 6 4 0 1 5 0 5 4 0 1 4 0 1 3 0 1 5 0 2 10 0 1 4 0 1 6 6 6 1 0 1 1 0 1 1 0 1 1 0 1 4 8 2","12 1 15 0 1 4 0 1 4 0 1 2 0 1 5 0 5 3 0 1 7 3 2 4 0 1 3 0 1 1 0 1 4 0 1 4 0 1 6 8 2","12 0 16 0 1 15 0 1 4 0 1 2 0 1 15 0 1 15 0 1 2 0 1 4 0 1 3 0 1 1 0 1 4 0 1 5 8 1","12 1 1 0 1 17 0 1 4 0 1 2 0 1 17 0 1 17 0 1 10 0 1 1 0 1 1 0 1 1 0 1 1 0 1 4 0 1 6 8 1","12 0 15 0 1 16 0 1 9 0 1 2 0 1 16 0 1 16 0 1 4 0 1 1 0 1 1 0 1 1 0 1 1 0 1 10 0 1","12 2 17 0 1 1 0 1 3 0 1 9 0 1 1 0 1 10 0 1 10 0 1 1 0 1 1 0 1 1 0 1 1 0 1 11 0 1 6 3 6 6 6 6","12 2 16 0 1 15 0 1 1 0 1 4 0 1 15 0 1 3 0 1 2 0 1 9 0 1 9 0 1 12 0 1 1 0 1 4 0 1 6 3 3 6 6 3","12 0 4 0 1 17 0 1 1 0 1 4 0 1 17 0 1 15 0 1 10 0 1 10 0 1 3 0 1 8 1 1 9 0 1 10 0 1","12 0 15 0 1 16 0 1 9 0 1 9 0 1 16 0 1 17 0 1 3 0 1 8 0 1 12 0 1 9 0 1 10 0 1 2 0 1","12 0 17 0 1 1 0 1 10 0 1 10 0 1 1 0 1 16 0 1 10 0 1 9 0 1 8 1 1 3 0 1 8 0 1 10 0 1","12 0 16 0 1 15 0 1 8 0 1 8 0 1 15 0 1 3 0 1 2 0 1 4 0 1 9 0 1 12 0 1 9 0 1 2 0 1","12 0 2 0 1 17 0 1 9 0 1 9 0 1 17 0 1 1 0 1 10 0 1 1 0 1 2 0 1 8 1 1 3 0 1 10 0 1","12 1 15 0 1 16 0 1 4 0 1 4 0 1 16 0 1 9 0 1 4 0 1 9 0 1 9 0 1 9 0 1 3 0 1 4 0 1 6 3 14","12 1 17 0 1 1 0 1 1 0 1 9 0 1 10 0 1 3 0 1 10 0 1 10 0 1 3 0 1 3 0 1 9 0 1 9 0 1 6 6 9","12 0 16 0 1 15 0 1 9 0 1 4 0 1 3 0 1 2 0 1 4 0 1 8 0 1 9 0 1 12 0 1 2 0 1 1 0 1","12 1 10 0 1 17 0 1 10 0 1 9 0 1 15 0 1 9 0 1 9 0 1 9 0 1 3 0 1 8 1 1 10 0 1 10 0 1 6 0 7","12 0 4 0 1 16 0 1 8 0 1 10 0 1 17 0 1 4 0 1 3 0 1 3 0 1 1 0 1 9 0 1 2 0 1 4 0 1","12 1 15 0 1 4 0 1 9 0 1 8 1 1 16 0 1 9 0 1 2 0 1 3 0 1 9 0 1 3 0 1 2 0 1 9 0 1 6 0 6","12 0 17 0 1 2 0 1 1 0 1 9 0 1 2 0 1 4 0 1 9 0 1 9 0 1 1 0 1 9 0 1 2 0 1 1 0 1","12 1 16 0 1 15 0 1 9 0 1 1 0 1 15 0 1 1 0 1 0 0 1 3 0 1 9 0 1 10 0 1 7 7 3 1 0 1 6 7 3","12 0 10 0 1 17 0 1 10 0 1 9 0 1 17 0 1 9 0 1 0 0 1 3 0 1 10 0 1 8 0 1 4 0 1 1 0 1","12 0 2 0 1 16 0 1 8 0 1 0 0 1 16 0 1 0 0 1 0 0 1 9 0 1 8 1 1 9 0 1 17 0 1 9 0 1","12 0 10 0 1 10 0 1 9 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1 0 0 1","1 10 5 0 5 6 8 5 3 0 9 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1","9 4 3 0 1 5 0 5 5 8 3 4 0 1 5 0 5 4 0 1 4 0 1 4 0 1 5 0 5 1 0 1 1 0 1 1 0 1 4 8 4","12 1 15 0 1 4 0 1 11 0 1 2 0 1 4 0 1 1 0 1 9 0 1 2 0 1 15 0 1 3 0 1 4 0 1 5 0 2 6 8 4","12 0 17 0 1 4 0 1 9 0 1 9 0 1 4 0 1 1 0 1 2 0 1 2 0 1 17 0 1 1 0 1 1 0 1 3 0 1","12 0 16 0 1 15 0 1 4 0 1 2 0 1 1 0 1 1 0 1 9 0 1 9 0 1 16 0 1 1 0 1 1 0 1 15 0 1","12 1 10 0 1 17 0 1 4 0 1 2 0 1 10 0 1 1 0 1 4 0 1 4 0 1 10 0 1 1 0 1 10 0 1 17 0 1 6 8 2","12 3 1 0 1 16 0 1 11 0 1 9 0 1 3 0 1 9 0 1 9 0 1 9 0 1 1 0 1 1 0 1 17 0 1 16 0 1 6 3 6 6 6 6 6 7 6","12 4 15 0 1 1 0 1 9 0 1 4 0 1 3 0 1 10 0 1 2 0 1 2 0 1 15 0 1 9 0 1 1 0 1 3 0 1 6 3 6 6 6 3 6 7 3 6 8 2","12 2 17 0 1 15 0 1 4 0 1 9 0 1 3 0 1 8 0 1 9 0 1 2 0 1 16 0 1 10 0 1 10 0 1 15 0 1 6 3 6 6 0 6","12 2 16 0 1 17 0 1 11 0 1 4 0 1 3 0 1 9 0 1 4 0 1 9 0 1 1 0 1 8 0 1 4 0 1 17 0 1 6 3 6 6 8 1","12 2 10 0 1 16 0 1 9 0 1 9 0 1 10 0 1 4 0 1 9 0 1 10 0 1 15 0 1 9 0 1 1 0 1 16 0 1 6 7 9 6 8 1","12 1 1 0 1 4 0 1 4 0 1 10 0 1 3 0 1 9 0 1 10 0 1 8 0 1 17 0 1 3 0 1 9 0 1 1 0 1 6 8 2","12 1 15 0 1 15 0 1 1 0 1 8 0 1 2 0 1 4 0 1 8 0 1 9 0 1 16 0 1 3 0 1 3 0 1 1 0 1 6 0 7","12 3 17 0 1 17 0 1 9 0 1 9 0 1 10 0 1 2 0 1 9 0 1 4 0 1 1 0 1 9 0 1 3 0 1 9 0 1 6 3 14 6 6 9 6 8 1","12 0 16 0 1 16 0 1 1 0 1 4 0 1 4 0 1 9 0 1 1 0 1 4 0 1 15 0 1 3 0 1 9 0 1 10 0 1","12 0 3 0 1 2 0 1 9 0 1 9 0 1 4 0 1 4 0 1 9 0 1 9 0 1 17 0 1 9 0 1 1 0 1 8 0 1","12 1 15 0 1 15 0 1 10 0 1 4 0 1 7 7 9 2 0 1 4 0 1 10 0 1 16 0 1 10 0 1 9 0 1 9 0 1 6 7 9","12 0 17 0 1 17 0 1 8 0 1 9 0 1 3 0 1 9 0 1 9 0 1 8 0 1 4 0 1 8 0 1 4 0 1 3 0 1","12 0 16 0 1 16 0 1 9 0 1 10 0 1 3 0 1 1 0 1 10 0 1 9 0 1 2 0 1 9 0 1 4 0 1 9 0 1","12 0 2 0 1 4 0 1 1 0 1 8 0 1 3 0 1 1 0 1 8 0 1 3 0 1 15 0 1 2 0 1 4 0 1 10 0 1","12 0 15 0 1 15 0 1 9 0 1 9 0 1 9 0 1 9 0 1 9 0 1 9 0 1 17 0 1 9 0 1 9 0 1 8 0 1","12 0 17 0 1 17 0 1 0 0 1 1 0 1 3 0 1 4 0 1 1 0 1 3 0 1 16 0 1 2 0 1 4 0 1 9 0 1","12 0 16 0 1 1 0 1 0 0 1 9 0 1 9 0 1 9 0 1 9 0 1 3 0 1 4 0 1 9 0 1 2 0 1 2 0 1","12 0 3 0 1 9 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 9 0 1 9 0 1 0 0 1 9 0 1 9 0 1","1 10 4 0 1 6 6 15 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1","10 5 10 0 1 5 0 4 5 0 6 2 0 1 4 0 1 5 0 7 4 0 1 2 0 1 4 0 1 4 0 1 6 3 10 6 7 3 1 0 1 1 0 1 4 8 2","12 0 2 0 1 5 0 2 15 0 1 4 0 1 4 0 1 4 0 1 3 0 1 4 0 1 2 0 1 1 0 1 1 0 1 3 0 1","12 0 10 0 1 15 0 1 17 0 1 2 0 1 4 0 1 15 0 1 3 0 1 10 0 1 10 0 1 10 0 1 1 0 1 3 0 1","12 0 3 0 1 17 0 1 16 0 1 10 0 1 10 0 1 16 0 1 3 0 1 12 0 1 4 0 1 3 0 1 1 0 1 1 0 1","12 0 10 0 1 16 0 1 1 0 1 12 0 1 12 0 1 4 0 1 3 0 1 8 0 1 2 0 1 3 0 1 10 0 1 9 0 1","12 2 7 3 4 1 0 1 15 0 1 8 0 1 8 0 1 15 0 1 9 0 1 9 0 1 2 0 1 3 0 1 4 0 1 10 0 1 6 3 4 6 8 13","12 0 1 0 1 15 0 1 17 0 1 9 0 1 9 0 1 17 0 1 10 0 1 4 0 1 10 0 1 1 0 1 4 0 1 8 0 1","12 1 7 7 4 17 0 1 16 0 1 3 0 1 4 0 1 16 0 1 8 0 1 10 0 1 12 0 1 10 0 1 4 0 1 9 0 1 6 7 4","12 0 4 0 1 16 0 1 1 0 1 10 0 1 10 0 1 10 0 1 9 0 1 12 0 1 4 0 1 4 0 1 9 0 1 3 0 1","12 0 4 0 1 1 0 1 15 0 1 12 0 1 12 0 1 1 0 1 3 0 1 8 0 1 4 0 1 2 0 1 4 0 1 9 0 1","12 0 4 0 1 15 0 1 17 0 1 8 0 1 8 0 1 15 0 1 9 0 1 9 0 1 9 0 1 2 0 1 9 0 1 10 0 1","12 2 4 0 1 17 0 1 16 0 1 9 0 1 9 0 1 4 0 1 10 0 1 4 0 1 4 0 1 7 7 8 1 0 1 8 0 1 6 7 8 6 0 27","12 0 9 0 1 16 0 1 3 0 1 2 0 1 4 0 1 2 0 1 8 1 1 10 0 1 2 0 1 1 0 1 9 0 1 9 0 1","12 0 3 0 1 1 0 1 15 0 1 10 0 1 9 0 1 15 0 1 9 0 1 12 0 1 10 0 1 1 0 1 1 0 1 4 0 1","12 0 1 0 1 15 0 1 2 0 1 12 0 1 10 0 1 3 0 1 1 0 1 8 0 1 1 0 1 1 0 1 9 0 1 1 0 1","12 0 9 0 1 16 0 1 15 0 1 8 0 1 8 1 1 3 0 1 9 0 1 9 0 1 1 0 1 9 0 1 10 0 1 1 0 1","12 0 4 0 1 4 0 1 16 0 1 9 0 1 9 0 1 3 0 1 1 0 1 3 0 1 9 0 1 10 0 1 3 0 1 9 0 1","12 0 1 0 1 2 0 1 2 0 1 2 0 1 1 0 1 3 0 1 9 0 1 2 0 1 10 0 1 8 0 1 9 0 1 1 0 1","12 0 9 0 1 15 0 1 15 0 1 9 0 1 1 0 1 3 0 1 10 0 1 10 0 1 0 0 1 9 0 1 3 0 1 9 0 1","12 0 1 0 1 2 0 1 17 0 1 10 0 1 1 0 1 3 0 1 4 0 1 12 0 1 0 0 1 3 0 1 9 0 1 3 0 1","12 1 1 0 1 15 0 1 16 0 1 0 0 1 1 0 1 15 0 1 1 0 1 8 1 1 0 0 1 1 0 1 2 0 1 9 0 1 6 6 3","12 0 9 0 1 16 0 1 10 0 1 0 0 1 9 0 1 16 0 1 9 0 1 9 0 1 0 0 1 9 0 1 9 0 1 3 0 1","12 0 10 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 10 0 1 0 0 1 0 0 1 0 0 1 4 0 1 10 0 1","1 10 10 0 1 6 0 25 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1","10 4 7 6 3 3 0 1 4 0 1 4 0 1 4 0 1 4 0 1 12 0 1 1 0 1 4 0 1 4 0 1 6 6 9 1 0 1 1 0 1 4 8 4","12 2 1 0 1 1 0 1 4 0 1 4 0 1 4 0 1 4 0 1 2 0 1 4 0 1 3 0 1 3 0 1 4 0 1 4 0 1 6 1 2 6 8 15","12 0 1 0 1 1 0 1 4 0 1 4 0 1 4 0 1 4 0 1 2 0 1 4 0 1 3 0 1 1 0 1 8 0 1 4 0 1","12 0 10 0 1 1 0 1 4 0 1 4 0 1 10 0 1 1 0 1 2 0 1 1 0 1 3 0 1 1 0 1 9 0 1 2 0 1","12 0 2 0 1 9 0 1 2 0 1 2 0 1 3 0 1 1 0 1 9 0 1 1 0 1 3 0 1 1 0 1 2 0 1 12 0 1","12 2 10 0 1 1 0 1 9 0 1 2 0 1 3 0 1 9 0 1 1 0 1 1 0 1 1 0 1 9 0 1 12 0 1 8 0 1 6 3 6 6 6 3","12 1 3 0 1 9 0 1 1 0 1 9 0 1 1 0 1 10 0 1 9 0 1 9 0 1 1 0 1 3 0 1 8 0 1 9 0 1 6 3 6","12 1 10 0 1 10 0 1 1 0 1 1 0 1 1 0 1 8 0 1 4 0 1 10 0 1 9 0 1 3 0 1 9 0 1 4 0 1 6 3 6","12 1 2 0 1 3 0 1 1 0 1 9 0 1 10 0 1 9 0 1 9 0 1 8 0 1 3 0 1 3 0 1 4 0 1 2 0 1 6 3 4","12 0 10 0 1 10 0 1 9 0 1 1 0 1 3 0 1 4 0 1 4 0 1 9 0 1 9 0 1 3 0 1 9 0 1 2 0 1","12 1 7 6 12 2 0 1 1 0 1 9 0 1 1 0 1 2 0 1 4 0 1 3 0 1 2 0 1 9 0 1 4 0 1 2 0 1 6 6 9","12 1 16 0 1 9 0 1 1 0 1 4 0 1 10 0 1 9 0 1 2 0 1 1 0 1 2 0 1 10 0 1 9 0 1 9 0 1 6 6 3","12 2 1 0 1 10 0 1 9 0 1 1 0 1 2 0 1 10 0 1 9 0 1 9 0 1 9 0 1 4 0 1 1 0 1 3 0 1 6 3 22 6 8 1","12 0 16 0 1 4 0 1 10 0 1 9 0 1 2 0 1 8 0 1 10 0 1 3 0 1 3 0 1 1 0 1 9 0 1 2 0 1","12 1 1 0 1 4 0 1 3 0 1 10 0 1 2 0 1 9 0 1 4 0 1 9 0 1 1 0 1 9 0 1 0 0 1 9 0 1 6 8 1","12 1 16 0 1 2 0 1 9 0 1 3 0 1 7 7 12 1 0 1 9 0 1 4 0 1 9 0 1 10 0 1 0 0 1 4 0 1 6 7 12","12 1 4 0 1 2 0 1 10 0 1 3 0 1 16 0 1 9 0 1 10 0 1 4 0 1 10 0 1 0 0 1 0 0 1 9 0 1 6 8 1","12 1 16 0 1 2 0 1 3 0 1 16 0 1 17 0 1 10 0 1 0 0 1 9 0 1 4 0 1 0 0 1 0 0 1 10 0 1 6 8 1","12 2 1 0 1 7 1 7 9 0 1 3 0 1 1 0 1 4 0 1 0 0 1 10 0 1 9 0 1 0 0 1 0 0 1 4 0 1 6 1 7 6 8 2","12 0 16 0 1 3 0 1 10 0 1 16 0 1 16 0 1 9 0 1 0 0 1 0 0 1 4 0 1 0 0 1 0 0 1 9 0 1","12 1 0 0 1 16 0 1 1 0 1 1 0 1 0 0 1 10 0 1 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1 10 0 1 6 8 1","12 0 0 0 1 1 0 1 9 0 1 16 0 1 0 0 1 0 0 1 0 0 1 0 0 1 2 0 1 0 0 1 0 0 1 0 0 1","12 0 0 0 1 16 0 1 10 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 16 0 1 0 0 1 0 0 1 0 0 1","1 10 4 0 1 6 0 75 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1","10 3 4 0 1 4 0 1 4 0 1 4 0 1 3 0 1 4 0 1 3 0 1 4 0 1 4 0 1 4 0 1 1 0 1 1 0 1 4 8 2","12 1 4 0 1 4 0 1 1 0 1 2 0 1 3 0 1 4 0 1 1 0 1 4 0 1 4 0 1 4 0 1 1 0 1 3 0 1 6 8 14","12 0 2 0 1 4 0 1 1 0 1 9 0 1 3 0 1 1 0 1 1 0 1 4 0 1 4 0 1 10 0 1 1 0 1 3 0 1","12 0 9 0 1 4 0 1 1 0 1 10 0 1 3 0 1 10 0 1 1 0 1 4 0 1 9 0 1 3 0 1 1 0 1 1 0 1","12 0 10 0 1 1 0 1 1 0 1 2 0 1 1 0 1 3 0 1 9 0 1 9 0 1 10 0 1 3 0 1 1 0 1 1 0 1","12 0 2 0 1 9 0 1 9 0 1 9 0 1 9 0 1 3 0 1 10 0 1 10 0 1 2 0 1 3 0 1 2 0 1 1 0 1","12 0 9 0 1 10 0 1 10 0 1 10 0 1 10 0 1 3 0 1 3 0 1 3 0 1 9 0 1 1 0 1 2 0 1 9 0 1","12 1 10 0 1 2 0 1 3 0 1 2 0 1 4 0 1 3 0 1 3 0 1 3 0 1 10 0 1 1 0 1 2 0 1 10 0 1 6 1 1","12 0 2 0 1 2 0 1 2 0 1 2 0 1 4 0 1 10 0 1 2 0 1 3 0 1 2 0 1 10 0 1 2 0 1 3 0 1","12 0 9 0 1 2 0 1 9 0 1 9 0 1 4 0 1 3 0 1 2 0 1 3 0 1 2 0 1 3 0 1 4 0 1 9 0 1","12 1 10 0 1 9 0 1 10 0 1 10 0 1 4 0 1 2 0 1 9 0 1 6 0 1 9 0 1 2 0 1 2 0 1 10 0 1 6 6 3","12 1 3 0 1 10 0 1 2 0 1 3 0 1 6 0 1 10 0 1 10 0 1 4 0 1 10 0 1 2 0 1 2 0 1 4 0 1 6 1 4","12 0 3 0 1 3 0 1 2 0 1 1 0 1 1 0 1 4 0 1 2 0 1 4 0 1 3 0 1 10 0 1 2 0 1 2 0 1","12 0 3 0 1 3 0 1 2 0 1 1 0 1 1 0 1 4 0 1 9 0 1 2 0 1 3 0 1 4 0 1 9 0 1 9 0 1","12 2 1 0 1 3 0 1 6 0 1 1 0 1 1 0 1 6 0 1 10 0 1 2 0 1 1 0 1 6 0 1 10 0 1 10 0 1 6 7 3 6 0 5","12 1 1 0 1 3 0 1 4 0 1 1 0 1 1 0 1 4 0 1 4 0 1 9 0 1 1 0 1 16 0 1 2 0 1 4 0 1 6 6 3","12 2 6 0 1 1 0 1 4 0 1 6 0 1 12 0 1 1 0 1 4 0 1 10 0 1 1 0 1 17 0 1 9 0 1 4 0 1 6 0 14 6 8 1","12 1 4 0 1 6 0 1 1 0 1 1 0 1 4 0 1 1 0 1 4 0 1 3 0 1 6 0 1 3 0 1 10 0 1 2 0 1 6 0 13","12 1 9 0 1 9 0 1 16 0 1 16 0 1 4 0 1 16 0 1 6 0 1 3 0 1 1 0 1 16 0 1 1 0 1 6 0 1 6 0 15","12 1 1 0 1 2 0 1 4 0 1 6 0 1 2 0 1 4 0 1 3 0 1 1 0 1 1 0 1 17 0 1 1 0 1 1 0 1 6 8 1","12 0 16 0 1 9 0 1 4 0 1 17 0 1 9 0 1 4 0 1 3 0 1 1 0 1 16 0 1 1 0 1 1 0 1 16 0 1","12 2 0 0 1 0 0 1 9 0 1 0 0 1 3 0 1 9 0 1 16 0 1 6 0 1 17 0 1 16 0 1 6 0 1 17 0 1 6 6 3 6 0 11",},

    {"1 1 0 0 1 4 0 13","1 10 1 0 1 6 0 8 3 0 7 3 4 12 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 5 10 2 5 11 2","6 1 4 0 1 5 10 1 4 0 1 1 0 1 4 0 1 5 10 1 6 0 1","6 1 4 0 1 1 0 1 5 11 1 1 0 1 1 0 1 14 0 1 4 0 1","6 2 8 4 1 14 0 1 5 0 1 1 0 1 5 11 1 7 10 1 6 0 1 4 0 1","6 2 9 0 1 7 10 1 4 0 1 1 0 1 5 0 1 17 0 1 6 0 1 4 0 1","6 2 4 0 1 17 0 1 14 0 1 8 4 1 4 0 1 4 0 1 6 0 1 4 0 1","6 2 8 4 1 4 0 1 7 11 1 9 0 1 1 0 1 4 0 1 6 0 1 4 0 1","6 2 9 0 1 1 0 1 15 0 1 4 0 1 14 0 1 4 0 1 6 0 1 4 0 1","6 2 3 0 1 8 4 1 17 0 1 4 0 1 7 11 1 8 4 1 6 0 1 4 0 1","6 2 3 0 1 9 0 1 1 0 1 4 0 1 15 0 1 9 0 1 6 0 1 4 0 1","6 2 17 0 1 4 0 1 1 0 1 4 0 1 17 0 1 4 0 1 6 0 1 4 0 1","6 0 0 0 1 8 4 1 1 0 1 8 0 1 4 0 1 8 4 1","6 0 4 0 1 9 0 1 8 4 1 9 0 1 1 0 1 9 0 1","6 0 3 0 1 4 0 1 9 0 1 1 0 1 1 0 1 1 0 1","6 0 0 0 1 8 4 1 1 0 1 8 0 1 8 4 1 8 0 1","6 0 4 0 1 9 0 1 8 4 1 9 0 1 9 0 1 9 0 1","6 0 3 0 1 4 0 1 9 0 1 3 0 1 4 0 1 0 0 1","6 0 0 0 1 8 0 1 3 0 1 8 0 1 8 0 1 0 0 1","6 0 4 0 1 9 0 1 8 4 1 9 0 1 9 0 1 3 0 1","6 0 0 0 1 0 0 1 9 0 1 3 0 1 0 0 1 0 0 1","6 0 0 0 1 0 0 1 0 0 1 8 0 1 0 0 1 0 0 1","6 0 0 0 1 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1","6 0 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1","1 4 5 0 1 1 0 1 1 0 1 1 0 1 1 0 1","5 0 4 0 1 4 0 1 4 0 1 4 0 1 5 0 1","5 0 1 0 1 5 0 1 4 0 1 1 0 1 1 0 1","5 0 15 0 1 15 0 1 1 0 1 1 0 1 15 0 1","5 0 17 0 1 17 0 1 14 0 1 1 0 1 17 0 1","5 0 16 0 1 16 0 1 4 0 1 14 0 1 16 0 1","5 2 3 0 1 7 8 1 4 0 1 0 0 1 2 0 1 6 8 1 4 0 3","5 2 2 0 1 4 0 1 1 0 1 2 0 1 7 8 1 6 8 1 4 0 4","5 2 7 8 1 16 0 1 9 0 1 2 0 1 4 0 1 6 8 1 4 0 2","5 0 0 0 1 17 0 1 1 0 1 5 0 1 17 0 1","5 0 0 0 1 3 0 1 9 0 1 4 0 1 0 0 1","5 0 0 0 1 6 0 1 3 0 1 15 0 1 0 0 1","5 0 0 0 1 0 0 1 1 0 1 0 0 1 0 0 1","5 0 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1","5 0 0 0 1 0 0 1 4 0 1 0 0 1 0 0 1","5 0 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1","5 0 0 0 1 0 0 1 1 0 1 0 0 1 0 0 1","5 0 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1","5 0 0 0 1 0 0 1 3 0 1 0 0 1 0 0 1","5 0 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1","5 0 0 0 1 0 0 1 3 0 1 0 0 1 0 0 1","5 0 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1","5 0 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1","5 0 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1","1 6 5 0 4 6 8 1 1 0 1 1 0 1 1 0 1 1 0 1 3 0 5","5 0 15 0 1 4 0 1 4 0 1 4 0 1 4 0 1","5 1 17 0 1 4 0 1 4 0 1 1 0 1 1 0 1 6 0 2","5 0 16 0 1 1 0 1 4 0 1 1 0 1 1 0 1","5 0 1 0 1 1 0 1 4 0 1 1 0 1 9 0 1","5 0 15 0 1 1 0 1 1 0 1 1 0 1 1 0 1","5 0 17 0 1 1 0 1 9 0 1 9 0 1 9 0 1","5 0 16 0 1 9 0 1 3 0 1 1 0 1 4 0 1","5 0 4 0 1 3 0 1 9 0 1 9 0 1 9 0 1","5 0 15 0 1 4 0 1 1 0 1 4 0 1 4 0 1","5 0 17 0 1 4 0 1 9 0 1 9 0 1 4 0 1","5 0 16 0 1 4 0 1 1 0 1 4 0 1 9 0 1","5 0 2 0 1 2 0 1 9 0 1 4 0 1 10 0 1","5 0 15 0 1 3 0 1 3 0 1 9 0 1 8 0 1","5 0 17 0 1 2 0 1 9 0 1 10 0 1 9 0 1","5 0 16 0 1 2 0 1 2 0 1 8 0 1 1 0 1","5 0 3 0 1 9 0 1 9 0 1 9 0 1 9 0 1","5 2 7 8 4 1 0 1 4 0 1 3 0 1 10 0 1 6 8 4 5 10 1","5 0 5 10 1 1 0 1 4 0 1 9 0 1 8 0 1","5 0 1 0 1 4 0 1 9 0 1 4 0 1 9 0 1","5 0 1 0 1 9 0 1 1 0 1 4 0 1 3 0 1","5 0 7 10 1 4 0 1 9 0 1 0 0 1 2 0 1","5 0 17 0 1 0 0 1 0 0 1 0 0 1 9 0 1","5 0 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1","1 6 5 0 3 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 3 0 5","6 0 4 0 1 4 0 1 4 0 1 4 0 1 4 0 1 4 0 1","6 1 15 0 1 4 0 1 4 0 1 1 0 1 4 0 1 4 0 1 6 0 2","6 0 17 0 1 4 0 1 4 0 1 1 0 1 4 0 1 4 0 1","6 0 16 0 1 1 0 1 1 0 1 1 0 1 4 0 1 1 0 1","6 0 1 0 1 9 0 1 1 0 1 1 0 1 1 0 1 1 0 1","6 0 15 0 1 4 0 1 1 0 1 9 0 1 9 0 1 1 0 1","6 0 17 0 1 9 0 1 1 0 1 1 0 1 10 0 1 1 0 1","6 0 16 0 1 2 0 1 9 0 1 9 0 1 8 0 1 9 0 1","6 0 3 0 1 9 0 1 10 0 1 4 0 1 9 0 1 10 0 1","6 0 1 0 1 4 0 1 8 0 1 9 0 1 1 0 1 8 0 1","6 0 15 0 1 9 0 1 9 0 1 2 0 1 9 0 1 9 0 1","6 0 17 0 1 3 0 1 1 0 1 9 0 1 10 0 1 2 0 1","6 0 16 0 1 3 0 1 9 0 1 2 0 1 8 0 1 9 0 1","6 0 2 0 1 3 0 1 3 0 1 9 0 1 9 0 1 2 0 1","6 0 2 0 1 3 0 1 3 0 1 0 0 1 1 0 1 9 0 1","6 2 7 8 3 1 0 1 3 0 1 0 0 1 9 0 1 4 0 1 6 8 3 5 10 1","6 0 16 0 1 17 0 1 2 0 1 3 0 1 1 0 1 9 0 1","6 1 7 8 1 2 0 1 2 0 1 2 0 1 9 0 1 3 0 1 6 8 1","6 0 17 0 1 17 0 1 2 0 1 2 0 1 0 0 1 3 0 1","6 0 1 0 1 0 0 1 2 0 1 5 10 1 0 0 1 3 0 1","6 0 16 0 1 0 0 1 6 0 1 4 0 1 0 0 1 2 0 1","6 0 17 0 1 0 0 1 0 0 1 4 0 1 0 0 1 2 0 1","6 0 0 0 1 0 0 1 0 0 1 7 10 1 0 0 1 6 0 1","1 6 5 0 5 1 0 1 1 0 1 1 0 1 1 0 1 3 0 5 3 1 3","5 0 15 0 1 4 0 1 4 0 1 4 0 1 4 0 1","5 0 17 0 1 4 0 1 4 0 1 4 0 1 4 0 1","5 1 16 0 1 1 0 1 4 0 1 1 0 1 4 0 1 6 8 1","5 1 1 0 1 17 0 1 1 0 1 1 0 1 4 0 1 3 3 1","5 1 15 0 1 2 0 1 1 0 1 1 0 1 1 0 1 6 0 2","5 0 17 0 1 17 0 1 1 0 1 9 0 1 1 0 1","5 0 16 0 1 3 0 1 1 0 1 3 0 1 1 0 1","5 0 4 0 1 1 0 1 1 0 1 1 0 1 9 0 1","5 0 15 0 1 1 0 1 9 0 1 9 0 1 10 0 1","5 0 17 0 1 17 0 1 10 0 1 2 0 1 8 0 1","5 0 16 0 1 4 0 1 8 0 1 16 0 1 9 0 1","5 1 2 0 1 4 0 1 9 0 1 17 0 1 1 0 1 4 0 1","5 0 15 0 1 2 0 1 3 0 1 2 0 1 9 0 1","5 1 17 0 1 2 0 1 9 0 1 2 0 1 10 0 1 4 0 1","5 1 16 0 1 17 0 1 3 0 1 7 8 1 8 0 1 6 8 1","5 1 4 0 1 4 0 1 3 0 1 0 0 1 9 0 1 4 0 1","5 0 15 0 1 0 0 1 2 0 1 0 0 1 2 0 1","5 1 17 0 1 0 0 1 2 0 1 0 0 1 2 0 1 4 0 1","5 0 16 0 1 0 0 1 2 0 1 0 0 1 2 0 1","5 1 3 0 1 0 0 1 2 0 1 0 0 1 9 0 1 4 0 1","5 0 3 0 1 0 0 1 6 0 1 0 0 1 0 0 1","5 3 7 8 5 0 0 1 0 0 1 0 0 1 0 0 1 6 8 4 4 0 1 3 3 3","5 0 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1","1 5 5 0 5 6 8 1 1 0 1 1 0 1 1 0 1 3 0 4","4 2 4 0 1 4 0 1 4 0 1 4 0 1 1 0 1 1 0 1","6 0 15 0 1 5 0 4 4 0 1 4 0 1 4 0 1 4 0 1","6 2 17 0 1 15 0 1 1 0 1 4 0 1 4 0 1 4 0 1 6 0 2 3 3 1","6 0 16 0 1 17 0 1 1 0 1 1 0 1 4 0 1 1 0 1","6 0 4 0 1 16 0 1 1 0 1 1 0 1 4 0 1 1 0 1","6 0 15 0 1 1 0 1 9 0 1 9 0 1 4 0 1 1 0 1","6 0 17 0 1 15 0 1 1 0 1 4 0 1 9 0 1 1 0 1","6 0 16 0 1 17 0 1 1 0 1 4 0 1 3 0 1 1 0 1","6 0 3 0 1 16 0 1 9 0 1 9 0 1 9 0 1 9 0 1","6 0 3 0 1 1 0 1 10 0 1 10 0 1 1 0 1 3 0 1","6 2 7 8 1 15 0 1 8 3 1 8 3 1 9 0 1 9 0 1 6 8 1 3 3 1","6 0 1 0 1 17 0 1 9 0 1 9 0 1 1 0 1 4 0 1","6 0 1 0 1 16 0 1 2 0 1 1 0 1 9 0 1 4 0 1","6 0 1 0 1 4 0 1 9 0 1 9 0 1 1 0 1 2 0 1","6 0 1 0 1 2 0 1 3 0 1 10 0 1 9 0 1 3 0 1","6 0 9 0 1 15 0 1 9 0 1 8 3 1 10 0 1 9 0 1","6 0 4 0 1 17 0 1 2 0 1 9 0 1 8 3 1 4 0 1","6 0 9 0 1 16 0 1 9 0 1 1 0 1 9 0 1 4 0 1","6 0 3 0 1 3 0 1 3 0 1 9 0 1 1 0 1 0 0 1","6 0 2 0 1 2 0 1 2 0 1 0 0 1 9 0 1 0 0 1","6 2 9 0 1 7 8 4 2 0 1 0 0 1 4 0 1 0 0 1 6 8 4 3 3 2","6 0 0 0 1 0 0 1 6 0 1 0 0 1 9 0 1 0 0 1","6 0 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1","1 10 4 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 3 0 2 3 1 1 3 3 1","8 3 1 0 1 5 0 1 4 0 1 0 0 1 4 0 1 5 0 5 0 0 1 4 0 1 6 8 1 1 0 1 3 3 1","9 0 10 0 1 5 0 3 4 0 1 0 0 1 4 0 1 4 0 1 4 0 1 0 0 1 4 0 1","9 0 2 0 1 15 0 1 4 0 1 0 0 1 4 0 1 15 0 1 4 0 1 0 0 1 4 0 1","9 0 10 0 1 17 0 1 4 0 1 0 0 1 4 0 1 17 0 1 1 0 1 0 0 1 4 0 1","9 0 3 0 1 16 0 1 1 0 1 0 0 1 1 0 1 16 0 1 1 0 1 0 0 1 1 0 1","9 7 7 7 10 7 8 1 1 0 1 0 0 1 9 0 1 4 0 1 9 0 1 0 0 1 1 0 1 6 7 10 6 8 1 4 0 2 3 3 2 2 0 1 5 10 2 4 8 1","9 2 3 0 1 1 0 1 3 0 1 3 0 1 3 0 1 15 0 1 3 0 1 3 0 1 3 0 1 6 8 1 4 8 1","9 2 5 10 1 15 0 1 3 0 1 1 0 1 3 0 1 17 0 1 3 0 1 3 0 1 3 0 1 6 8 1 4 0 2","9 0 5 0 1 17 0 1 3 0 1 5 10 1 3 0 1 16 0 1 1 0 1 3 0 1 3 0 1","9 1 1 0 1 16 0 1 3 0 1 5 0 1 3 0 1 3 0 1 1 0 1 1 0 1 3 0 1 4 0 1","9 0 14 0 1 1 0 1 14 0 1 14 0 1 3 0 1 3 0 1 8 0 1 1 0 1 1 0 1","9 2 7 10 1 15 0 1 1 0 1 7 10 1 14 0 1 7 8 1 9 0 1 1 0 1 1 0 1 6 8 1 4 0 3","9 1 15 0 1 17 0 1 8 3 1 15 0 1 3 0 1 7 8 1 4 0 1 14 0 1 8 3 1 6 8 1","9 1 17 0 1 16 0 1 9 0 1 17 0 1 14 0 1 4 0 1 9 0 1 3 0 1 9 0 1 4 0 2","9 0 4 0 1 4 0 1 4 0 1 3 0 1 3 0 1 4 0 1 4 0 1 1 0 1 1 0 1","9 0 4 0 1 2 0 1 9 0 1 1 0 1 8 3 1 4 0 1 9 0 1 8 0 1 8 0 1","9 0 4 0 1 15 0 1 4 0 1 14 0 1 9 0 1 1 0 1 4 0 1 9 0 1 9 0 1","9 0 9 0 1 17 0 1 9 0 1 3 0 1 3 0 1 1 0 1 4 0 1 2 0 1 3 0 1","9 0 4 0 1 16 0 1 4 0 1 8 3 1 8 3 1 9 0 1 9 0 1 8 3 1 8 0 1","9 0 9 0 1 3 0 1 4 0 1 9 0 1 9 0 1 3 0 1 10 0 1 9 0 1 9 0 1","9 1 4 0 1 2 0 1 4 0 1 3 0 1 0 0 1 9 0 1 4 0 1 3 0 1 3 0 1 6 0 9","9 1 2 0 1 7 8 3 9 0 1 8 3 1 0 0 1 1 0 1 9 0 1 8 3 1 8 0 1 6 8 2","9 1 9 0 1 0 0 1 10 0 1 9 0 1 0 0 1 9 0 1 10 0 1 9 0 1 9 0 1 6 8 1","1 9 5 0 1 6 7 2 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 3 0 4 3 3 4","7 3 4 0 1 4 0 1 1 0 1 1 0 1 5 0 1 4 0 1 1 0 1 1 0 1 1 0 1 5 10 1","9 0 4 0 1 5 0 1 5 0 1 5 0 1 4 0 1 5 0 1 5 0 1 4 0 1 4 0 1","9 0 15 0 1 4 0 1 1 0 1 15 0 1 1 0 1 1 0 1 15 0 1 4 0 1 4 0 1","9 0 17 0 1 15 0 1 1 0 1 17 0 1 15 0 1 15 0 1 17 0 1 1 0 1 4 0 1","9 0 16 0 1 17 0 1 15 0 1 16 0 1 17 0 1 17 0 1 16 0 1 1 0 1 4 0 1","9 2 3 0 1 16 0 1 17 0 1 7 8 1 16 0 1 16 0 1 7 8 1 1 0 1 4 0 1 6 8 2 4 8 1","9 1 3 0 1 3 0 1 16 0 1 5 10 1 3 0 1 2 0 1 3 0 1 1 0 1 1 0 1 6 8 1","9 2 7 8 1 7 8 1 2 0 1 3 0 1 2 0 1 7 8 1 3 0 1 1 0 1 1 0 1 6 8 3 5 10 1","9 1 4 0 1 1 0 1 2 0 1 7 10 1 7 8 1 4 0 1 3 0 1 9 0 1 9 0 1 6 8 1","9 0 4 0 1 1 0 1 7 8 1 17 0 1 3 0 1 1 0 1 3 0 1 4 0 1 1 0 1","9 0 1 0 1 1 0 1 4 0 1 4 0 1 3 0 1 1 0 1 3 0 1 8 3 1 9 0 1","9 0 9 0 1 9 0 1 4 0 1 5 10 1 3 0 1 9 0 1 1 0 1 9 0 1 1 0 1","9 0 4 0 1 1 0 1 4 0 1 1 0 1 3 0 1 4 0 1 8 3 1 2 0 1 8 0 1","9 0 9 0 1 9 0 1 1 0 1 1 0 1 1 0 1 9 0 1 9 0 1 9 0 1 9 0 1","9 0 2 0 1 3 0 1 3 0 1 7 10 1 1 0 1 4 0 1 1 0 1 3 0 1 1 0 1","9 0 9 0 1 9 0 1 3 0 1 17 0 1 1 0 1 9 0 1 8 3 1 9 0 1 8 0 1","9 0 4 0 1 3 0 1 1 0 1 3 0 1 8 3 1 3 0 1 9 0 1 3 0 1 9 0 1","9 0 9 0 1 9 0 1 1 0 1 3 0 1 9 0 1 3 0 1 1 0 1 9 0 1 3 0 1","9 0 0 0 1 3 0 1 1 0 1 4 0 1 4 0 1 3 0 1 8 0 1 1 0 1 0 0 1","9 1 0 0 1 9 0 1 9 0 1 4 0 1 9 0 1 3 0 1 9 0 1 9 0 1 0 0 1 6 8 1","9 0 0 0 1 3 0 1 0 0 1 2 0 1 0 0 1 2 0 1 1 0 1 0 0 1 0 0 1","9 0 0 0 1 9 0 1 0 0 1 17 0 1 0 0 1 16 0 1 8 0 1 0 0 1 0 0 1","9 0 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 17 0 1 9 0 1 0 0 1 0 0 1","1 8 1 0 1 6 8 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 3 0 4 3 3 1","6 5 10 0 1 5 0 5 5 0 4 3 0 1 3 0 1 3 0 1 1 0 1 1 0 1 1 0 1 1 0 1 3 3 1","10 0 2 0 1 15 0 1 15 0 1 1 0 1 1 0 1 4 0 1 3 0 1 10 0 1 3 0 1 3 0 1","10 6 7 6 6 17 0 1 17 0 1 1 0 1 1 0 1 1 0 1 3 0 1 7 6 6 3 0 1 1 0 1 6 6 12 1 0 1 4 0 3 3 3 2 5 10 1 5 11 2","11 1 5 0 4 4 0 1 5 10 1 2 0 1 4 0 1 0 0 1 1 0 1 3 0 1 3 0 1 1 0 1 4 0 1 4 0 3","11 0 1 0 1 15 0 1 3 0 1 5 11 2 1 0 1 0 0 1 1 0 1 3 0 1 1 0 1 1 0 1 4 0 1","11 1 15 0 1 17 0 1 1 0 1 3 0 1 1 0 1 0 0 1 1 0 1 3 0 1 1 0 1 1 0 1 4 0 1 4 0 3","11 0 17 0 1 16 0 1 7 10 1 3 0 1 1 0 1 0 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1","11 1 16 0 1 1 0 1 17 0 1 7 11 1 9 0 1 0 0 1 9 0 1 9 0 1 1 0 1 9 0 1 9 0 1 4 0 3","11 0 1 0 1 15 0 1 3 0 1 17 0 1 10 0 1 3 0 1 4 0 1 1 0 1 9 0 1 10 0 1 4 0 1","11 1 15 0 1 17 0 1 3 0 1 4 0 1 8 3 1 2 0 1 9 0 1 9 0 1 10 0 1 8 3 1 9 0 1 4 0 3","11 0 17 0 1 16 0 1 9 0 1 1 0 1 9 0 1 5 0 1 4 0 1 3 0 1 8 3 1 9 0 1 1 0 1","11 1 16 0 1 3 0 1 2 0 1 1 0 1 4 0 1 3 0 1 9 0 1 9 0 1 9 0 1 4 0 1 9 0 1 4 0 3","11 0 3 0 1 3 0 1 9 0 1 7 11 1 4 0 1 3 0 1 4 0 1 4 0 1 1 0 1 4 0 1 3 0 1","11 1 15 0 1 3 0 1 3 0 1 17 0 1 9 0 1 15 0 1 4 0 1 4 0 1 9 0 1 9 0 1 3 0 1 4 0 3","11 0 17 0 1 2 0 1 9 0 1 3 0 1 2 0 1 4 0 1 9 0 1 4 0 1 10 0 1 4 0 1 1 0 1","11 0 16 0 1 15 0 1 1 0 1 4 0 1 9 0 1 4 0 1 2 0 1 4 0 1 8 3 1 4 0 1 3 0 1","11 1 2 0 1 17 0 1 9 0 1 3 0 1 4 0 1 5 0 1 9 0 1 4 0 1 9 0 1 9 0 1 4 0 1 6 0 2","11 0 15 0 1 16 0 1 1 0 1 4 0 1 4 0 1 3 0 1 2 0 1 9 0 1 3 0 1 4 0 1 4 0 1","11 0 17 0 1 4 0 1 9 0 1 4 0 1 9 0 1 1 0 1 9 0 1 4 0 1 9 0 1 9 0 1 9 0 1","11 1 16 0 1 7 8 3 1 0 1 0 0 1 4 0 1 1 0 1 2 0 1 4 0 1 10 0 1 0 0 1 2 0 1 6 8 3","11 0 2 0 1 4 0 1 9 0 1 0 0 1 9 0 1 15 0 1 16 0 1 9 0 1 8 0 1 0 0 1 9 0 1","11 1 7 8 4 16 0 1 4 0 1 0 0 1 2 0 1 0 0 1 17 0 1 2 0 1 9 0 1 0 0 1 0 0 1 6 8 4","11 0 16 0 1 6 0 1 9 0 1 0 0 1 9 0 1 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1 0 0 1","1 10 4 0 1 3 0 4 3 3 4 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1","9 4 1 0 1 5 0 3 5 0 4 4 0 1 4 0 1 5 0 5 4 0 1 4 0 1 4 0 1 6 8 1 1 0 1 5 11 1 4 8 1","10 2 3 0 1 4 0 1 15 0 1 4 0 1 4 0 1 15 0 1 3 0 1 4 0 1 4 0 1 4 0 1 6 8 1 4 0 3","10 0 3 0 1 15 0 1 17 0 1 4 0 1 4 0 1 17 0 1 5 11 1 4 0 1 4 0 1 4 0 1","10 1 3 0 1 17 0 1 16 0 1 4 0 1 4 0 1 16 0 1 3 0 1 1 0 1 1 0 1 1 0 1 4 0 3","10 1 3 0 1 16 0 1 7 8 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 6 8 1","10 1 3 0 1 1 0 1 3 0 1 1 0 1 1 0 1 15 0 1 1 0 1 1 0 1 9 0 1 10 0 1 4 0 3","10 0 3 0 1 15 0 1 15 0 1 9 0 1 1 0 1 17 0 1 7 11 1 1 0 1 4 0 1 2 0 1","10 1 1 0 1 17 0 1 17 0 1 1 0 1 9 0 1 16 0 1 17 0 1 9 0 1 9 0 1 10 0 1 4 0 3","10 0 1 0 1 16 0 1 16 0 1 9 0 1 3 0 1 1 0 1 3 0 1 1 0 1 2 0 1 3 0 1","10 3 9 0 1 4 0 1 1 0 1 1 0 1 9 0 1 15 0 1 9 0 1 9 0 1 9 0 1 7 7 8 6 7 8 4 0 3 5 11 1","10 0 10 0 1 2 0 1 15 0 1 9 0 1 1 0 1 17 0 1 1 0 1 3 0 1 4 0 1 3 0 1","10 1 8 0 1 15 0 1 17 0 1 10 0 1 9 0 1 16 0 1 9 0 1 9 0 1 9 0 1 3 0 1 4 0 3","10 0 9 0 1 17 0 1 16 0 1 8 0 1 3 0 1 3 0 1 3 0 1 3 0 1 0 0 1 3 0 1","10 1 1 0 1 16 0 1 3 0 1 9 0 1 2 0 1 15 0 1 9 0 1 9 0 1 0 0 1 3 0 1 4 0 3","10 0 9 0 1 3 0 1 2 0 1 1 0 1 9 0 1 17 0 1 2 0 1 3 0 1 0 0 1 9 0 1","10 0 10 0 1 3 0 1 15 0 1 9 0 1 1 0 1 16 0 1 9 0 1 9 0 1 0 0 1 4 0 1","10 1 8 0 1 7 8 3 17 0 1 10 0 1 9 0 1 2 0 1 2 0 1 3 0 1 0 0 1 1 0 1 6 8 3","10 0 9 0 1 3 0 1 16 0 1 8 0 1 3 0 1 15 0 1 9 0 1 9 0 1 0 0 1 9 0 1","10 0 2 0 1 5 0 1 4 0 1 9 0 1 9 0 1 17 0 1 3 0 1 3 0 1 0 0 1 0 0 1","10 0 2 0 1 3 0 1 4 0 1 0 0 1 3 0 1 16 0 1 9 0 1 9 0 1 0 0 1 0 0 1","10 2 2 0 1 1 0 1 7 8 3 0 0 1 9 0 1 2 0 1 1 0 1 3 0 1 0 0 1 0 0 1 6 8 3 6 0 2","10 1 2 0 1 1 0 1 0 0 1 0 0 1 3 0 1 7 8 5 9 0 1 9 0 1 0 0 1 0 0 1 6 8 5","10 0 9 0 1 15 0 1 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1","1 10 1 0 1 3 0 4 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1","10 4 4 0 1 4 0 1 4 0 1 4 0 1 4 0 1 1 0 1 4 0 1 4 0 1 1 0 1 4 0 1 1 0 1 1 0 1 5 11 2 4 8 3","12 2 4 0 1 4 0 1 1 0 1 4 0 1 4 0 1 1 0 1 4 0 1 4 0 1 5 0 5 4 0 1 4 0 1 4 0 1 6 8 3 4 0 5","12 0 4 0 1 4 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 15 0 1 4 0 1 1 0 1 4 0 1","12 1 9 0 1 4 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 17 0 1 9 0 1 5 0 5 1 0 1 4 0 1","12 0 10 0 1 9 0 1 9 0 1 1 0 1 1 0 1 9 0 1 9 0 1 9 0 1 16 0 1 10 0 1 15 0 1 1 0 1","12 0 3 0 1 10 0 1 10 0 1 9 0 1 1 0 1 10 0 1 10 0 1 10 0 1 1 0 1 3 0 1 17 0 1 1 0 1","12 0 3 0 1 3 0 1 2 0 1 10 0 1 1 0 1 2 0 1 3 0 1 3 0 1 15 0 1 3 0 1 16 0 1 9 0 1","12 0 3 0 1 3 0 1 2 0 1 3 0 1 9 0 1 2 0 1 2 0 1 3 0 1 17 0 1 3 0 1 1 0 1 10 0 1","12 3 2 0 1 3 0 1 2 0 1 3 0 1 10 0 1 2 0 1 2 0 1 2 0 1 16 0 1 7 4 6 15 0 1 3 0 1 6 4 6 4 0 14 4 8 5","12 2 7 4 6 3 0 1 7 4 6 2 0 1 3 0 1 2 0 1 7 4 6 7 4 6 3 0 1 5 0 3 17 0 1 2 0 1 6 4 24 4 0 5","12 1 1 0 1 7 4 6 1 0 1 2 0 1 2 0 1 7 4 6 4 0 1 4 0 1 15 0 1 4 0 1 16 0 1 2 0 1 6 4 12","12 2 1 0 1 5 11 1 1 0 1 7 4 6 2 0 1 4 0 1 4 0 1 4 0 1 17 0 1 15 0 1 1 0 1 2 0 1 6 4 6 4 0 5","12 1 10 0 1 5 0 1 1 0 1 5 11 1 2 0 1 1 0 1 1 0 1 1 0 1 16 0 1 17 0 1 15 0 1 7 4 6 6 4 6","12 1 2 0 1 4 0 1 1 0 1 5 0 1 2 0 1 1 0 1 14 0 1 1 0 1 2 0 1 16 0 1 17 0 1 5 11 1 4 0 5","12 1 10 0 1 4 0 1 13 0 1 4 0 1 7 4 6 1 0 1 4 0 1 8 0 1 15 0 1 1 0 1 16 0 1 5 0 1 6 4 6","12 1 2 0 1 4 0 1 3 0 1 1 0 1 0 0 1 8 0 1 8 0 1 9 0 1 17 0 1 15 0 1 3 0 1 1 0 1 4 0 5","12 0 10 0 1 14 0 1 3 0 1 1 0 1 0 0 1 9 0 1 9 0 1 1 0 1 16 0 1 17 0 1 15 0 1 1 0 1","12 2 7 6 12 7 11 1 3 0 1 14 0 1 0 0 1 1 0 1 1 0 1 9 0 1 3 0 1 16 0 1 17 0 1 1 0 1 6 6 12 6 8 5","12 0 0 0 1 15 0 1 3 0 1 7 11 1 0 0 1 8 0 1 9 0 1 10 0 1 15 0 1 4 0 1 16 0 1 14 0 1","12 0 0 0 1 17 0 1 9 0 1 15 0 1 0 0 1 9 0 1 10 0 1 8 0 1 17 0 1 2 0 1 3 0 1 7 11 1","12 1 0 0 1 4 0 1 0 0 1 17 0 1 0 0 1 0 0 1 8 0 1 9 0 1 16 0 1 15 0 1 15 0 1 15 0 1 6 0 3","12 0 0 0 1 8 0 1 0 0 1 0 0 1 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1 17 0 1 17 0 1 17 0 1","12 0 0 0 1 9 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 16 0 1 16 0 1 0 0 1","1 10 4 0 1 6 4 12 6 8 13 3 0 11 3 1 1 3 3 9 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1","6 9 4 0 1 3 0 1 5 0 3 4 0 1 4 0 1 5 0 5 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 2 0 1 5 11 1 4 8 1","12 2 10 0 1 3 0 1 3 0 1 8 3 1 8 3 1 4 0 1 4 0 1 5 0 5 2 0 1 4 0 1 5 11 1 3 0 1 6 8 1 4 0 3","12 0 3 0 1 3 0 1 1 0 1 9 0 1 9 0 1 15 0 1 2 0 1 15 0 1 8 3 1 4 0 1 4 0 1 3 0 1","12 1 3 0 1 1 0 1 15 0 1 4 0 1 4 0 1 17 0 1 2 0 1 17 0 1 9 0 1 4 0 1 4 0 1 3 0 1 4 0 3","12 1 7 6 6 1 0 1 17 0 1 8 3 1 2 0 1 16 0 1 8 3 1 16 0 1 4 0 1 1 0 1 1 0 1 9 0 1 6 6 6","12 1 4 0 1 9 0 1 16 0 1 9 0 1 8 3 1 1 0 1 9 0 1 1 0 1 2 0 1 1 0 1 7 11 1 3 0 1 4 0 3","12 0 4 0 1 1 0 1 1 0 1 4 0 1 9 0 1 15 0 1 2 0 1 15 0 1 8 3 1 1 0 1 17 0 1 9 0 1","12 1 4 0 1 1 0 1 15 0 1 8 3 1 4 0 1 17 0 1 8 3 1 17 0 1 9 0 1 9 0 1 4 0 1 1 0 1 4 0 3","12 0 4 0 1 9 0 1 17 0 1 9 0 1 8 3 1 16 0 1 9 0 1 16 0 1 4 0 1 3 0 1 4 0 1 9 0 1","12 1 9 0 1 4 0 1 16 0 1 2 0 1 9 0 1 4 0 1 2 0 1 1 0 1 8 3 1 3 0 1 9 0 1 1 0 1 4 0 3","12 0 1 0 1 9 0 1 3 0 1 8 3 1 2 0 1 2 0 1 8 0 1 15 0 1 9 0 1 3 0 1 1 0 1 9 0 1","12 1 1 0 1 4 0 1 2 0 1 9 0 1 2 0 1 15 0 1 9 0 1 17 0 1 4 0 1 16 0 1 9 0 1 1 0 1 4 0 3","12 0 1 0 1 9 0 1 2 0 1 4 0 1 8 0 1 17 0 1 4 0 1 16 0 1 8 0 1 17 0 1 1 0 1 9 0 1","12 1 1 0 1 2 0 1 15 0 1 8 0 1 9 0 1 16 0 1 8 0 1 1 0 1 9 0 1 2 0 1 9 0 1 1 0 1 4 0 3","12 0 9 0 1 9 0 1 17 0 1 9 0 1 3 0 1 4 0 1 9 0 1 15 0 1 4 0 1 16 0 1 3 0 1 9 0 1","12 0 10 0 1 3 0 1 16 0 1 1 0 1 8 3 1 15 0 1 4 0 1 17 0 1 8 0 1 17 0 1 9 0 1 10 0 1","12 0 3 0 1 9 0 1 1 0 1 8 0 1 9 0 1 17 0 1 8 0 1 16 0 1 9 0 1 2 0 1 1 0 1 4 0 1","12 0 3 0 1 3 0 1 9 0 1 9 0 1 0 0 1 16 0 1 9 0 1 4 0 1 2 0 1 16 0 1 9 0 1 9 0 1","12 0 2 0 1 9 0 1 3 0 1 3 0 1 0 0 1 3 0 1 4 0 1 2 0 1 8 0 1 17 0 1 3 0 1 10 0 1","12 0 9 0 1 3 0 1 9 0 1 1 0 1 0 0 1 1 0 1 8 0 1 15 0 1 9 0 1 3 0 1 9 0 1 0 0 1","12 1 3 0 1 9 0 1 1 0 1 1 0 1 0 0 1 15 0 1 9 0 1 17 0 1 3 0 1 16 0 1 3 0 1 0 0 1 6 0 9","12 0 1 0 1 0 0 1 9 0 1 1 0 1 0 0 1 4 0 1 0 0 1 16 0 1 8 0 1 17 0 1 2 0 1 0 0 1","12 0 9 0 1 0 0 1 0 0 1 9 0 1 0 0 1 9 0 1 0 0 1 0 0 1 9 0 1 0 0 1 9 0 1 0 0 1","1 10 1 0 1 3 0 9 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1","10 1 4 0 1 5 0 5 5 0 5 4 0 1 4 0 1 5 0 5 3 0 1 4 0 1 4 0 1 2 0 1 6 8 14","10 0 10 0 1 4 0 1 15 0 1 1 0 1 4 0 1 15 0 1 3 0 1 4 0 1 4 0 1 9 0 1","10 0 3 0 1 15 0 1 17 0 1 10 0 1 4 0 1 17 0 1 3 0 1 4 0 1 4 0 1 4 0 1","10 0 2 0 1 17 0 1 16 0 1 3 0 1 4 0 1 16 0 1 3 0 1 4 0 1 4 0 1 2 0 1","10 1 7 7 4 16 0 1 1 0 1 7 7 4 4 0 1 1 0 1 1 0 1 1 0 1 4 0 1 9 0 1 6 7 8","10 0 1 0 1 1 0 1 15 0 1 3 0 1 1 0 1 15 0 1 1 0 1 1 0 1 2 0 1 3 0 1","10 0 10 0 1 15 0 1 17 0 1 5 0 2 1 0 1 17 0 1 1 0 1 1 0 1 2 0 1 9 0 1","10 0 2 0 1 17 0 1 16 0 1 3 0 1 1 0 1 16 0 1 9 0 1 1 0 1 2 0 1 2 0 1","10 0 10 0 1 16 0 1 1 0 1 15 0 1 1 0 1 1 0 1 10 0 1 1 0 1 2 0 1 9 0 1","10 1 7 6 6 4 0 1 15 0 1 17 0 1 9 0 1 15 0 1 8 0 1 8 0 1 8 0 1 2 0 1 6 6 6","10 0 4 0 1 15 0 1 17 0 1 16 0 1 10 0 1 17 0 1 9 0 1 9 0 1 9 0 1 2 0 1","10 1 2 0 1 17 0 1 16 0 1 3 0 1 8 0 1 16 0 1 1 0 1 3 0 1 1 0 1 9 0 1 6 8 2","10 0 9 0 1 16 0 1 3 0 1 15 0 1 9 0 1 1 0 1 8 0 1 3 0 1 9 0 1 4 0 1","10 0 4 0 1 2 0 1 15 0 1 17 0 1 3 0 1 15 0 1 9 0 1 3 0 1 1 0 1 9 0 1","10 0 9 0 1 15 0 1 17 0 1 16 0 1 3 0 1 17 0 1 4 0 1 9 0 1 9 0 1 4 0 1","10 0 4 0 1 17 0 1 16 0 1 0 0 1 9 0 1 16 0 1 8 0 1 10 0 1 1 0 1 9 0 1","10 0 4 0 1 16 0 1 2 0 1 0 0 1 10 0 1 4 0 1 9 0 1 8 0 1 9 0 1 4 0 1","10 0 9 0 1 4 0 1 15 0 1 0 0 1 8 0 1 2 0 1 0 0 1 9 0 1 3 0 1 9 0 1","10 0 1 0 1 15 0 1 17 0 1 0 0 1 9 0 1 15 0 1 0 0 1 2 0 1 2 0 1 1 0 1","10 0 9 0 1 17 0 1 16 0 1 0 0 1 2 0 1 17 0 1 0 0 1 9 0 1 9 0 1 9 0 1","10 1 0 0 1 16 0 1 0 0 1 0 0 1 9 0 1 16 0 1 0 0 1 0 0 1 0 0 1 3 0 1 6 0 9","10 0 0 0 1 1 0 1 0 0 1 0 0 1 4 0 1 0 0 1 0 0 1 0 0 1 0 0 1 9 0 1","10 0 0 0 1 9 0 1 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1","1 10 5 0 5 6 8 17 3 0 9 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1","9 2 4 0 1 5 0 5 4 0 1 4 0 1 5 0 5 4 0 1 4 0 1 4 0 1 5 0 5 1 0 1 1 0 1","11 0 4 0 1 15 0 1 4 0 1 2 0 1 4 0 1 4 0 1 4 0 1 4 0 1 15 0 1 3 0 1 1 0 1","11 0 10 0 1 17 0 1 4 0 1 2 0 1 15 0 1 1 0 1 2 0 1 4 0 1 17 0 1 3 0 1 1 0 1","11 0 3 0 1 16 0 1 9 0 1 2 0 1 17 0 1 1 0 1 9 0 1 4 0 1 16 0 1 3 0 1 1 0 1","11 0 3 0 1 1 0 1 2 0 1 9 0 1 16 0 1 1 0 1 2 0 1 1 0 1 1 0 1 1 0 1 9 0 1","11 0 1 0 1 15 0 1 9 0 1 4 0 1 1 0 1 9 0 1 9 0 1 1 0 1 15 0 1 9 0 1 1 0 1","11 0 1 0 1 17 0 1 4 0 1 9 0 1 15 0 1 10 0 1 3 0 1 9 0 1 17 0 1 3 0 1 9 0 1","11 0 10 0 1 16 0 1 1 0 1 4 0 1 17 0 1 8 0 1 9 0 1 10 0 1 16 0 1 9 0 1 3 0 1","11 0 2 0 1 1 0 1 1 0 1 4 0 1 16 0 1 9 0 1 4 0 1 8 0 1 1 0 1 1 0 1 9 0 1","11 0 2 0 1 15 0 1 9 0 1 4 0 1 4 0 1 4 0 1 2 0 1 9 0 1 15 0 1 9 0 1 3 0 1","11 1 7 6 6 17 0 1 10 0 1 9 0 1 15 0 1 2 0 1 9 0 1 3 0 1 17 0 1 1 0 1 9 0 1 6 6 6","11 0 3 0 1 16 0 1 8 0 1 10 0 1 17 0 1 9 0 1 4 0 1 1 0 1 16 0 1 9 0 1 2 0 1","11 0 3 0 1 3 0 1 9 0 1 8 0 1 16 0 1 10 0 1 9 0 1 1 0 1 1 0 1 0 0 1 9 0 1","11 0 15 0 1 15 0 1 1 0 1 9 0 1 2 0 1 8 0 1 2 0 1 9 0 1 15 0 1 0 0 1 2 0 1","11 0 17 0 1 17 0 1 9 0 1 3 0 1 15 0 1 9 0 1 9 0 1 3 0 1 17 0 1 0 0 1 9 0 1","11 0 16 0 1 16 0 1 1 0 1 1 0 1 17 0 1 4 0 1 3 0 1 1 0 1 16 0 1 0 0 1 2 0 1","11 0 3 0 1 2 0 1 9 0 1 9 0 1 16 0 1 9 0 1 9 0 1 9 0 1 4 0 1 0 0 1 9 0 1","11 0 15 0 1 15 0 1 3 0 1 4 0 1 4 0 1 10 0 1 3 0 1 0 0 1 2 0 1 0 0 1 3 0 1","11 0 17 0 1 17 0 1 1 0 1 9 0 1 15 0 1 8 0 1 9 0 1 0 0 1 15 0 1 0 0 1 9 0 1","11 0 16 0 1 16 0 1 9 0 1 1 0 1 17 0 1 9 0 1 3 0 1 0 0 1 17 0 1 0 0 1 1 0 1","11 1 0 0 1 1 0 1 3 0 1 9 0 1 16 0 1 1 0 1 9 0 1 0 0 1 16 0 1 0 0 1 9 0 1 6 0 9","11 0 0 0 1 1 0 1 1 0 1 1 0 1 0 0 1 1 0 1 0 0 1 0 0 1 0 0 1 0 0 1 1 0 1","11 0 0 0 1 9 0 1 9 0 1 9 0 1 0 0 1 9 0 1 0 0 1 0 0 1 0 0 1 0 0 1 9 0 1","1 10 5 8 4 3 0 9 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1","10 3 1 0 1 10 0 1 4 0 1 3 0 1 5 0 5 3 0 1 1 0 1 4 0 1 5 0 5 1 0 1 6 8 9 1 0 1 4 8 2","11 2 4 0 1 7 6 6 9 0 1 1 0 1 15 0 1 3 0 1 1 0 1 9 0 1 10 0 1 10 0 1 1 0 1 6 6 6 6 8 1","11 1 4 0 1 5 0 5 2 0 1 1 0 1 17 0 1 10 0 1 10 0 1 2 0 1 7 6 3 2 0 1 5 0 2 6 6 3","11 1 4 0 1 15 0 1 9 0 1 10 0 1 16 0 1 4 0 1 2 0 1 9 0 1 4 0 1 7 6 6 3 0 1 6 6 6","11 1 4 0 1 17 0 1 4 0 1 4 0 1 1 0 1 4 0 1 7 6 3 2 0 1 15 0 1 4 0 1 15 0 1 6 6 3","11 1 11 0 1 16 0 1 4 0 1 2 0 1 15 0 1 7 7 6 4 0 1 9 0 1 17 0 1 4 0 1 17 0 1 6 7 6","11 1 9 0 1 1 0 1 2 0 1 7 7 6 17 0 1 4 0 1 4 0 1 4 0 1 16 0 1 4 0 1 16 0 1 6 7 6","11 0 1 0 1 15 0 1 9 0 1 4 0 1 16 0 1 4 0 1 2 0 1 4 0 1 1 0 1 2 0 1 3 0 1","11 0 11 0 1 17 0 1 10 0 1 2 0 1 1 0 1 4 0 1 2 0 1 2 0 1 15 0 1 9 0 1 15 0 1","11 0 9 0 1 16 0 1 8 0 1 2 0 1 15 0 1 4 0 1 9 0 1 9 0 1 17 0 1 4 0 1 17 0 1","11 0 3 0 1 1 0 1 9 0 1 2 0 1 17 0 1 1 0 1 2 0 1 10 0 1 16 0 1 4 0 1 16 0 1","11 0 1 0 1 15 0 1 2 0 1 2 0 1 16 0 1 9 0 1 9 0 1 8 0 1 4 0 1 2 0 1 3 0 1","11 0 11 0 1 17 0 1 9 0 1 9 0 1 10 0 1 1 0 1 4 0 1 9 0 1 15 0 1 9 0 1 1 0 1","11 0 9 0 1 16 0 1 10 0 1 4 0 1 1 0 1 9 0 1 1 0 1 2 0 1 17 0 1 10 0 1 1 0 1","11 0 3 0 1 3 0 1 8 0 1 9 0 1 15 0 1 3 0 1 9 0 1 9 0 1 16 0 1 8 0 1 1 0 1","11 0 1 0 1 15 0 1 9 0 1 1 0 1 17 0 1 9 0 1 1 0 1 10 0 1 2 0 1 9 0 1 1 0 1","11 0 11 0 1 17 0 1 2 0 1 9 0 1 16 0 1 1 0 1 9 0 1 8 0 1 15 0 1 2 0 1 9 0 1","11 0 9 0 1 16 0 1 9 0 1 0 0 1 4 0 1 9 0 1 4 0 1 9 0 1 17 0 1 9 0 1 3 0 1","11 0 4 0 1 2 0 1 10 0 1 0 0 1 2 0 1 3 0 1 9 0 1 3 0 1 16 0 1 10 0 1 9 0 1","11 0 4 0 1 15 0 1 8 0 1 0 0 1 15 0 1 9 0 1 1 0 1 9 0 1 4 0 1 8 0 1 2 0 1","11 1 9 0 1 17 0 1 9 0 1 0 0 1 17 0 1 1 0 1 9 0 1 3 0 1 15 0 1 9 0 1 9 0 1 6 0 9","11 0 2 0 1 16 0 1 4 0 1 0 0 1 16 0 1 9 0 1 0 0 1 9 0 1 17 0 1 2 0 1 0 0 1","11 0 9 0 1 0 0 1 9 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 16 0 1 9 0 1 0 0 1","1 10 3 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 3 0 11","10 4 5 8 5 5 0 5 4 0 1 1 0 1 5 0 5 10 0 1 4 0 1 1 0 1 4 0 1 5 0 2 6 7 1 1 0 1 1 0 1 4 8 2","12 1 1 0 1 4 0 1 1 0 1 5 8 3 3 0 1 4 0 1 4 0 1 3 0 1 10 0 1 1 0 1 2 0 1 1 0 1 6 8 6","12 0 1 0 1 15 0 1 1 0 1 3 0 1 15 0 1 5 0 5 4 0 1 1 0 1 3 0 1 10 0 1 2 0 1 1 0 1","12 2 1 0 1 17 0 1 10 0 1 3 0 1 17 0 1 15 0 1 1 0 1 1 0 1 7 7 4 2 0 1 2 0 1 1 0 1 6 7 3 6 8 1","12 1 11 0 1 16 0 1 3 0 1 1 0 1 16 0 1 17 0 1 1 0 1 10 0 1 1 0 1 7 7 2 2 0 1 1 0 1 6 7 2","12 1 9 0 1 1 0 1 2 0 1 11 0 1 1 0 1 16 0 1 1 0 1 4 0 1 1 0 1 7 7 2 9 0 1 1 0 1 6 7 2","12 1 3 0 1 15 0 1 7 7 4 9 0 1 15 0 1 1 0 1 9 0 1 2 0 1 1 0 1 3 0 1 10 0 1 9 0 1 6 7 4","12 0 11 0 1 17 0 1 4 0 1 3 0 1 17 0 1 15 0 1 1 0 1 2 0 1 1 0 1 15 0 1 8 0 1 3 0 1","12 1 9 0 1 16 0 1 4 0 1 2 0 1 16 0 1 17 0 1 1 0 1 7 7 6 12 0 1 17 0 1 9 0 1 9 0 1 6 7 6","12 1 3 0 1 4 0 1 4 0 1 11 0 1 1 0 1 16 0 1 9 0 1 4 0 1 8 0 1 16 0 1 4 0 1 3 0 1 6 8 5","12 0 2 0 1 15 0 1 4 0 1 9 0 1 15 0 1 1 0 1 4 0 1 3 0 1 9 0 1 10 0 1 9 0 1 9 0 1","12 0 11 0 1 17 0 1 2 0 1 3 0 1 17 0 1 15 0 1 9 0 1 3 0 1 4 0 1 3 0 1 10 0 1 3 0 1","12 0 9 0 1 16 0 1 9 0 1 11 0 1 16 0 1 17 0 1 10 0 1 3 0 1 2 0 1 15 0 1 8 0 1 9 0 1","12 0 3 0 1 2 0 1 10 0 1 9 0 1 10 0 1 16 0 1 8 0 1 1 0 1 9 0 1 17 0 1 9 0 1 10 0 1","12 1 11 0 1 15 0 1 8 0 1 1 0 1 3 0 1 1 0 1 9 0 1 1 0 1 1 0 1 16 0 1 4 0 1 8 0 1 6 0 7","12 0 9 0 1 17 0 1 9 0 1 9 0 1 15 0 1 15 0 1 3 0 1 1 0 1 9 0 1 4 0 1 4 0 1 9 0 1","12 0 2 0 1 16 0 1 1 0 1 1 0 1 17 0 1 17 0 1 2 0 1 9 0 1 4 0 1 4 0 1 4 0 1 3 0 1","12 0 11 0 1 10 0 1 9 0 1 9 0 1 16 0 1 16 0 1 10 0 1 3 0 1 10 0 1 6 0 1 9 0 1 9 0 1","12 0 9 0 1 4 0 1 1 0 1 4 0 1 2 0 1 4 0 1 4 0 1 9 0 1 2 0 1 4 0 1 10 0 1 10 0 1","12 0 4 0 1 15 0 1 10 0 1 1 0 1 15 0 1 2 0 1 9 0 1 3 0 1 9 0 1 4 0 1 8 0 1 8 0 1","12 1 4 0 1 17 0 1 3 0 1 9 0 1 17 0 1 15 0 1 2 0 1 1 0 1 2 0 1 1 0 1 9 0 1 9 0 1 6 6 7","12 1 0 0 1 16 0 1 9 0 1 4 0 1 16 0 1 17 0 1 10 0 1 2 0 1 9 0 1 1 0 1 1 0 1 2 0 1 6 6 5","12 0 0 0 1 0 0 1 0 0 1 9 0 1 0 0 1 16 0 1 0 0 1 9 0 1 0 0 1 0 0 1 9 0 1 9 0 1","1 10 3 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 3 0 8","10 4 3 0 1 4 0 1 1 0 1 1 0 1 5 0 5 1 0 1 4 0 1 1 0 1 5 0 5 5 8 3 6 3 8 1 0 1 1 0 1 4 8 2","12 1 3 0 1 4 0 1 5 8 1 5 0 5 15 0 1 1 0 1 2 0 1 5 0 2 4 0 1 3 0 1 9 0 1 4 0 1 6 8 10","12 0 1 0 1 1 0 1 4 0 1 15 0 1 16 0 1 1 0 1 9 0 1 3 0 1 15 0 1 3 0 1 2 0 1 4 0 1","12 0 10 0 1 1 0 1 4 0 1 17 0 1 10 0 1 10 0 1 4 0 1 15 0 1 17 0 1 3 0 1 9 0 1 9 0 1","12 1 1 0 1 1 0 1 4 0 1 16 0 1 1 0 1 3 0 1 9 0 1 16 0 1 16 0 1 3 0 1 2 0 1 4 0 1 6 7 4","12 0 10 0 1 9 0 1 1 0 1 1 0 1 15 0 1 10 0 1 4 0 1 3 0 1 1 0 1 1 0 1 9 0 1 9 0 1","12 0 3 0 1 10 0 1 1 0 1 15 0 1 17 0 1 4 0 1 9 0 1 15 0 1 15 0 1 11 0 1 4 0 1 4 0 1","12 0 10 0 1 8 0 1 1 0 1 17 0 1 16 0 1 2 0 1 4 0 1 17 0 1 17 0 1 9 0 1 9 0 1 9 0 1","12 1 2 0 1 9 0 1 1 0 1 16 0 1 1 0 1 2 0 1 9 0 1 16 0 1 16 0 1 1 0 1 4 0 1 1 0 1 6 6 8","12 1 10 0 1 4 0 1 11 0 1 1 0 1 15 0 1 2 0 1 2 0 1 4 0 1 4 0 1 11 0 1 4 0 1 10 0 1 6 8 5","12 1 2 0 1 9 0 1 9 0 1 15 0 1 17 0 1 7 3 4 9 0 1 4 0 1 15 0 1 9 0 1 9 0 1 3 0 1 6 3 4","12 0 10 0 1 2 0 1 3 0 1 17 0 1 16 0 1 4 0 1 2 0 1 4 0 1 17 0 1 4 0 1 3 0 1 3 0 1","12 1 3 0 1 9 0 1 9 0 1 16 0 1 1 0 1 4 0 1 9 0 1 1 0 1 16 0 1 1 0 1 9 0 1 1 0 1 6 6 7","12 1 10 0 1 10 0 1 3 0 1 3 0 1 15 0 1 4 0 1 10 0 1 10 0 1 2 0 1 11 0 1 2 0 1 1 0 1 6 0 2","12 0 4 0 1 8 0 1 9 0 1 15 0 1 17 0 1 4 0 1 8 0 1 1 0 1 15 0 1 9 0 1 9 0 1 10 0 1","12 1 4 0 1 9 0 1 10 0 1 17 0 1 16 0 1 4 0 1 9 0 1 1 0 1 17 0 1 3 0 1 3 0 1 3 0 1 6 0 3","12 0 4 0 1 4 0 1 8 0 1 16 0 1 4 0 1 1 0 1 3 0 1 1 0 1 16 0 1 9 0 1 9 0 1 1 0 1","12 0 4 0 1 9 0 1 9 0 1 2 0 1 2 0 1 1 0 1 9 0 1 9 0 1 4 0 1 10 0 1 3 0 1 10 0 1","12 1 7 3 12 2 0 1 2 0 1 15 0 1 15 0 1 1 0 1 2 0 1 4 0 1 15 0 1 8 0 1 9 0 1 2 0 1 6 3 12","12 0 4 0 1 9 0 1 9 0 1 17 0 1 17 0 1 9 0 1 9 0 1 4 0 1 17 0 1 9 0 1 2 0 1 2 0 1","12 0 1 0 1 2 0 1 10 0 1 16 0 1 16 0 1 10 0 1 3 0 1 4 0 1 16 0 1 4 0 1 9 0 1 2 0 1","12 1 1 0 1 9 0 1 8 0 1 2 0 1 4 0 1 8 0 1 9 0 1 4 0 1 1 0 1 1 0 1 4 0 1 7 7 14 6 7 14","12 2 10 0 1 2 0 1 9 0 1 17 0 1 9 0 1 9 0 1 0 0 1 9 0 1 9 0 1 9 0 1 9 0 1 17 0 1 6 6 3 6 8 2","1 10 4 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 3 0 9","10 4 4 0 1 5 0 5 3 0 1 4 0 1 1 0 1 3 0 1 5 8 4 4 0 1 4 0 1 5 0 5 6 7 4 6 8 5 1 0 1 1 0 1","12 0 4 0 1 4 0 1 1 0 1 4 0 1 5 0 2 3 0 1 1 0 1 4 0 1 1 0 1 3 0 1 4 0 1 4 0 1","12 0 4 0 1 15 0 1 1 0 1 4 0 1 3 0 1 1 0 1 1 0 1 4 0 1 5 0 5 15 0 1 4 0 1 4 0 1","12 1 1 0 1 17 0 1 1 0 1 4 0 1 15 0 1 10 0 1 1 0 1 4 0 1 15 0 1 17 0 1 4 0 1 2 0 1 6 8 2","12 1 10 0 1 16 0 1 9 0 1 1 0 1 17 0 1 3 0 1 9 0 1 9 0 1 17 0 1 16 0 1 4 0 1 2 0 1 6 8 1","12 1 1 0 1 1 0 1 3 0 1 9 0 1 16 0 1 2 0 1 1 0 1 2 0 1 16 0 1 1 0 1 1 0 1 2 0 1 6 0 7","12 0 10 0 1 15 0 1 3 0 1 10 0 1 10 0 1 10 0 1 11 0 1 2 0 1 1 0 1 15 0 1 1 0 1 2 0 1","12 0 3 0 1 17 0 1 10 0 1 8 0 1 3 0 1 4 0 1 9 0 1 9 0 1 15 0 1 17 0 1 9 0 1 9 0 1","12 1 1 0 1 16 0 1 3 0 1 9 0 1 15 0 1 4 0 1 3 0 1 10 0 1 17 0 1 16 0 1 10 0 1 10 0 1 6 6 4","12 2 10 0 1 4 0 1 2 0 1 2 0 1 17 0 1 7 7 6 11 0 1 8 0 1 16 0 1 1 0 1 8 0 1 8 0 1 6 7 6 6 8 3","12 0 1 0 1 15 0 1 10 0 1 2 0 1 16 0 1 4 0 1 9 0 1 9 0 1 1 0 1 15 0 1 9 0 1 9 0 1","12 0 10 0 1 17 0 1 2 0 1 9 0 1 1 0 1 1 0 1 3 0 1 2 0 1 15 0 1 17 0 1 3 0 1 4 0 1","12 1 3 0 1 16 0 1 10 0 1 3 0 1 9 0 1 1 0 1 11 0 1 2 0 1 17 0 1 16 0 1 1 0 1 9 0 1 6 6 2","12 1 10 0 1 2 0 1 4 0 1 2 0 1 1 0 1 1 0 1 9 0 1 9 0 1 16 0 1 10 0 1 9 0 1 10 0 1 6 6 3","12 0 3 0 1 15 0 1 4 0 1 9 0 1 9 0 1 1 0 1 2 0 1 3 0 1 1 0 1 3 0 1 10 0 1 8 0 1","12 0 3 0 1 17 0 1 4 0 1 3 0 1 3 0 1 9 0 1 11 0 1 3 0 1 15 0 1 15 0 1 8 0 1 9 0 1","12 0 2 0 1 16 0 1 4 0 1 2 0 1 9 0 1 4 0 1 9 0 1 3 0 1 17 0 1 17 0 1 9 0 1 1 0 1","12 0 2 0 1 10 0 1 2 0 1 9 0 1 2 0 1 4 0 1 3 0 1 3 0 1 16 0 1 16 0 1 2 0 1 9 0 1","12 1 2 0 1 4 0 1 7 3 6 3 0 1 9 0 1 4 0 1 3 0 1 1 0 1 4 0 1 2 0 1 10 0 1 10 0 1 6 3 6","12 0 2 0 1 15 0 1 3 0 1 2 0 1 2 0 1 4 0 1 1 0 1 1 0 1 2 0 1 15 0 1 3 0 1 8 0 1","12 1 7 3 10 17 0 1 1 0 1 9 0 1 9 0 1 9 0 1 9 0 1 1 0 1 15 0 1 17 0 1 3 0 1 9 0 1 6 3 10","12 0 2 0 1 16 0 1 0 0 1 3 0 1 3 0 1 0 0 1 4 0 1 1 0 1 17 0 1 16 0 1 2 0 1 0 0 1","12 1 9 0 1 0 0 1 0 0 1 9 0 1 9 0 1 0 0 1 9 0 1 6 0 1 16 0 1 0 0 1 6 0 1 0 0 1 6 6 3","1 10 5 0 5 3 0 9 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1","10 6 15 0 1 1 0 1 4 0 1 4 0 1 5 8 4 5 0 2 1 0 1 4 0 1 10 0 1 5 0 5 6 6 6 6 7 4 1 0 1 1 0 1 1 0 1 4 8 4","13 0 4 0 1 1 0 1 9 0 1 2 0 1 4 0 1 3 0 1 5 0 4 4 0 1 5 0 5 15 0 1 4 0 1 4 0 1 10 0 1","13 0 1 0 1 1 0 1 2 0 1 9 0 1 4 0 1 3 0 1 4 0 1 4 0 1 1 0 1 17 0 1 2 0 1 9 0 1 7 6 3","13 0 10 0 1 1 0 1 9 0 1 4 0 1 4 0 1 1 0 1 15 0 1 9 0 1 15 0 1 16 0 1 2 0 1 5 8 1 3 0 1","13 0 2 0 1 10 0 1 2 0 1 4 0 1 4 0 1 10 0 1 17 0 1 4 0 1 17 0 1 1 0 1 9 0 1 4 0 1 3 0 1","13 1 10 0 1 2 0 1 9 0 1 9 0 1 1 0 1 3 0 1 16 0 1 9 0 1 16 0 1 15 0 1 2 0 1 11 0 1 3 0 1 6 6 3","13 0 3 0 1 10 0 1 4 0 1 2 0 1 11 0 1 1 0 1 4 0 1 1 0 1 4 0 1 17 0 1 9 0 1 3 0 1 3 0 1","13 1 7 7 6 3 0 1 9 0 1 2 0 1 9 0 1 10 0 1 4 0 1 1 0 1 15 0 1 16 0 1 4 0 1 5 8 2 1 0 1 6 7 6","13 0 3 0 1 10 0 1 4 0 1 9 0 1 1 0 1 2 0 1 15 0 1 1 0 1 17 0 1 10 0 1 9 0 1 11 0 1 9 0 1","13 0 3 0 1 1 0 1 9 0 1 10 0 1 11 0 1 10 0 1 17 0 1 9 0 1 16 0 1 1 0 1 2 0 1 2 0 1 1 0 1","13 0 3 0 1 10 0 1 10 0 1 8 0 1 9 0 1 2 0 1 16 0 1 3 0 1 1 0 1 15 0 1 9 0 1 11 0 1 9 0 1","13 0 15 0 1 3 0 1 8 0 1 9 0 1 3 0 1 10 0 1 3 0 1 1 0 1 15 0 1 16 0 1 10 0 1 1 0 1 1 0 1","13 0 17 0 1 10 0 1 9 0 1 3 0 1 1 0 1 3 0 1 3 0 1 9 0 1 17 0 1 4 0 1 8 0 1 5 8 2 9 0 1","13 1 16 0 1 2 0 1 1 0 1 3 0 1 11 0 1 10 0 1 3 0 1 4 0 1 16 0 1 15 0 1 9 0 1 2 0 1 4 0 1 6 8 10","13 0 4 0 1 10 0 1 9 0 1 2 0 1 9 0 1 4 0 1 3 0 1 4 0 1 4 0 1 17 0 1 4 0 1 2 0 1 9 0 1","13 0 1 0 1 2 0 1 4 0 1 9 0 1 3 0 1 4 0 1 3 0 1 9 0 1 2 0 1 16 0 1 4 0 1 11 0 1 1 0 1","13 0 1 0 1 10 0 1 9 0 1 1 0 1 1 0 1 4 0 1 15 0 1 1 0 1 15 0 1 10 0 1 4 0 1 3 0 1 9 0 1","13 1 15 0 1 4 0 1 10 0 1 1 0 1 11 0 1 4 0 1 17 0 1 9 0 1 17 0 1 1 0 1 9 0 1 3 0 1 10 0 1 6 0 6","13 1 17 0 1 4 0 1 8 0 1 1 0 1 9 0 1 7 3 10 16 0 1 10 0 1 16 0 1 15 0 1 10 0 1 3 0 1 8 0 1 6 3 10","13 0 16 0 1 2 0 1 9 0 1 1 0 1 3 0 1 4 0 1 1 0 1 8 0 1 2 0 1 17 0 1 8 0 1 1 0 1 9 0 1","13 0 10 0 1 2 0 1 1 0 1 5 8 2 9 0 1 16 0 1 15 0 1 9 0 1 15 0 1 16 0 1 9 0 1 1 0 1 3 0 1","13 1 4 0 1 7 3 14 9 0 1 4 0 1 3 0 1 17 0 1 17 0 1 3 0 1 17 0 1 4 0 1 1 0 1 1 0 1 9 0 1 6 3 14","13 0 17 0 1 0 0 1 0 0 1 2 0 1 9 0 1 1 0 1 16 0 1 9 0 1 16 0 1 9 0 1 9 0 1 1 0 1 0 0 1","1 10 3 0 1 3 0 9 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1","10 5 5 8 5 4 0 1 4 0 1 1 0 1 5 0 5 5 8 1 1 0 1 4 0 1 5 0 5 5 0 5 6 7 6 1 0 1 1 0 1 1 0 1 4 8 4","13 0 1 0 1 4 0 1 4 0 1 4 0 1 4 0 1 3 0 1 3 0 1 2 0 1 15 0 1 15 0 1 4 0 1 4 0 1 1 0 1","13 0 1 0 1 4 0 1 1 0 1 1 0 1 15 0 1 3 0 1 5 8 3 2 0 1 17 0 1 17 0 1 4 0 1 4 0 1 1 0 1","13 0 1 0 1 1 0 1 1 0 1 1 0 1 17 0 1 1 0 1 3 0 1 2 0 1 16 0 1 16 0 1 4 0 1 4 0 1 1 0 1","13 1 11 0 1 9 0 1 1 0 1 1 0 1 16 0 1 1 0 1 3 0 1 2 0 1 1 0 1 1 0 1 4 0 1 4 0 1 1 0 1 6 8 10","13 1 9 0 1 1 0 1 9 0 1 10 0 1 1 0 1 1 0 1 1 0 1 9 0 1 15 0 1 15 0 1 4 0 1 1 0 1 1 0 1 6 6 6","13 1 3 0 1 1 0 1 4 0 1 2 0 1 15 0 1 9 0 1 11 0 1 10 0 1 17 0 1 17 0 1 9 0 1 1 0 1 9 0 1 6 6 3","13 0 11 0 1 9 0 1 4 0 1 2 0 1 17 0 1 3 0 1 9 0 1 8 0 1 16 0 1 16 0 1 10 0 1 1 0 1 4 0 1","13 0 9 0 1 10 0 1 9 0 1 2 0 1 16 0 1 10 0 1 3 0 1 9 0 1 10 0 1 1 0 1 8 0 1 1 0 1 9 0 1","13 1 3 0 1 1 0 1 10 0 1 7 7 4 4 0 1 3 0 1 2 0 1 4 0 1 1 0 1 15 0 1 9 0 1 9 0 1 10 0 1 6 7 4","13 0 2 0 1 10 0 1 2 0 1 3 0 1 15 0 1 2 0 1 11 0 1 4 0 1 15 0 1 17 0 1 3 0 1 10 0 1 8 0 1","13 0 11 0 1 3 0 1 9 0 1 5 0 2 17 0 1 10 0 1 9 0 1 9 0 1 17 0 1 16 0 1 3 0 1 8 0 1 9 0 1","13 0 9 0 1 9 0 1 10 0 1 3 0 1 16 0 1 2 0 1 3 0 1 4 0 1 16 0 1 10 0 1 3 0 1 9 0 1 3 0 1","13 0 3 0 1 10 0 1 3 0 1 15 0 1 2 0 1 11 0 1 11 0 1 9 0 1 1 0 1 3 0 1 3 0 1 3 0 1 3 0 1","13 0 11 0 1 3 0 1 3 0 1 17 0 1 15 0 1 9 0 1 9 0 1 1 0 1 15 0 1 15 0 1 5 8 3 2 0 1 9 0 1","13 1 9 0 1 3 0 1 3 0 1 16 0 1 17 0 1 10 0 1 1 0 1 9 0 1 17 0 1 17 0 1 4 0 1 9 0 1 3 0 1 6 6 9","13 0 2 0 1 2 0 1 3 0 1 10 0 1 16 0 1 4 0 1 1 0 1 4 0 1 16 0 1 16 0 1 4 0 1 3 0 1 9 0 1","13 1 11 0 1 2 0 1 2 0 1 3 0 1 10 0 1 4 0 1 1 0 1 9 0 1 4 0 1 2 0 1 11 0 1 1 0 1 3 0 1 6 0 6","13 1 9 0 1 2 0 1 7 3 4 15 0 1 4 0 1 4 0 1 9 0 1 10 0 1 2 0 1 15 0 1 4 0 1 9 0 1 3 0 1 6 3 4","13 0 0 0 1 2 0 1 4 0 1 17 0 1 15 0 1 4 0 1 10 0 1 8 0 1 15 0 1 17 0 1 11 0 1 3 0 1 9 0 1","13 1 0 0 1 7 3 6 4 0 1 16 0 1 17 0 1 2 0 1 8 0 1 9 0 1 17 0 1 16 0 1 3 0 1 9 0 1 10 0 1 6 3 6","13 1 0 0 1 0 0 1 4 0 1 0 0 1 16 0 1 7 3 6 9 0 1 1 0 1 16 0 1 0 0 1 3 0 1 1 0 1 8 0 1 6 3 6","13 0 0 0 1 0 0 1 10 0 1 0 0 1 4 0 1 0 0 1 0 0 1 9 0 1 10 0 1 0 0 1 2 0 1 9 0 1 9 0 1","1 10 5 0 5 3 0 9 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1","10 4 3 0 1 1 0 1 5 8 5 1 0 1 5 0 5 3 0 1 5 8 2 4 0 1 5 0 5 5 0 2 1 0 1 1 0 1 1 0 1 4 8 4","13 0 15 0 1 1 0 1 4 0 1 5 8 2 4 0 1 3 0 1 2 0 1 4 0 1 15 0 1 3 0 1 4 0 1 4 0 1 5 8 1","13 0 17 0 1 1 0 1 2 0 1 3 0 1 15 0 1 1 0 1 2 0 1 1 0 1 17 0 1 15 0 1 4 0 1 4 0 1 4 0 1","13 0 16 0 1 1 0 1 11 0 1 3 0 1 17 0 1 10 0 1 2 0 1 1 0 1 16 0 1 17 0 1 4 0 1 4 0 1 4 0 1","13 1 10 0 1 10 0 1 9 0 1 3 0 1 16 0 1 3 0 1 11 0 1 1 0 1 10 0 1 16 0 1 4 0 1 4 0 1 4 0 1 6 8 10","13 2 1 0 1 2 0 1 4 0 1 1 0 1 1 0 1 1 0 1 9 0 1 1 0 1 1 0 1 3 0 1 4 0 1 4 0 1 1 0 1 6 6 6 6 7 6","13 2 15 0 1 10 0 1 11 0 1 1 0 1 15 0 1 10 0 1 4 0 1 9 0 1 15 0 1 15 0 1 1 0 1 2 0 1 1 0 1 6 6 6 6 7 2","13 1 17 0 1 3 0 1 9 0 1 1 0 1 17 0 1 2 0 1 11 0 1 10 0 1 17 0 1 17 0 1 12 0 1 9 0 1 1 0 1 6 0 6","13 0 16 0 1 10 0 1 4 0 1 11 0 1 16 0 1 10 0 1 9 0 1 8 0 1 16 0 1 16 0 1 8 0 1 2 0 1 1 0 1","13 0 10 0 1 1 0 1 11 0 1 9 0 1 4 0 1 2 0 1 4 0 1 9 0 1 1 0 1 10 0 1 9 0 1 9 0 1 11 0 1","13 0 1 0 1 10 0 1 9 0 1 3 0 1 15 0 1 10 0 1 9 0 1 1 0 1 15 0 1 3 0 1 3 0 1 10 0 1 9 0 1","13 0 15 0 1 3 0 1 3 0 1 2 0 1 17 0 1 3 0 1 4 0 1 9 0 1 17 0 1 1 0 1 3 0 1 8 0 1 4 0 1","13 2 17 0 1 10 0 1 2 0 1 11 0 1 16 0 1 10 0 1 9 0 1 10 0 1 16 0 1 1 0 1 2 0 1 9 0 1 9 0 1 6 6 9 6 7 4","13 0 16 0 1 2 0 1 11 0 1 9 0 1 10 0 1 4 0 1 10 0 1 8 0 1 1 0 1 1 0 1 9 0 1 3 0 1 3 0 1","13 0 3 0 1 10 0 1 9 0 1 2 0 1 2 0 1 4 0 1 8 0 1 9 0 1 15 0 1 1 0 1 4 0 1 9 0 1 2 0 1","13 0 15 0 1 2 0 1 3 0 1 9 0 1 15 0 1 4 0 1 9 0 1 4 0 1 16 0 1 9 0 1 9 0 1 3 0 1 9 0 1","13 0 17 0 1 10 0 1 11 0 1 4 0 1 17 0 1 4 0 1 2 0 1 2 0 1 4 0 1 4 0 1 1 0 1 3 0 1 4 0 1","13 1 16 0 1 4 0 1 9 0 1 4 0 1 16 0 1 7 3 10 9 0 1 9 0 1 2 0 1 11 0 1 1 0 1 2 0 1 2 0 1 6 3 10","13 0 2 0 1 4 0 1 3 0 1 4 0 1 4 0 1 4 0 1 10 0 1 10 0 1 15 0 1 4 0 1 1 0 1 2 0 1 9 0 1","13 0 15 0 1 2 0 1 9 0 1 4 0 1 15 0 1 2 0 1 8 0 1 8 0 1 17 0 1 11 0 1 9 0 1 9 0 1 2 0 1","13 0 17 0 1 2 0 1 1 0 1 4 0 1 17 0 1 9 0 1 9 0 1 9 0 1 16 0 1 4 0 1 10 0 1 4 0 1 9 0 1","13 1 16 0 1 7 3 14 9 0 1 10 0 1 16 0 1 4 0 1 4 0 1 1 0 1 4 0 1 4 0 1 8 0 1 9 0 1 3 0 1 6 3 14","13 0 10 0 1 5 8 1 0 0 1 1 0 1 0 0 1 9 0 1 9 0 1 9 0 1 9 0 1 2 0 1 9 0 1 0 0 1 9 0 1","1 10 4 0 1 3 0 9 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1","10 5 4 0 1 5 0 4 5 0 5 4 0 1 4 0 1 5 0 5 5 8 2 4 0 1 4 0 1 4 0 1 6 7 10 1 0 1 1 0 1 1 0 1 4 8 1","13 0 2 0 1 4 0 1 15 0 1 2 0 1 2 0 1 15 0 1 3 0 1 4 0 1 3 0 1 4 0 1 3 0 1 3 0 1 4 0 1","13 0 10 0 1 15 0 1 17 0 1 2 0 1 2 0 1 17 0 1 1 0 1 2 0 1 1 0 1 1 0 1 3 0 1 3 0 1 4 0 1","13 0 4 0 1 17 0 1 16 0 1 10 0 1 2 0 1 16 0 1 1 0 1 2 0 1 1 0 1 1 0 1 3 0 1 3 0 1 10 0 1","13 1 10 0 1 16 0 1 1 0 1 3 0 1 2 0 1 1 0 1 1 0 1 2 0 1 1 0 1 9 0 1 1 0 1 1 0 1 3 0 1 6 8 10","13 2 2 0 1 4 0 1 15 0 1 10 0 1 9 0 1 15 0 1 9 0 1 2 0 1 10 0 1 10 0 1 9 0 1 1 0 1 10 0 1 6 6 6 6 7 2","13 1 10 0 1 15 0 1 17 0 1 2 0 1 4 0 1 17 0 1 4 0 1 9 0 1 3 0 1 8 0 1 3 0 1 9 0 1 1 0 1 6 6 6","13 0 3 0 1 17 0 1 16 0 1 10 0 1 9 0 1 16 0 1 9 0 1 10 0 1 16 0 1 9 0 1 9 0 1 4 0 1 10 0 1","13 0 10 0 1 16 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 8 0 1 17 0 1 4 0 1 4 0 1 9 0 1 1 0 1","13 0 2 0 1 4 0 1 15 0 1 1 0 1 10 0 1 15 0 1 11 0 1 9 0 1 10 0 1 2 0 1 1 0 1 1 0 1 1 0 1","13 0 10 0 1 15 0 1 17 0 1 10 0 1 4 0 1 17 0 1 9 0 1 4 0 1 2 0 1 9 0 1 1 0 1 9 0 1 9 0 1","13 0 3 0 1 17 0 1 16 0 1 1 0 1 9 0 1 16 0 1 3 0 1 4 0 1 16 0 1 10 0 1 1 0 1 3 0 1 4 0 1","13 2 1 0 1 16 0 1 4 0 1 7 3 8 4 0 1 10 0 1 3 0 1 9 0 1 17 0 1 8 0 1 1 0 1 9 0 1 1 0 1 6 6 9 6 3 8","13 0 10 0 1 3 0 1 4 0 1 5 8 1 1 0 1 1 0 1 2 0 1 10 0 1 3 0 1 9 0 1 9 0 1 1 0 1 10 0 1","13 0 1 0 1 3 0 1 2 0 1 2 0 1 9 0 1 15 0 1 11 0 1 8 0 1 2 0 1 4 0 1 10 0 1 10 0 1 4 0 1","13 0 10 0 1 3 0 1 15 0 1 2 0 1 4 0 1 17 0 1 9 0 1 9 0 1 16 0 1 1 0 1 8 0 1 3 0 1 10 0 1","13 0 3 0 1 3 0 1 17 0 1 11 0 1 1 0 1 16 0 1 1 0 1 1 0 1 17 0 1 1 0 1 9 0 1 2 0 1 2 0 1","13 2 10 0 1 3 0 1 16 0 1 0 0 1 9 0 1 4 0 1 9 0 1 9 0 1 4 0 1 9 0 1 4 0 1 10 0 1 10 0 1 6 8 14 6 0 24","13 1 7 3 16 15 0 1 4 0 1 0 0 1 0 0 1 2 0 1 3 0 1 1 0 1 4 0 1 1 0 1 4 0 1 2 0 1 4 0 1 6 3 16","13 0 0 0 1 17 0 1 15 0 1 0 0 1 0 0 1 15 0 1 3 0 1 1 0 1 4 0 1 9 0 1 9 0 1 10 0 1 2 0 1","13 1 0 0 1 16 0 1 17 0 1 0 0 1 0 0 1 17 0 1 9 0 1 1 0 1 2 0 1 10 0 1 4 0 1 0 0 1 10 0 1 6 7 6","13 0 0 0 1 10 0 1 16 0 1 0 0 1 0 0 1 16 0 1 2 0 1 9 0 1 2 0 1 8 0 1 4 0 1 0 0 1 2 0 1","13 0 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 9 0 1 0 0 1 11 0 1 9 0 1 9 0 1 0 0 1 10 0 1","1 10 5 0 5 3 0 9 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1","10 5 15 0 1 1 0 1 5 8 4 1 0 1 5 0 5 3 0 1 2 0 1 4 0 1 4 0 1 5 0 5 6 7 4 1 0 1 1 0 1 1 0 1 4 8 4","13 1 4 0 1 1 0 1 11 0 1 5 0 2 1 0 1 3 0 1 9 0 1 2 0 1 4 0 1 15 0 1 3 0 1 4 0 1 4 0 1 6 8 10","13 0 15 0 1 1 0 1 9 0 1 3 0 1 15 0 1 1 0 1 4 0 1 2 0 1 1 0 1 17 0 1 3 0 1 1 0 1 4 0 1","13 0 17 0 1 1 0 1 4 0 1 3 0 1 17 0 1 10 0 1 4 0 1 9 0 1 1 0 1 16 0 1 3 0 1 16 0 1 4 0 1","13 0 16 0 1 10 0 1 11 0 1 15 0 1 16 0 1 3 0 1 9 0 1 2 0 1 1 0 1 10 0 1 1 0 1 17 0 1 4 0 1","13 3 4 0 1 2 0 1 9 0 1 17 0 1 4 0 1 1 0 1 3 0 1 9 0 1 9 0 1 1 0 1 1 0 1 10 0 1 9 0 1 6 3 6 6 6 6 6 7 6","13 3 4 0 1 10 0 1 4 0 1 16 0 1 15 0 1 10 0 1 9 0 1 4 0 1 4 0 1 15 0 1 1 0 1 1 0 1 1 0 1 6 3 6 6 6 6 6 7 2","13 1 15 0 1 3 0 1 11 0 1 4 0 1 17 0 1 2 0 1 2 0 1 4 0 1 4 0 1 17 0 1 1 0 1 10 0 1 12 0 1 6 3 6","13 0 17 0 1 10 0 1 9 0 1 1 0 1 16 0 1 10 0 1 9 0 1 9 0 1 9 0 1 16 0 1 9 0 1 1 0 1 8 0 1","13 0 16 0 1 1 0 1 4 0 1 1 0 1 1 0 1 2 0 1 2 0 1 10 0 1 10 0 1 10 0 1 3 0 1 10 0 1 9 0 1","13 1 3 0 1 10 0 1 11 0 1 15 0 1 15 0 1 10 0 1 9 0 1 8 0 1 8 0 1 1 0 1 1 0 1 4 0 1 1 0 1 6 0 1","13 1 3 0 1 3 0 1 9 0 1 17 0 1 17 0 1 3 0 1 2 0 1 9 0 1 9 0 1 15 0 1 9 0 1 10 0 1 12 0 1 6 8 6","13 2 3 0 1 10 0 1 2 0 1 16 0 1 16 0 1 10 0 1 9 0 1 1 0 1 3 0 1 17 0 1 10 0 1 4 0 1 8 0 1 6 3 18 6 6 9","13 1 3 0 1 2 0 1 9 0 1 3 0 1 4 0 1 4 0 1 10 0 1 9 0 1 12 0 1 16 0 1 8 0 1 4 0 1 9 0 1 6 0 3","13 0 3 0 1 10 0 1 4 0 1 3 0 1 2 0 1 4 0 1 8 0 1 4 0 1 8 0 1 4 0 1 9 0 1 2 0 1 3 0 1","13 0 15 0 1 2 0 1 9 0 1 3 0 1 15 0 1 4 0 1 9 0 1 9 0 1 9 0 1 15 0 1 2 0 1 2 0 1 9 0 1","13 0 17 0 1 10 0 1 10 0 1 9 0 1 17 0 1 4 0 1 3 0 1 10 0 1 3 0 1 17 0 1 9 0 1 10 0 1 1 0 1","13 1 16 0 1 4 0 1 8 0 1 2 0 1 16 0 1 7 3 10 9 0 1 8 0 1 1 0 1 16 0 1 0 0 1 4 0 1 1 0 1 6 3 10","13 0 1 0 1 4 0 1 9 0 1 9 0 1 2 0 1 0 0 1 0 0 1 9 0 1 12 0 1 1 0 1 0 0 1 2 0 1 9 0 1","13 1 15 0 1 2 0 1 2 0 1 0 0 1 15 0 1 0 0 1 0 0 1 2 0 1 8 0 1 15 0 1 0 0 1 9 0 1 3 0 1 6 7 8","13 0 17 0 1 2 0 1 9 0 1 0 0 1 17 0 1 0 0 1 0 0 1 9 0 1 9 0 1 17 0 1 0 0 1 0 0 1 3 0 1","13 1 16 0 1 7 3 14 2 0 1 0 0 1 16 0 1 0 0 1 0 0 1 2 0 1 3 0 1 16 0 1 0 0 1 0 0 1 3 0 1 6 3 14","13 0 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1 0 0 1 0 0 1 9 0 1 9 0 1 10 0 1 0 0 1 0 0 1 9 0 1","1 10 5 0 5 6 7 11 6 8 14 3 0 9 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1","8 6 4 0 1 5 0 5 4 0 1 1 0 1 5 0 5 4 0 1 4 0 1 4 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 4 8 4","13 1 15 0 1 15 0 1 4 0 1 5 8 1 3 0 1 5 0 5 4 0 1 2 0 1 3 0 1 4 0 1 4 0 1 4 0 1 3 0 1 6 8 4","13 0 17 0 1 17 0 1 4 0 1 3 0 1 3 0 1 15 0 1 2 0 1 2 0 1 3 0 1 4 0 1 4 0 1 4 0 1 3 0 1","13 0 16 0 1 16 0 1 10 0 1 1 0 1 15 0 1 17 0 1 2 0 1 2 0 1 1 0 1 4 0 1 4 0 1 1 0 1 3 0 1","13 1 1 0 1 1 0 1 3 0 1 1 0 1 17 0 1 16 0 1 2 0 1 2 0 1 1 0 1 4 0 1 2 0 1 1 0 1 1 0 1 6 8 2","13 1 15 0 1 15 0 1 10 0 1 1 0 1 16 0 1 1 0 1 2 0 1 9 0 1 12 0 1 9 0 1 10 0 1 9 0 1 12 0 1 6 6 6","13 1 17 0 1 17 0 1 3 0 1 1 0 1 10 0 1 15 0 1 9 0 1 10 0 1 8 0 1 10 0 1 4 0 1 3 0 1 8 0 1 6 6 6","13 1 16 0 1 16 0 1 10 0 1 11 0 1 3 0 1 17 0 1 4 0 1 8 0 1 9 0 1 8 0 1 10 0 1 1 0 1 9 0 1 6 6 3","13 0 4 0 1 1 0 1 2 0 1 9 0 1 15 0 1 16 0 1 9 0 1 9 0 1 1 0 1 9 0 1 4 0 1 9 0 1 1 0 1","13 0 15 0 1 15 0 1 10 0 1 2 0 1 17 0 1 1 0 1 10 0 1 1 0 1 12 0 1 1 0 1 9 0 1 3 0 1 12 0 1","13 0 17 0 1 17 0 1 3 0 1 12 0 1 16 0 1 15 0 1 8 0 1 10 0 1 8 0 1 1 0 1 1 0 1 3 0 1 8 0 1","13 0 16 0 1 16 0 1 10 0 1 8 0 1 10 0 1 17 0 1 9 0 1 4 0 1 9 0 1 1 0 1 1 0 1 12 0 1 9 0 1","13 1 2 0 1 10 0 1 2 0 1 9 0 1 3 0 1 16 0 1 4 0 1 10 0 1 3 0 1 1 0 1 9 0 1 8 0 1 1 0 1 6 6 6","13 0 15 0 1 3 0 1 10 0 1 3 0 1 12 0 1 1 0 1 9 0 1 1 0 1 3 0 1 1 0 1 1 0 1 9 0 1 1 0 1","13 0 17 0 1 15 0 1 1 0 1 9 0 1 8 0 1 15 0 1 1 0 1 10 0 1 10 0 1 9 0 1 9 0 1 1 0 1 9 0 1","13 1 16 0 1 17 0 1 1 0 1 3 0 1 9 0 1 17 0 1 9 0 1 4 0 1 2 0 1 3 0 1 3 0 1 9 0 1 4 0 1 6 0 2","13 0 10 0 1 16 0 1 10 0 1 3 0 1 3 0 1 16 0 1 10 0 1 10 0 1 10 0 1 10 0 1 3 0 1 4 0 1 9 0 1","13 1 4 0 1 2 0 1 7 3 14 9 0 1 12 0 1 4 0 1 8 0 1 4 0 1 0 0 1 3 0 1 10 0 1 9 0 1 0 0 1 6 3 14","13 0 15 0 1 15 0 1 0 0 1 10 0 1 8 0 1 2 0 1 9 0 1 9 0 1 0 0 1 2 0 1 4 0 1 10 0 1 0 0 1","13 0 17 0 1 17 0 1 0 0 1 8 0 1 9 0 1 15 0 1 3 0 1 4 0 1 0 0 1 9 0 1 1 0 1 8 0 1 0 0 1","13 0 16 0 1 16 0 1 0 0 1 9 0 1 0 0 1 17 0 1 9 0 1 9 0 1 0 0 1 0 0 1 9 0 1 9 0 1 0 0 1","13 0 1 0 1 10 0 1 0 0 1 4 0 1 0 0 1 16 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 4 0 1 0 0 1","13 0 9 0 1 0 0 1 0 0 1 10 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 9 0 1 0 0 1","1 10 2 0 1 6 6 27 3 0 7 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1","9 5 5 8 6 5 0 5 5 0 5 4 0 1 5 0 5 5 0 2 5 8 3 4 0 1 4 0 1 1 0 1 1 0 1 1 0 1 1 0 1 4 8 4","13 0 9 0 1 15 0 1 15 0 1 3 0 1 4 0 1 3 0 1 2 0 1 4 0 1 1 0 1 4 0 1 4 0 1 4 0 1 4 0 1","13 0 2 0 1 17 0 1 17 0 1 1 0 1 15 0 1 15 0 1 2 0 1 9 0 1 10 0 1 4 0 1 4 0 1 4 0 1 4 0 1","13 0 11 0 1 16 0 1 16 0 1 5 8 2 17 0 1 17 0 1 11 0 1 4 0 1 2 0 1 4 0 1 4 0 1 4 0 1 1 0 1","13 0 9 0 1 10 0 1 10 0 1 1 0 1 16 0 1 16 0 1 9 0 1 9 0 1 10 0 1 4 0 1 4 0 1 4 0 1 1 0 1","13 3 4 0 1 1 0 1 1 0 1 1 0 1 1 0 1 3 0 1 2 0 1 3 0 1 3 0 1 4 0 1 9 0 1 9 0 1 1 0 1 6 3 6 6 7 6 6 8 9","13 2 11 0 1 15 0 1 15 0 1 1 0 1 15 0 1 15 0 1 11 0 1 3 0 1 7 7 8 2 0 1 1 0 1 10 0 1 9 0 1 6 3 6 6 7 4","13 2 9 0 1 17 0 1 17 0 1 1 0 1 17 0 1 17 0 1 9 0 1 3 0 1 1 0 1 2 0 1 1 0 1 8 0 1 10 0 1 6 3 6 6 7 6","13 2 4 0 1 16 0 1 16 0 1 10 0 1 16 0 1 16 0 1 4 0 1 3 0 1 10 0 1 9 0 1 1 0 1 9 0 1 8 0 1 6 3 1 6 7 2","13 1 11 0 1 1 0 1 10 0 1 11 0 1 4 0 1 3 0 1 11 0 1 3 0 1 1 0 1 10 0 1 9 0 1 1 0 1 9 0 1 6 7 18","13 0 9 0 1 15 0 1 1 0 1 3 0 1 15 0 1 1 0 1 9 0 1 3 0 1 10 0 1 8 0 1 10 0 1 1 0 1 4 0 1","13 0 4 0 1 17 0 1 15 0 1 3 0 1 17 0 1 1 0 1 4 0 1 3 0 1 3 0 1 9 0 1 8 0 1 9 0 1 9 0 1","13 1 11 0 1 16 0 1 17 0 1 2 0 1 16 0 1 1 0 1 9 0 1 1 0 1 3 0 1 3 0 1 9 0 1 1 0 1 10 0 1 6 3 14","13 0 9 0 1 1 0 1 16 0 1 10 0 1 2 0 1 12 0 1 4 0 1 1 0 1 10 0 1 3 0 1 1 0 1 9 0 1 8 0 1","13 0 3 0 1 15 0 1 3 0 1 11 0 1 15 0 1 8 0 1 9 0 1 12 0 1 3 0 1 3 0 1 9 0 1 1 0 1 9 0 1","13 0 2 0 1 17 0 1 15 0 1 1 0 1 17 0 1 9 0 1 10 0 1 8 0 1 2 0 1 2 0 1 3 0 1 9 0 1 2 0 1","13 0 11 0 1 16 0 1 17 0 1 10 0 1 16 0 1 3 0 1 8 0 1 9 0 1 9 0 1 2 0 1 1 0 1 10 0 1 9 0 1","13 1 9 0 1 4 0 1 16 0 1 4 0 1 4 0 1 1 0 1 9 0 1 1 0 1 3 0 1 9 0 1 9 0 1 8 0 1 4 0 1 6 0 9","13 0 3 0 1 2 0 1 2 0 1 10 0 1 15 0 1 9 0 1 1 0 1 12 0 1 2 0 1 4 0 1 3 0 1 9 0 1 2 0 1","13 0 11 0 1 15 0 1 15 0 1 4 0 1 17 0 1 4 0 1 9 0 1 8 0 1 9 0 1 9 0 1 9 0 1 3 0 1 9 0 1","13 0 9 0 1 17 0 1 17 0 1 2 0 1 16 0 1 9 0 1 4 0 1 9 0 1 0 0 1 4 0 1 10 0 1 12 0 1 4 0 1","13 0 0 0 1 16 0 1 16 0 1 9 0 1 0 0 1 0 0 1 1 0 1 0 0 1 0 0 1 4 0 1 8 0 1 8 0 1 9 0 1","13 0 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1 9 0 1 9 0 1 9 0 1 0 0 1","1 10 5 0 5 6 7 3 6 8 16 3 0 17 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1","8 6 4 0 1 5 0 5 4 0 1 4 0 1 3 0 1 5 0 2 10 0 1 4 0 1 6 6 6 1 0 1 1 0 1 1 0 1 1 0 1 4 8 2","12 1 15 0 1 4 0 1 4 0 1 2 0 1 5 0 5 3 0 1 7 3 2 4 0 1 3 0 1 1 0 1 4 0 1 4 0 1 6 8 2","12 0 16 0 1 15 0 1 4 0 1 2 0 1 15 0 1 15 0 1 2 0 1 4 0 1 3 0 1 1 0 1 4 0 1 5 8 1","12 1 1 0 1 17 0 1 4 0 1 2 0 1 17 0 1 17 0 1 10 0 1 1 0 1 1 0 1 1 0 1 1 0 1 4 0 1 6 8 1","12 0 15 0 1 16 0 1 9 0 1 2 0 1 16 0 1 16 0 1 4 0 1 1 0 1 1 0 1 1 0 1 1 0 1 10 0 1","12 2 17 0 1 1 0 1 3 0 1 9 0 1 1 0 1 10 0 1 10 0 1 1 0 1 1 0 1 1 0 1 1 0 1 11 0 1 6 3 6 6 6 6","12 2 16 0 1 15 0 1 1 0 1 4 0 1 15 0 1 3 0 1 2 0 1 9 0 1 9 0 1 12 0 1 1 0 1 4 0 1 6 3 3 6 6 3","12 0 4 0 1 17 0 1 1 0 1 4 0 1 17 0 1 15 0 1 10 0 1 10 0 1 3 0 1 8 1 1 9 0 1 10 0 1","12 0 15 0 1 16 0 1 9 0 1 9 0 1 16 0 1 17 0 1 3 0 1 8 0 1 12 0 1 9 0 1 10 0 1 2 0 1","12 0 17 0 1 1 0 1 10 0 1 10 0 1 1 0 1 16 0 1 10 0 1 9 0 1 8 1 1 3 0 1 8 0 1 10 0 1","12 0 16 0 1 15 0 1 8 0 1 8 0 1 15 0 1 3 0 1 2 0 1 4 0 1 9 0 1 12 0 1 9 0 1 2 0 1","12 0 2 0 1 17 0 1 9 0 1 9 0 1 17 0 1 1 0 1 10 0 1 1 0 1 2 0 1 8 1 1 3 0 1 10 0 1","12 1 15 0 1 16 0 1 4 0 1 4 0 1 16 0 1 9 0 1 4 0 1 9 0 1 9 0 1 9 0 1 3 0 1 4 0 1 6 3 14","12 1 17 0 1 1 0 1 1 0 1 9 0 1 10 0 1 3 0 1 10 0 1 10 0 1 3 0 1 3 0 1 9 0 1 9 0 1 6 6 9","12 0 16 0 1 15 0 1 9 0 1 4 0 1 3 0 1 2 0 1 4 0 1 8 0 1 9 0 1 12 0 1 2 0 1 1 0 1","12 1 10 0 1 17 0 1 10 0 1 9 0 1 15 0 1 9 0 1 9 0 1 9 0 1 3 0 1 8 1 1 10 0 1 10 0 1 6 0 7","12 0 4 0 1 16 0 1 8 0 1 10 0 1 17 0 1 4 0 1 3 0 1 3 0 1 1 0 1 9 0 1 2 0 1 4 0 1","12 1 15 0 1 4 0 1 9 0 1 8 1 1 16 0 1 9 0 1 2 0 1 3 0 1 9 0 1 3 0 1 2 0 1 9 0 1 6 0 6","12 0 17 0 1 2 0 1 1 0 1 9 0 1 2 0 1 4 0 1 9 0 1 9 0 1 1 0 1 9 0 1 2 0 1 1 0 1","12 1 16 0 1 15 0 1 9 0 1 1 0 1 15 0 1 1 0 1 0 0 1 3 0 1 9 0 1 10 0 1 7 7 3 1 0 1 6 7 3","12 0 10 0 1 17 0 1 10 0 1 9 0 1 17 0 1 9 0 1 0 0 1 3 0 1 10 0 1 8 0 1 4 0 1 1 0 1","12 0 2 0 1 16 0 1 8 0 1 0 0 1 16 0 1 0 0 1 0 0 1 9 0 1 8 1 1 9 0 1 17 0 1 9 0 1","12 0 10 0 1 10 0 1 9 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1 0 0 1","1 10 5 0 5 6 8 5 3 0 9 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1","9 4 3 0 1 5 0 5 5 8 3 4 0 1 5 0 5 4 0 1 4 0 1 4 0 1 5 0 5 1 0 1 1 0 1 1 0 1 4 8 4","12 1 15 0 1 4 0 1 11 0 1 2 0 1 4 0 1 1 0 1 9 0 1 2 0 1 15 0 1 3 0 1 4 0 1 5 0 2 6 8 4","12 0 17 0 1 4 0 1 9 0 1 9 0 1 4 0 1 1 0 1 2 0 1 2 0 1 17 0 1 1 0 1 1 0 1 3 0 1","12 0 16 0 1 15 0 1 4 0 1 2 0 1 1 0 1 1 0 1 9 0 1 9 0 1 16 0 1 1 0 1 1 0 1 15 0 1","12 1 10 0 1 17 0 1 4 0 1 2 0 1 10 0 1 1 0 1 4 0 1 4 0 1 10 0 1 1 0 1 10 0 1 17 0 1 6 8 2","12 3 1 0 1 16 0 1 11 0 1 9 0 1 3 0 1 9 0 1 9 0 1 9 0 1 1 0 1 1 0 1 17 0 1 16 0 1 6 3 6 6 6 6 6 7 6","12 4 15 0 1 1 0 1 9 0 1 4 0 1 3 0 1 10 0 1 2 0 1 2 0 1 15 0 1 9 0 1 1 0 1 3 0 1 6 3 6 6 6 3 6 7 3 6 8 2","12 2 17 0 1 15 0 1 4 0 1 9 0 1 3 0 1 8 0 1 9 0 1 2 0 1 16 0 1 10 0 1 10 0 1 15 0 1 6 3 6 6 0 6","12 2 16 0 1 17 0 1 11 0 1 4 0 1 3 0 1 9 0 1 4 0 1 9 0 1 1 0 1 8 0 1 4 0 1 17 0 1 6 3 6 6 8 1","12 2 10 0 1 16 0 1 9 0 1 9 0 1 10 0 1 4 0 1 9 0 1 10 0 1 15 0 1 9 0 1 1 0 1 16 0 1 6 7 9 6 8 1","12 1 1 0 1 4 0 1 4 0 1 10 0 1 3 0 1 9 0 1 10 0 1 8 0 1 17 0 1 3 0 1 9 0 1 1 0 1 6 8 2","12 1 15 0 1 15 0 1 1 0 1 8 0 1 2 0 1 4 0 1 8 0 1 9 0 1 16 0 1 3 0 1 3 0 1 1 0 1 6 0 7","12 3 17 0 1 17 0 1 9 0 1 9 0 1 10 0 1 2 0 1 9 0 1 4 0 1 1 0 1 9 0 1 3 0 1 9 0 1 6 3 14 6 6 9 6 8 1","12 0 16 0 1 16 0 1 1 0 1 4 0 1 4 0 1 9 0 1 1 0 1 4 0 1 15 0 1 3 0 1 9 0 1 10 0 1","12 0 3 0 1 2 0 1 9 0 1 9 0 1 4 0 1 4 0 1 9 0 1 9 0 1 17 0 1 9 0 1 1 0 1 8 0 1","12 1 15 0 1 15 0 1 10 0 1 4 0 1 7 7 9 2 0 1 4 0 1 10 0 1 16 0 1 10 0 1 9 0 1 9 0 1 6 7 9","12 0 17 0 1 17 0 1 8 0 1 9 0 1 3 0 1 9 0 1 9 0 1 8 0 1 4 0 1 8 0 1 4 0 1 3 0 1","12 0 16 0 1 16 0 1 9 0 1 10 0 1 3 0 1 1 0 1 10 0 1 9 0 1 2 0 1 9 0 1 4 0 1 9 0 1","12 0 2 0 1 4 0 1 1 0 1 8 0 1 3 0 1 1 0 1 8 0 1 3 0 1 15 0 1 2 0 1 4 0 1 10 0 1","12 0 15 0 1 15 0 1 9 0 1 9 0 1 9 0 1 9 0 1 9 0 1 9 0 1 17 0 1 9 0 1 9 0 1 8 0 1","12 0 17 0 1 17 0 1 0 0 1 1 0 1 3 0 1 4 0 1 1 0 1 3 0 1 16 0 1 2 0 1 4 0 1 9 0 1","12 0 16 0 1 1 0 1 0 0 1 9 0 1 9 0 1 9 0 1 9 0 1 3 0 1 4 0 1 9 0 1 2 0 1 2 0 1","12 0 3 0 1 9 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 9 0 1 9 0 1 0 0 1 9 0 1 9 0 1","1 10 4 0 1 6 6 15 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1","10 5 10 0 1 5 0 4 5 0 6 2 0 1 4 0 1 5 0 7 4 0 1 2 0 1 4 0 1 4 0 1 6 3 10 6 7 3 1 0 1 1 0 1 4 8 2","12 0 2 0 1 5 0 2 15 0 1 4 0 1 4 0 1 4 0 1 3 0 1 4 0 1 2 0 1 1 0 1 1 0 1 3 0 1","12 0 10 0 1 15 0 1 17 0 1 2 0 1 4 0 1 15 0 1 3 0 1 10 0 1 10 0 1 10 0 1 1 0 1 3 0 1","12 0 3 0 1 17 0 1 16 0 1 10 0 1 10 0 1 16 0 1 3 0 1 12 0 1 4 0 1 3 0 1 1 0 1 1 0 1","12 0 10 0 1 16 0 1 1 0 1 12 0 1 12 0 1 4 0 1 3 0 1 8 0 1 2 0 1 3 0 1 10 0 1 9 0 1","12 2 7 3 4 1 0 1 15 0 1 8 0 1 8 0 1 15 0 1 9 0 1 9 0 1 2 0 1 3 0 1 4 0 1 10 0 1 6 3 4 6 8 13","12 0 1 0 1 15 0 1 17 0 1 9 0 1 9 0 1 17 0 1 10 0 1 4 0 1 10 0 1 1 0 1 4 0 1 8 0 1","12 1 7 7 4 17 0 1 16 0 1 3 0 1 4 0 1 16 0 1 8 0 1 10 0 1 12 0 1 10 0 1 4 0 1 9 0 1 6 7 4","12 0 4 0 1 16 0 1 1 0 1 10 0 1 10 0 1 10 0 1 9 0 1 12 0 1 4 0 1 4 0 1 9 0 1 3 0 1","12 0 4 0 1 1 0 1 15 0 1 12 0 1 12 0 1 1 0 1 3 0 1 8 0 1 4 0 1 2 0 1 4 0 1 9 0 1","12 0 4 0 1 15 0 1 17 0 1 8 0 1 8 0 1 15 0 1 9 0 1 9 0 1 9 0 1 2 0 1 9 0 1 10 0 1","12 2 4 0 1 17 0 1 16 0 1 9 0 1 9 0 1 4 0 1 10 0 1 4 0 1 4 0 1 7 7 8 1 0 1 8 0 1 6 7 8 6 0 27","12 0 9 0 1 16 0 1 3 0 1 2 0 1 4 0 1 2 0 1 8 1 1 10 0 1 2 0 1 1 0 1 9 0 1 9 0 1","12 0 3 0 1 1 0 1 15 0 1 10 0 1 9 0 1 15 0 1 9 0 1 12 0 1 10 0 1 1 0 1 1 0 1 4 0 1","12 0 1 0 1 15 0 1 2 0 1 12 0 1 10 0 1 3 0 1 1 0 1 8 0 1 1 0 1 1 0 1 9 0 1 1 0 1","12 0 9 0 1 16 0 1 15 0 1 8 0 1 8 1 1 3 0 1 9 0 1 9 0 1 1 0 1 9 0 1 10 0 1 1 0 1","12 0 4 0 1 4 0 1 16 0 1 9 0 1 9 0 1 3 0 1 1 0 1 3 0 1 9 0 1 10 0 1 3 0 1 9 0 1","12 0 1 0 1 2 0 1 2 0 1 2 0 1 1 0 1 3 0 1 9 0 1 2 0 1 10 0 1 8 0 1 9 0 1 1 0 1","12 0 9 0 1 15 0 1 15 0 1 9 0 1 1 0 1 3 0 1 10 0 1 10 0 1 0 0 1 9 0 1 3 0 1 9 0 1","12 0 1 0 1 2 0 1 17 0 1 10 0 1 1 0 1 3 0 1 4 0 1 12 0 1 0 0 1 3 0 1 9 0 1 3 0 1","12 1 1 0 1 15 0 1 16 0 1 0 0 1 1 0 1 15 0 1 1 0 1 8 1 1 0 0 1 1 0 1 2 0 1 9 0 1 6 6 3","12 0 9 0 1 16 0 1 10 0 1 0 0 1 9 0 1 16 0 1 9 0 1 9 0 1 0 0 1 9 0 1 9 0 1 3 0 1","12 0 10 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 10 0 1 0 0 1 0 0 1 0 0 1 4 0 1 10 0 1","1 10 10 0 1 6 0 25 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1","10 4 7 6 3 3 0 1 4 0 1 4 0 1 4 0 1 4 0 1 12 0 1 1 0 1 4 0 1 4 0 1 6 6 9 1 0 1 1 0 1 4 8 4","12 2 1 0 1 1 0 1 4 0 1 4 0 1 4 0 1 4 0 1 2 0 1 4 0 1 3 0 1 3 0 1 4 0 1 4 0 1 6 1 2 6 8 15","12 0 1 0 1 1 0 1 4 0 1 4 0 1 4 0 1 4 0 1 2 0 1 4 0 1 3 0 1 1 0 1 8 0 1 4 0 1","12 0 10 0 1 1 0 1 4 0 1 4 0 1 10 0 1 1 0 1 2 0 1 1 0 1 3 0 1 1 0 1 9 0 1 2 0 1","12 0 2 0 1 9 0 1 2 0 1 2 0 1 3 0 1 1 0 1 9 0 1 1 0 1 3 0 1 1 0 1 2 0 1 12 0 1","12 2 10 0 1 1 0 1 9 0 1 2 0 1 3 0 1 9 0 1 1 0 1 1 0 1 1 0 1 9 0 1 12 0 1 8 0 1 6 3 6 6 6 3","12 1 3 0 1 9 0 1 1 0 1 9 0 1 1 0 1 10 0 1 9 0 1 9 0 1 1 0 1 3 0 1 8 0 1 9 0 1 6 3 6","12 1 10 0 1 10 0 1 1 0 1 1 0 1 1 0 1 8 0 1 4 0 1 10 0 1 9 0 1 3 0 1 9 0 1 4 0 1 6 3 6","12 1 2 0 1 3 0 1 1 0 1 9 0 1 10 0 1 9 0 1 9 0 1 8 0 1 3 0 1 3 0 1 4 0 1 2 0 1 6 3 4","12 0 10 0 1 10 0 1 9 0 1 1 0 1 3 0 1 4 0 1 4 0 1 9 0 1 9 0 1 3 0 1 9 0 1 2 0 1","12 1 7 6 12 2 0 1 1 0 1 9 0 1 1 0 1 2 0 1 4 0 1 3 0 1 2 0 1 9 0 1 4 0 1 2 0 1 6 6 9","12 1 16 0 1 9 0 1 1 0 1 4 0 1 10 0 1 9 0 1 2 0 1 1 0 1 2 0 1 10 0 1 9 0 1 9 0 1 6 6 3","12 2 1 0 1 10 0 1 9 0 1 1 0 1 2 0 1 10 0 1 9 0 1 9 0 1 9 0 1 4 0 1 1 0 1 3 0 1 6 3 22 6 8 1","12 0 16 0 1 4 0 1 10 0 1 9 0 1 2 0 1 8 0 1 10 0 1 3 0 1 3 0 1 1 0 1 9 0 1 2 0 1","12 1 1 0 1 4 0 1 3 0 1 10 0 1 2 0 1 9 0 1 4 0 1 9 0 1 1 0 1 9 0 1 0 0 1 9 0 1 6 8 1","12 1 16 0 1 2 0 1 9 0 1 3 0 1 7 7 12 1 0 1 9 0 1 4 0 1 9 0 1 10 0 1 0 0 1 4 0 1 6 7 12","12 1 4 0 1 2 0 1 10 0 1 3 0 1 16 0 1 9 0 1 10 0 1 4 0 1 10 0 1 0 0 1 0 0 1 9 0 1 6 8 1","12 1 16 0 1 2 0 1 3 0 1 16 0 1 17 0 1 10 0 1 0 0 1 9 0 1 4 0 1 0 0 1 0 0 1 10 0 1 6 8 1","12 2 1 0 1 7 1 7 9 0 1 3 0 1 1 0 1 4 0 1 0 0 1 10 0 1 9 0 1 0 0 1 0 0 1 4 0 1 6 1 7 6 8 2","12 0 16 0 1 3 0 1 10 0 1 16 0 1 16 0 1 9 0 1 0 0 1 0 0 1 4 0 1 0 0 1 0 0 1 9 0 1","12 1 0 0 1 16 0 1 1 0 1 1 0 1 0 0 1 10 0 1 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1 10 0 1 6 8 1","12 0 0 0 1 1 0 1 9 0 1 16 0 1 0 0 1 0 0 1 0 0 1 0 0 1 2 0 1 0 0 1 0 0 1 0 0 1","12 0 0 0 1 16 0 1 10 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 16 0 1 0 0 1 0 0 1 0 0 1","1 10 4 0 1 6 0 75 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1","10 3 4 0 1 4 0 1 4 0 1 4 0 1 3 0 1 4 0 1 3 0 1 4 0 1 4 0 1 4 0 1 1 0 1 1 0 1 4 8 2","12 1 4 0 1 4 0 1 1 0 1 2 0 1 3 0 1 4 0 1 1 0 1 4 0 1 4 0 1 4 0 1 1 0 1 3 0 1 6 8 14","12 0 2 0 1 4 0 1 1 0 1 9 0 1 3 0 1 1 0 1 1 0 1 4 0 1 4 0 1 10 0 1 1 0 1 3 0 1","12 0 9 0 1 4 0 1 1 0 1 10 0 1 3 0 1 10 0 1 1 0 1 4 0 1 9 0 1 3 0 1 1 0 1 1 0 1","12 0 10 0 1 1 0 1 1 0 1 2 0 1 1 0 1 3 0 1 9 0 1 9 0 1 10 0 1 3 0 1 1 0 1 1 0 1","12 0 2 0 1 9 0 1 9 0 1 9 0 1 9 0 1 3 0 1 10 0 1 10 0 1 2 0 1 3 0 1 2 0 1 1 0 1","12 0 9 0 1 10 0 1 10 0 1 10 0 1 10 0 1 3 0 1 3 0 1 3 0 1 9 0 1 1 0 1 2 0 1 9 0 1","12 1 10 0 1 2 0 1 3 0 1 2 0 1 4 0 1 3 0 1 3 0 1 3 0 1 10 0 1 1 0 1 2 0 1 10 0 1 6 1 1","12 0 2 0 1 2 0 1 2 0 1 2 0 1 4 0 1 10 0 1 2 0 1 3 0 1 2 0 1 10 0 1 2 0 1 3 0 1","12 0 9 0 1 2 0 1 9 0 1 9 0 1 4 0 1 3 0 1 2 0 1 3 0 1 2 0 1 3 0 1 4 0 1 9 0 1","12 1 10 0 1 9 0 1 10 0 1 10 0 1 4 0 1 2 0 1 9 0 1 6 0 1 9 0 1 2 0 1 2 0 1 10 0 1 6 6 3","12 1 3 0 1 10 0 1 2 0 1 3 0 1 6 0 1 10 0 1 10 0 1 4 0 1 10 0 1 2 0 1 2 0 1 4 0 1 6 1 4","12 0 3 0 1 3 0 1 2 0 1 1 0 1 1 0 1 4 0 1 2 0 1 4 0 1 3 0 1 10 0 1 2 0 1 2 0 1","12 0 3 0 1 3 0 1 2 0 1 1 0 1 1 0 1 4 0 1 9 0 1 2 0 1 3 0 1 4 0 1 9 0 1 9 0 1","12 2 1 0 1 3 0 1 6 0 1 1 0 1 1 0 1 6 0 1 10 0 1 2 0 1 1 0 1 6 0 1 10 0 1 10 0 1 6 7 3 6 0 5","12 1 1 0 1 3 0 1 4 0 1 1 0 1 1 0 1 4 0 1 4 0 1 9 0 1 1 0 1 16 0 1 2 0 1 4 0 1 6 6 3","12 2 6 0 1 1 0 1 4 0 1 6 0 1 12 0 1 1 0 1 4 0 1 10 0 1 1 0 1 17 0 1 9 0 1 4 0 1 6 0 14 6 8 1","12 1 4 0 1 6 0 1 1 0 1 1 0 1 4 0 1 1 0 1 4 0 1 3 0 1 6 0 1 3 0 1 10 0 1 2 0 1 6 0 13","12 1 9 0 1 9 0 1 16 0 1 16 0 1 4 0 1 16 0 1 6 0 1 3 0 1 1 0 1 16 0 1 1 0 1 6 0 1 6 0 15","12 1 1 0 1 2 0 1 4 0 1 6 0 1 2 0 1 4 0 1 3 0 1 1 0 1 1 0 1 17 0 1 1 0 1 1 0 1 6 8 1","12 0 16 0 1 9 0 1 4 0 1 17 0 1 9 0 1 4 0 1 3 0 1 1 0 1 16 0 1 1 0 1 1 0 1 16 0 1","12 2 0 0 1 0 0 1 9 0 1 0 0 1 3 0 1 9 0 1 16 0 1 6 0 1 17 0 1 16 0 1 6 0 1 17 0 1 6 6 3 6 0 11",},

};


%%writefile source/include/policy_plugin_abi.hpp
// Stable C ABI between the native tournament and separately compiled policies.
#pragma once

#include "runtime_types.hpp"

#include <cstdint>

namespace kag::native {

inline constexpr uint32_t POLICY_PLUGIN_ABI_VERSION = 1;

using PluginAbiVersion = uint32_t (*)();
using PluginCreate = void* (*)();
using PluginDestroy = void (*)(void* context);
using PluginAct = int (*)(
    void* context,
    const State* state,
    const Config* config,
    int seat,
    Action* output);

}  // namespace kag::native


%%writefile source/include/runtime_types.hpp
// SPDX-License-Identifier: Apache-2.0
// Minimal Kaggriculture types required by the submitted tape router.
#pragma once

#include <cstdint>

namespace kag {

enum Item : std::uint8_t {
    WHEAT = 0,
    CARROT,
    TOMATO,
    STRAWBERRY,
    MELON,
    EGG,
    MILK,
    WOOL,
    FERTILIZER,
    GOOSE,
    COW,
    SHEEP,
    N_ITEMS,
};

inline constexpr int N_PRODUCTS = 9;
inline constexpr int N_CROPS = 5;
inline constexpr int N_ANIMALS = 3;
inline constexpr int MAX_UNITS = 40;
inline constexpr int BOARD = 10;
inline constexpr int MAX_SHOP_INSTANCES = 8;

inline bool is_animal(std::uint8_t item) {
    return item >= GOOSE && item < N_ITEMS;
}

enum Op : std::uint8_t {
    OP_PASS = 0,
    OP_NORTH,
    OP_SOUTH,
    OP_EAST,
    OP_WEST,
    OP_PICKUP,
    OP_DROP,
    OP_PLACE,
    OP_PLANT,
    OP_WATER,
    OP_HARVEST,
    OP_FERTILIZE,
    OP_DIG,
    OP_BUILD_COOP,
    OP_BUILD_PASTURE,
    OP_FEED,
    OP_COLLECT_FERTILIZER,
    OP_CARE,
};

enum MOp : std::uint8_t {
    M_NONE = 0,
    M_HIRE,
    M_BUY_LAND,
    M_BUY_SEED,
    M_BUY_PRODUCT,
    M_BUY_ANIMAL,
    M_SELL,
};

enum ShopId : std::uint8_t {
    SHOP_BAKERY = 0,
    SHOP_BRUNCH_SPOT,
    SHOP_FARMERS_MARKET,
    SHOP_ICE_CREAM_SHOP,
    SHOP_PET_CAFE,
    SHOP_PIZZA_SHOP,
    SHOP_SMOOTHIE_SHOP,
    SHOP_YARN_STORE,
};

enum TileKind : std::uint8_t {
    T_EMPTY = 0,
    T_LOCKED,
    T_WEED,
    T_COOP,
    T_PASTURE,
    T_PLANT,
};

struct CropDef {
    int seed;
};

inline constexpr CropDef CROPS[N_CROPS] = {{10}, {20}, {50}, {100}, {80}};

struct AnimalDef {
    int cost;
};

inline constexpr AnimalDef ANIMALS[N_ANIMALS] = {{300}, {400}, {500}};
inline constexpr int LAND_PRICES[3] = {1000, 2000, 4000};

inline int fib(int n) {
    int previous = 1;
    int current = 1;
    for (int index = 0; index < n; ++index) {
        const int next = previous + current;
        previous = current;
        current = next;
    }
    return previous;
}

struct Config {
    int episode_steps = 720;
    int max_orders = 10;
    int hire_mult = 1;
};

struct Tile {
    TileKind kind = T_EMPTY;
};

struct Farm {
    double money = 0;
    Tile tiles[BOARD][BOARD]{};
    int n_units = 1;
    int n_quadrants = 1;
    int hires_today = 0;
    std::int16_t shed[N_ITEMS]{};
    std::int16_t inv[MAX_UNITS][N_ITEMS]{};
};

struct Market {
    std::int32_t inventory[N_PRODUCTS]{};
    std::int32_t prices[N_PRODUCTS]{};
};

struct State {
    Farm farms[2]{};
    Market market{};
    std::uint8_t shops[MAX_SHOP_INSTANCES]{};
    int n_shops = 0;
    int step = 0;
};

struct UnitAction {
    std::uint8_t op = OP_PASS;
    std::uint8_t arg = 0;
    std::int16_t n = 1;
};

struct Order {
    std::uint8_t op = M_NONE;
    std::uint8_t item = 0;
    std::int32_t n = 0;
};

struct Action {
    UnitAction units[MAX_UNITS]{};
    int n_units = 1;
    Order orders[16]{};
    int n_orders = 0;
};

}  // namespace kag


%%writefile submission_bridge.cpp
// SPDX-License-Identifier: Apache-2.0
// Packed Python-observation bridge linked directly with ShopForge SixDay Guard R1.
#include "policy_plugin_abi.hpp"
#include "runtime_types.hpp"

#include <algorithm>
#include <cstdint>

extern "C" std::uint32_t kag_policy_abi_version();
extern "C" void* kag_policy_create();
extern "C" void kag_policy_destroy(void* context);
extern "C" int kag_policy_act(
    void* context,
    const kag::State* state,
    const kag::Config* config,
    int seat,
    kag::Action* output);

namespace {

#pragma pack(push, 1)
struct PackedTile {
    std::uint8_t kind = 0;
};

struct PackedFarm {
    double money = 0;
    PackedTile tiles[kag::BOARD][kag::BOARD]{};
    std::int32_t n_units = 1;
    std::int32_t n_quadrants = 1;
    std::int32_t hires_today = 0;
    std::int16_t shed[kag::N_ITEMS]{};
    std::int16_t inv[kag::MAX_UNITS][kag::N_ITEMS]{};
};

struct PackedObservation {
    std::int32_t step = 0;
    std::int32_t n_shops = 0;
    std::int32_t market_inventory[kag::N_PRODUCTS]{};
    std::int32_t market_prices[kag::N_PRODUCTS]{};
    std::uint8_t shops[kag::MAX_SHOP_INSTANCES]{};
    PackedFarm farms[2]{};
};

struct PackedAction {
    std::uint8_t unit_ops[kag::MAX_UNITS]{};
    std::uint8_t unit_args[kag::MAX_UNITS]{};
    std::int16_t unit_ns[kag::MAX_UNITS]{};
    std::int32_t n_units = 1;
    std::uint8_t order_ops[16]{};
    std::uint8_t order_items[16]{};
    std::int32_t order_ns[16]{};
    std::int32_t n_orders = 0;
};
#pragma pack(pop)

void fill_state(const PackedObservation& observation, kag::State& state) {
    state = kag::State{};
    state.step = observation.step;
    state.n_shops = std::max(0, std::min(observation.n_shops, kag::MAX_SHOP_INSTANCES));
    for (int index = 0; index < state.n_shops; ++index)
        state.shops[index] = observation.shops[index];
    for (int item = 0; item < kag::N_PRODUCTS; ++item) {
        state.market.inventory[item] = observation.market_inventory[item];
        state.market.prices[item] = observation.market_prices[item];
    }
    for (int player = 0; player < 2; ++player) {
        const PackedFarm& source = observation.farms[player];
        kag::Farm& farm = state.farms[player];
        farm.money = source.money;
        farm.n_units = std::max(1, std::min(source.n_units, kag::MAX_UNITS));
        farm.n_quadrants = std::max(0, std::min(source.n_quadrants, 4));
        farm.hires_today = source.hires_today;
        for (int y = 0; y < kag::BOARD; ++y) {
            for (int x = 0; x < kag::BOARD; ++x) {
                farm.tiles[y][x].kind =
                    static_cast<kag::TileKind>(source.tiles[y][x].kind);
            }
        }
        for (int item = 0; item < kag::N_ITEMS; ++item) {
            farm.shed[item] = source.shed[item];
        }
        for (int unit = 0; unit < kag::MAX_UNITS; ++unit)
            for (int item = 0; item < kag::N_ITEMS; ++item)
                farm.inv[unit][item] = source.inv[unit][item];
    }
}
void pack_action(const kag::Action& action, PackedAction& packed) {
    packed = PackedAction{};
    packed.n_units = std::max(1, std::min(action.n_units, kag::MAX_UNITS));
    for (int unit = 0; unit < packed.n_units; ++unit) {
        packed.unit_ops[unit] = action.units[unit].op;
        packed.unit_args[unit] = action.units[unit].arg;
        packed.unit_ns[unit] = action.units[unit].n;
    }
    packed.n_orders = std::max(0, std::min(action.n_orders, 16));
    for (int index = 0; index < packed.n_orders; ++index) {
        packed.order_ops[index] = action.orders[index].op;
        packed.order_items[index] = action.orders[index].item;
        packed.order_ns[index] = action.orders[index].n;
    }
}

struct Session {
    void* context[2]{};
    int last_step[2]{-1, -1};

    ~Session() {
        for (void*& value : context) {
            if (value != nullptr) kag_policy_destroy(value);
            value = nullptr;
        }
    }

    void reset(int seat) {
        if (context[seat] != nullptr) kag_policy_destroy(context[seat]);
        context[seat] = kag_policy_create();
        last_step[seat] = -1;
    }
};

Session session;

}  // namespace

extern "C" std::uint32_t kag_submission_abi_version() {
    return kag_policy_abi_version() == kag::native::POLICY_PLUGIN_ABI_VERSION ? 1u : 0u;
}

extern "C" int kag_submission_act(
    const PackedObservation* observation,
    int seat,
    int episode_steps,
    PackedAction* output) {
    if (observation == nullptr || output == nullptr || seat < 0 || seat > 1)
        return 1;
    if (session.context[seat] == nullptr || observation->step == 0 ||
        observation->step < session.last_step[seat]) {
        session.reset(seat);
    }
    if (session.context[seat] == nullptr) return 1;
    kag::State state;
    fill_state(*observation, state);
    kag::Config config;
    if (episode_steps > 0) config.episode_steps = episode_steps;
    kag::Action action;
    if (kag_policy_act(session.context[seat], &state, &config, seat, &action) != 0)
        return 1;
    pack_action(action, *output);
    session.last_step[seat] = observation->step;
    return 0;
}


%%writefile main.py
"""Kaggle entrypoint for the frozen hybrid_shopforge_3day_frontier_state_router_r5 native policy."""

from __future__ import annotations

import ctypes
import sys
from collections.abc import Mapping
from pathlib import Path

_ITEMS = (
    "WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG",
    "MILK", "WOOL", "FERTILIZER", "GOOSE", "COW", "SHEEP",
)
_PRODUCTS = _ITEMS[:9]
_SHOPS = (
    "BAKERY", "BRUNCH_SPOT", "FARMERS_MARKET", "ICE_CREAM_SHOP",
    "PET_CAFE", "PIZZA_SHOP", "SMOOTHIE_SHOP", "YARN_STORE",
)
_SHOP_ID = {name: index for index, name in enumerate(_SHOPS)}
_KIND_ID = {
    None: 0, "EMPTY": 0, "SOIL": 0, "LOCKED": 1, "WEED": 2,
    "COOP": 3, "PASTURE": 4, "PLANT": 5,
}
_UNIT_OPS = (
    "PASS", "NORTH", "SOUTH", "EAST", "WEST", "PICKUP", "DROP",
    "PLACE", "PLANT", "WATER", "HARVEST", "FERTILIZE", "DIG",
    "BUILD_COOP", "BUILD_PASTURE", "FEED", "COLLECT_FERTILIZER", "CARE",
)
_MARKET_OPS = ("PASS", "HIRE", "BUY_LAND", "BUY_SEED", "BUY_PRODUCT", "BUY_ANIMAL", "SELL")
_BOARD = 10
_MAX_UNITS = 40
_MAX_SHOPS = 8
_LIBRARY = None


def _read(value, key, default=None):
    if isinstance(value, Mapping):
        return value.get(key, default)
    getter = getattr(value, "get", None)
    if callable(getter):
        return getter(key, default)
    return getattr(value, key, default)


class _PackedTile(ctypes.Structure):
    _pack_ = 1
    _fields_ = [("kind", ctypes.c_uint8)]


class _PackedFarm(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("money", ctypes.c_double),
        ("tiles", _PackedTile * _BOARD * _BOARD),
        ("n_units", ctypes.c_int32),
        ("n_quadrants", ctypes.c_int32),
        ("hires_today", ctypes.c_int32),
        ("shed", ctypes.c_int16 * len(_ITEMS)),
        ("inv", ctypes.c_int16 * len(_ITEMS) * _MAX_UNITS),
    ]


class _PackedObservation(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("step", ctypes.c_int32),
        ("n_shops", ctypes.c_int32),
        ("market_inventory", ctypes.c_int32 * len(_PRODUCTS)),
        ("market_prices", ctypes.c_int32 * len(_PRODUCTS)),
        ("shops", ctypes.c_uint8 * _MAX_SHOPS),
        ("farms", _PackedFarm * 2),
    ]


class _PackedAction(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("unit_ops", ctypes.c_uint8 * _MAX_UNITS),
        ("unit_args", ctypes.c_uint8 * _MAX_UNITS),
        ("unit_ns", ctypes.c_int16 * _MAX_UNITS),
        ("n_units", ctypes.c_int32),
        ("order_ops", ctypes.c_uint8 * 16),
        ("order_items", ctypes.c_uint8 * 16),
        ("order_ns", ctypes.c_int32 * 16),
        ("n_orders", ctypes.c_int32),
    ]


def _library():
    global _LIBRARY
    if _LIBRARY is None:
        extension = "dylib" if sys.platform == "darwin" else "so"
        # Kaggle's source loader does not define ``__file__``.  The compiled
        # function filename still points at the extracted top-level main.py.
        path = Path(_library.__code__.co_filename).resolve().parent / f"agent.{extension}"
        library = ctypes.CDLL(str(path))
        library.kag_submission_abi_version.restype = ctypes.c_uint32
        library.kag_submission_act.argtypes = [
            ctypes.POINTER(_PackedObservation),
            ctypes.c_int,
            ctypes.c_int,
            ctypes.POINTER(_PackedAction),
        ]
        library.kag_submission_act.restype = ctypes.c_int
        if int(library.kag_submission_abi_version()) != 1:
            raise RuntimeError("ShopForge SixDay Guard submission ABI mismatch")
        _LIBRARY = library
    return _LIBRARY


def _fill_counts(target, mapping, names):
    for index, name in enumerate(names):
        target[index] = int(_read(mapping, name, 0) or 0) if mapping else 0


def _fill_tile(dst, tile):
    if tile is None:
        return
    if isinstance(tile, str):
        dst.kind = _KIND_ID.get(tile, 0)
        return
    kind = _read(tile, "kind")
    if kind == "PLANT" or _read(tile, "crop"):
        dst.kind = _KIND_ID["PLANT"]
        return
    dst.kind = _KIND_ID.get(kind, 0)


def _pack_observation(observation, seat):
    packed = _PackedObservation()
    step = int(_read(observation, "step", 0) or 0)
    packed.step = step
    market = _read(observation, "market", {}) or {}
    _fill_counts(packed.market_inventory, _read(market, "inventory", {}) or {}, _PRODUCTS)
    _fill_counts(packed.market_prices, _read(market, "prices", {}) or {}, _PRODUCTS)
    shops = list(_read(_read(observation, "town", {}) or {}, "unlocked_shops", []) or [])
    packed.n_shops = min(len(shops), _MAX_SHOPS)
    for index, shop in enumerate(shops[:_MAX_SHOPS]):
        packed.shops[index] = _SHOP_ID[str(shop)]

    farms = list(_read(observation, "farms", []) or [])
    if len(farms) != 2:
        raise ValueError("ShopForge needs exactly two public farms")
    for player, farm in enumerate(farms):
        dest = packed.farms[player]
        dest.money = float(_read(farm, "money", 0) or 0)
        positions = [_read(farm, "farmer", [0, 0]), *list(_read(farm, "hands", []) or [])]
        dest.n_units = max(1, min(len(positions), _MAX_UNITS))
        dest.n_quadrants = len(list(_read(farm, "unlocked_quadrants", []) or []))
        dest.hires_today = int(_read(farm, "hires_today", 0) or 0)
        tiles = list(_read(farm, "tiles", []) or [])
        for y, row in enumerate(tiles[:_BOARD]):
            for x, tile in enumerate(list(row or [])[:_BOARD]):
                _fill_tile(dest.tiles[y][x], tile)

    private = _read(observation, "private", {}) or {}
    own = packed.farms[seat]
    _fill_counts(own.shed, _read(private, "shed", {}) or {}, _ITEMS)
    inventories = list(_read(private, "inventories", []) or [])
    for unit, carried in enumerate(inventories[:_MAX_UNITS]):
        _fill_counts(own.inv[unit], carried or {}, _ITEMS)
    return packed


def _unit_order(op, arg, quantity):
    name = _UNIT_OPS[op] if 0 <= op < len(_UNIT_OPS) else "PASS"
    if name in {"PLANT", "PICKUP", "PLACE"}:
        item = _ITEMS[arg] if 0 <= arg < len(_ITEMS) else _ITEMS[0]
        return [name, item] if quantity == 1 else [name, item, int(quantity)]
    return [name]


def _market_order(op, item, quantity):
    name = _MARKET_OPS[op] if 0 <= op < len(_MARKET_OPS) else "PASS"
    if name == "PASS":
        return None
    if name in {"HIRE", "BUY_LAND"}:
        return [name]
    item_name = _ITEMS[item] if 0 <= item < len(_ITEMS) else _ITEMS[0]
    return [name, item_name, int(quantity)]


def _unpack_action(packed):
    n_units = max(1, min(int(packed.n_units), _MAX_UNITS))
    farmer = _unit_order(packed.unit_ops[0], packed.unit_args[0], packed.unit_ns[0])
    hands = [
        _unit_order(packed.unit_ops[index], packed.unit_args[index], packed.unit_ns[index])
        for index in range(1, n_units)
    ]
    market = []
    for index in range(max(0, min(int(packed.n_orders), 16))):
        order = _market_order(packed.order_ops[index], packed.order_items[index], packed.order_ns[index])
        if order is not None:
            market.append(order)
    return {"farmer": farmer, "hands": hands, "market": market}


def agent(observation, configuration=None):
    seat = int(_read(observation, "player", 0) or 0)
    packed = _pack_observation(observation, seat)
    episode_steps = int(_read(configuration or {}, "episodeSteps", 720) or 720)
    output = _PackedAction()
    status = _library().kag_submission_act(
        ctypes.byref(packed), seat, episode_steps, ctypes.byref(output)
    )
    if status != 0:
        raise RuntimeError("ShopForge native policy failed")
    return _unpack_action(output)


import subprocess
import tarfile

command = [
    "g++", "-O3", "-std=c++17", "-Wall", "-Wextra", "-pedantic",
    "-shared", "-fPIC", "-Isource/include", "-o", "agent.so",
    "source/policy.cpp", "submission_bridge.cpp",
]
subprocess.run(command, check=True)
archive = "shopstate-router-agent.tar.gz"
with tarfile.open(archive, "w:gz") as bundle:
    bundle.add("main.py", arcname="main.py")
    bundle.add("agent.so", arcname="agent.so")
with tarfile.open(archive, "r:gz") as bundle:
    assert bundle.getnames() == ["main.py", "agent.so"]
print("Built main.py, agent.so, and the top-level submission archive")

import hashlib
import json
from pathlib import Path

def file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

manifest = {
    "agent": "hybrid_shopforge_3day_frontier_state_router_r5",
    "anchor_action_sha256": "7ce8bc83ef01db6d31589384bc57d55cec3401f4a12ebf9c728f5a3c4f63f02e",
    "route_action_sha256": "0ebdd1a079a5777f8a480138bae270521a1e6012d8473899ba05ed7791e57990",
    "tape_include_sha256": file_sha256("source/tape.inc"),
    "expected_tape_include_sha256": "30b724c3c905d0c03e4ef38d36f96fb7acbd6abef5371abbedee36ea3717e09f",
    "main_py_sha256": file_sha256("main.py"),
    "agent_so_sha256": file_sha256("agent.so"),
    "submission_archive": "shopstate-router-agent.tar.gz",
    "submission_archive_sha256": file_sha256("shopstate-router-agent.tar.gz"),
    "segment_turns": 72,
    "decision_step": 360,
    "public_rules": [
        "BAKERY and market_inventory_fertilizer <= 10232.5",
        "PET_CAFE and rival_plant_tiles <= 64",
    ],
    "boundaries": [0, 72, 144, 216, 288, 360, 432, 504, 576, 648, 719],
}
assert manifest["tape_include_sha256"] == manifest["expected_tape_include_sha256"]
Path("submission-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
manifest
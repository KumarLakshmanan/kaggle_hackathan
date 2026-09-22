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

#include "sim.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>

namespace kag::native {

inline constexpr int SIX_DAY_TURNS = 144;

struct SixDayRequirements {
    double purchase_budget = 0.0;
    std::array<int, N_CROPS> starting_seeds{};
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
    std::array<int, N_CROPS> seed_balance{};
    std::array<int, N_ITEMS> item_balance{};
    std::array<int, 6> hires_by_day{};
    int quadrants = state.farms[seat].n_quadrants;

    for (int step = start; step < end; ++step) {
        const Action action = action_at(step);
        for (int index = 0; index < action.n_units; ++index) {
            const UnitAction& operation = action.units[index];
            const int quantity = planned_quantity(operation.n);
            if (operation.op == OP_PLANT && operation.arg < N_CROPS) {
                --seed_balance[operation.arg];
                result.starting_seeds[operation.arg] = std::max(
                    result.starting_seeds[operation.arg],
                    -seed_balance[operation.arg]);
            } else if (operation.op == OP_FEED) {
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
                seed_balance[order.item] += quantity;
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
    {
        "1 1 0 0 1 4 0 13",
        "1 10 1 0 1 6 0 8 3 0 7 3 4 12 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 5 10 2 5 11 2",
        "6 1 4 0 1 5 10 1 4 0 1 1 0 1 4 0 1 5 10 1 6 0 1",
        "6 1 4 0 1 1 0 1 5 11 1 1 0 1 1 0 1 14 0 1 4 0 1",
        "6 2 8 4 1 14 0 1 5 0 1 1 0 1 5 11 1 7 10 1 6 0 1 4 0 1",
        "6 2 9 0 1 7 10 1 4 0 1 1 0 1 5 0 1 17 0 1 6 0 1 4 0 1",
        "6 2 4 0 1 17 0 1 14 0 1 8 4 1 4 0 1 4 0 1 6 0 1 4 0 1",
        "6 2 8 4 1 4 0 1 7 11 1 9 0 1 1 0 1 4 0 1 6 0 1 4 0 1",
        "6 2 9 0 1 1 0 1 15 0 1 4 0 1 14 0 1 4 0 1 6 0 1 4 0 1",
        "6 2 3 0 1 8 4 1 17 0 1 4 0 1 7 11 1 8 4 1 6 0 1 4 0 1",
        "6 2 3 0 1 9 0 1 1 0 1 4 0 1 15 0 1 9 0 1 6 0 1 4 0 1",
        "6 2 17 0 1 4 0 1 1 0 1 4 0 1 17 0 1 4 0 1 6 0 1 4 0 1",
        "6 0 0 0 1 8 4 1 1 0 1 8 0 1 4 0 1 8 4 1",
        "6 0 4 0 1 9 0 1 8 4 1 9 0 1 1 0 1 9 0 1",
        "6 0 3 0 1 4 0 1 9 0 1 1 0 1 1 0 1 1 0 1",
        "6 0 0 0 1 8 4 1 1 0 1 8 0 1 8 4 1 8 0 1",
        "6 0 4 0 1 9 0 1 8 4 1 9 0 1 9 0 1 9 0 1",
        "6 0 3 0 1 4 0 1 9 0 1 3 0 1 4 0 1 0 0 1",
        "6 0 0 0 1 8 0 1 3 0 1 8 0 1 8 0 1 0 0 1",
        "6 0 4 0 1 9 0 1 8 4 1 9 0 1 9 0 1 3 0 1",
        "6 0 0 0 1 0 0 1 9 0 1 3 0 1 0 0 1 0 0 1",
        "6 0 0 0 1 0 0 1 0 0 1 8 0 1 0 0 1 0 0 1",
        "6 0 0 0 1 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1",
        "6 0 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1",
        "1 4 5 0 1 1 0 1 1 0 1 1 0 1 1 0 1",
        "5 0 4 0 1 4 0 1 4 0 1 4 0 1 5 0 1",
        "5 0 1 0 1 5 0 1 4 0 1 1 0 1 1 0 1",
        "5 0 15 0 1 15 0 1 1 0 1 1 0 1 15 0 1",
        "5 0 17 0 1 17 0 1 14 0 1 1 0 1 17 0 1",
        "5 0 16 0 1 16 0 1 4 0 1 14 0 1 16 0 1",
        "5 2 3 0 1 7 8 1 4 0 1 0 0 1 2 0 1 6 8 1 4 0 3",
        "5 2 2 0 1 4 0 1 1 0 1 2 0 1 7 8 1 6 8 1 4 0 4",
        "5 2 7 8 1 16 0 1 9 0 1 2 0 1 4 0 1 6 8 1 4 0 2",
        "5 0 0 0 1 17 0 1 1 0 1 5 0 1 17 0 1",
        "5 0 0 0 1 3 0 1 9 0 1 4 0 1 0 0 1",
        "5 0 0 0 1 6 0 1 3 0 1 15 0 1 0 0 1",
        "5 0 0 0 1 0 0 1 1 0 1 0 0 1 0 0 1",
        "5 0 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1",
        "5 0 0 0 1 0 0 1 4 0 1 0 0 1 0 0 1",
        "5 0 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1",
        "5 0 0 0 1 0 0 1 1 0 1 0 0 1 0 0 1",
        "5 0 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1",
        "5 0 0 0 1 0 0 1 3 0 1 0 0 1 0 0 1",
        "5 0 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1",
        "5 0 0 0 1 0 0 1 3 0 1 0 0 1 0 0 1",
        "5 0 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1",
        "5 0 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1",
        "5 0 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1",
        "1 6 5 0 4 6 8 1 1 0 1 1 0 1 1 0 1 1 0 1 3 0 5",
        "5 0 15 0 1 4 0 1 4 0 1 4 0 1 4 0 1",
        "5 1 17 0 1 4 0 1 4 0 1 1 0 1 1 0 1 6 0 2",
        "5 0 16 0 1 1 0 1 4 0 1 1 0 1 1 0 1",
        "5 0 1 0 1 1 0 1 4 0 1 1 0 1 9 0 1",
        "5 0 15 0 1 1 0 1 1 0 1 1 0 1 1 0 1",
        "5 0 17 0 1 1 0 1 9 0 1 9 0 1 9 0 1",
        "5 0 16 0 1 9 0 1 3 0 1 1 0 1 4 0 1",
        "5 0 4 0 1 3 0 1 9 0 1 9 0 1 9 0 1",
        "5 0 15 0 1 4 0 1 1 0 1 4 0 1 4 0 1",
        "5 0 17 0 1 4 0 1 9 0 1 9 0 1 4 0 1",
        "5 0 16 0 1 4 0 1 1 0 1 4 0 1 9 0 1",
        "5 0 2 0 1 2 0 1 9 0 1 4 0 1 10 0 1",
        "5 0 15 0 1 3 0 1 3 0 1 9 0 1 8 0 1",
        "5 0 17 0 1 2 0 1 9 0 1 10 0 1 9 0 1",
        "5 0 16 0 1 2 0 1 2 0 1 8 0 1 1 0 1",
        "5 0 3 0 1 9 0 1 9 0 1 9 0 1 9 0 1",
        "5 2 7 8 4 1 0 1 4 0 1 3 0 1 10 0 1 6 8 4 5 10 1",
        "5 0 5 10 1 1 0 1 4 0 1 9 0 1 8 0 1",
        "5 0 1 0 1 4 0 1 9 0 1 4 0 1 9 0 1",
        "5 0 1 0 1 9 0 1 1 0 1 4 0 1 3 0 1",
        "5 0 7 10 1 4 0 1 9 0 1 0 0 1 2 0 1",
        "5 0 17 0 1 0 0 1 0 0 1 0 0 1 9 0 1",
        "5 0 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1",
        "1 6 5 0 3 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 3 0 5",
        "6 0 4 0 1 4 0 1 4 0 1 4 0 1 4 0 1 4 0 1",
        "6 1 15 0 1 4 0 1 4 0 1 1 0 1 4 0 1 4 0 1 6 0 2",
        "6 0 17 0 1 4 0 1 4 0 1 1 0 1 4 0 1 4 0 1",
        "6 0 16 0 1 1 0 1 1 0 1 1 0 1 4 0 1 1 0 1",
        "6 0 1 0 1 9 0 1 1 0 1 1 0 1 1 0 1 1 0 1",
        "6 0 15 0 1 4 0 1 1 0 1 9 0 1 9 0 1 1 0 1",
        "6 0 17 0 1 9 0 1 1 0 1 1 0 1 10 0 1 1 0 1",
        "6 0 16 0 1 2 0 1 9 0 1 9 0 1 8 0 1 9 0 1",
        "6 0 3 0 1 9 0 1 10 0 1 4 0 1 9 0 1 10 0 1",
        "6 0 1 0 1 4 0 1 8 0 1 9 0 1 1 0 1 8 0 1",
        "6 0 15 0 1 9 0 1 9 0 1 2 0 1 9 0 1 9 0 1",
        "6 0 17 0 1 3 0 1 1 0 1 9 0 1 10 0 1 2 0 1",
        "6 0 16 0 1 3 0 1 9 0 1 2 0 1 8 0 1 9 0 1",
        "6 0 2 0 1 3 0 1 3 0 1 9 0 1 9 0 1 2 0 1",
        "6 0 2 0 1 3 0 1 3 0 1 0 0 1 1 0 1 9 0 1",
        "6 2 7 8 3 1 0 1 3 0 1 0 0 1 9 0 1 4 0 1 6 8 3 5 10 1",
        "6 0 16 0 1 17 0 1 2 0 1 3 0 1 1 0 1 9 0 1",
        "6 1 7 8 1 2 0 1 2 0 1 2 0 1 9 0 1 3 0 1 6 8 1",
        "6 0 17 0 1 17 0 1 2 0 1 2 0 1 0 0 1 3 0 1",
        "6 0 1 0 1 0 0 1 2 0 1 5 10 1 0 0 1 3 0 1",
        "6 0 16 0 1 0 0 1 6 0 1 4 0 1 0 0 1 2 0 1",
        "6 0 17 0 1 0 0 1 0 0 1 4 0 1 0 0 1 2 0 1",
        "6 0 0 0 1 0 0 1 0 0 1 7 10 1 0 0 1 6 0 1",
        "1 6 5 0 5 1 0 1 1 0 1 1 0 1 1 0 1 3 0 5 3 1 3",
        "5 0 15 0 1 4 0 1 4 0 1 4 0 1 4 0 1",
        "5 0 17 0 1 4 0 1 4 0 1 4 0 1 4 0 1",
        "5 1 16 0 1 1 0 1 4 0 1 1 0 1 4 0 1 6 8 1",
        "5 1 1 0 1 17 0 1 1 0 1 1 0 1 4 0 1 3 3 1",
        "5 1 15 0 1 2 0 1 1 0 1 1 0 1 1 0 1 6 0 2",
        "5 0 17 0 1 17 0 1 1 0 1 9 0 1 1 0 1",
        "5 0 16 0 1 3 0 1 1 0 1 3 0 1 1 0 1",
        "5 0 4 0 1 1 0 1 1 0 1 1 0 1 9 0 1",
        "5 0 15 0 1 1 0 1 9 0 1 9 0 1 10 0 1",
        "5 0 17 0 1 17 0 1 10 0 1 2 0 1 8 0 1",
        "5 0 16 0 1 4 0 1 8 0 1 16 0 1 9 0 1",
        "5 1 2 0 1 4 0 1 9 0 1 17 0 1 1 0 1 4 0 1",
        "5 0 15 0 1 2 0 1 3 0 1 2 0 1 9 0 1",
        "5 1 17 0 1 2 0 1 9 0 1 2 0 1 10 0 1 4 0 1",
        "5 1 16 0 1 17 0 1 3 0 1 7 8 1 8 0 1 6 8 1",
        "5 1 4 0 1 4 0 1 3 0 1 0 0 1 9 0 1 4 0 1",
        "5 0 15 0 1 0 0 1 2 0 1 0 0 1 2 0 1",
        "5 1 17 0 1 0 0 1 2 0 1 0 0 1 2 0 1 4 0 1",
        "5 0 16 0 1 0 0 1 2 0 1 0 0 1 2 0 1",
        "5 1 3 0 1 0 0 1 2 0 1 0 0 1 9 0 1 4 0 1",
        "5 0 3 0 1 0 0 1 6 0 1 0 0 1 0 0 1",
        "5 3 7 8 5 0 0 1 0 0 1 0 0 1 0 0 1 6 8 4 4 0 1 3 3 3",
        "5 0 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1",
        "1 5 5 0 5 6 8 1 1 0 1 1 0 1 1 0 1 3 0 4",
        "4 2 4 0 1 4 0 1 4 0 1 4 0 1 1 0 1 1 0 1",
        "6 0 15 0 1 5 0 4 4 0 1 4 0 1 4 0 1 4 0 1",
        "6 2 17 0 1 15 0 1 1 0 1 4 0 1 4 0 1 4 0 1 6 0 2 3 3 1",
        "6 0 16 0 1 17 0 1 1 0 1 1 0 1 4 0 1 1 0 1",
        "6 0 4 0 1 16 0 1 1 0 1 1 0 1 4 0 1 1 0 1",
        "6 0 15 0 1 1 0 1 9 0 1 9 0 1 4 0 1 1 0 1",
        "6 0 17 0 1 15 0 1 1 0 1 4 0 1 9 0 1 1 0 1",
        "6 0 16 0 1 17 0 1 1 0 1 4 0 1 3 0 1 1 0 1",
        "6 0 3 0 1 16 0 1 9 0 1 9 0 1 9 0 1 9 0 1",
        "6 0 3 0 1 1 0 1 10 0 1 10 0 1 1 0 1 3 0 1",
        "6 2 7 8 1 15 0 1 8 3 1 8 3 1 9 0 1 9 0 1 6 8 1 3 3 1",
        "6 0 1 0 1 17 0 1 9 0 1 9 0 1 1 0 1 4 0 1",
        "6 0 1 0 1 16 0 1 2 0 1 1 0 1 9 0 1 4 0 1",
        "6 0 1 0 1 4 0 1 9 0 1 9 0 1 1 0 1 2 0 1",
        "6 0 1 0 1 2 0 1 3 0 1 10 0 1 9 0 1 3 0 1",
        "6 0 9 0 1 15 0 1 9 0 1 8 3 1 10 0 1 9 0 1",
        "6 0 4 0 1 17 0 1 2 0 1 9 0 1 8 3 1 4 0 1",
        "6 0 9 0 1 16 0 1 9 0 1 1 0 1 9 0 1 4 0 1",
        "6 0 3 0 1 3 0 1 3 0 1 9 0 1 1 0 1 0 0 1",
        "6 0 2 0 1 2 0 1 2 0 1 0 0 1 9 0 1 0 0 1",
        "6 2 9 0 1 7 8 4 2 0 1 0 0 1 4 0 1 0 0 1 6 8 4 3 3 2",
        "6 0 0 0 1 0 0 1 6 0 1 0 0 1 9 0 1 0 0 1",
        "6 0 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1",
        "1 10 4 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 3 0 2 3 1 1 3 3 1",
        "8 3 1 0 1 5 0 1 4 0 1 0 0 1 4 0 1 5 0 5 0 0 1 4 0 1 6 8 1 1 0 1 3 3 1",
        "9 0 10 0 1 5 0 3 4 0 1 0 0 1 4 0 1 4 0 1 4 0 1 0 0 1 4 0 1",
        "9 0 2 0 1 15 0 1 4 0 1 0 0 1 4 0 1 15 0 1 4 0 1 0 0 1 4 0 1",
        "9 0 10 0 1 17 0 1 4 0 1 0 0 1 4 0 1 17 0 1 1 0 1 0 0 1 4 0 1",
        "9 0 3 0 1 16 0 1 1 0 1 0 0 1 1 0 1 16 0 1 1 0 1 0 0 1 1 0 1",
        "9 7 7 7 10 7 8 1 1 0 1 0 0 1 9 0 1 4 0 1 9 0 1 0 0 1 1 0 1 6 7 10 6 8 1 4 0 2 3 3 2 2 0 1 5 10 2 4 8 1",
        "9 2 3 0 1 1 0 1 3 0 1 3 0 1 3 0 1 15 0 1 3 0 1 3 0 1 3 0 1 6 8 1 4 8 1",
        "9 2 5 10 1 15 0 1 3 0 1 1 0 1 3 0 1 17 0 1 3 0 1 3 0 1 3 0 1 6 8 1 4 0 2",
        "9 0 5 0 1 17 0 1 3 0 1 5 10 1 3 0 1 16 0 1 1 0 1 3 0 1 3 0 1",
        "9 1 1 0 1 16 0 1 3 0 1 5 0 1 3 0 1 3 0 1 1 0 1 1 0 1 3 0 1 4 0 1",
        "9 0 14 0 1 1 0 1 14 0 1 14 0 1 3 0 1 3 0 1 8 0 1 1 0 1 1 0 1",
        "9 2 7 10 1 15 0 1 1 0 1 7 10 1 14 0 1 7 8 1 9 0 1 1 0 1 1 0 1 6 8 1 4 0 3",
        "9 1 15 0 1 17 0 1 8 3 1 15 0 1 3 0 1 7 8 1 4 0 1 14 0 1 8 3 1 6 8 1",
        "9 1 17 0 1 16 0 1 9 0 1 17 0 1 14 0 1 4 0 1 9 0 1 3 0 1 9 0 1 4 0 2",
        "9 0 4 0 1 4 0 1 4 0 1 3 0 1 3 0 1 4 0 1 4 0 1 1 0 1 1 0 1",
        "9 0 4 0 1 2 0 1 9 0 1 1 0 1 8 3 1 4 0 1 9 0 1 8 0 1 8 0 1",
        "9 0 4 0 1 15 0 1 4 0 1 14 0 1 9 0 1 1 0 1 4 0 1 9 0 1 9 0 1",
        "9 0 9 0 1 17 0 1 9 0 1 3 0 1 3 0 1 1 0 1 4 0 1 2 0 1 3 0 1",
        "9 0 4 0 1 16 0 1 4 0 1 8 3 1 8 3 1 9 0 1 9 0 1 8 3 1 8 0 1",
        "9 0 9 0 1 3 0 1 4 0 1 9 0 1 9 0 1 3 0 1 10 0 1 9 0 1 9 0 1",
        "9 1 4 0 1 2 0 1 4 0 1 3 0 1 0 0 1 9 0 1 4 0 1 3 0 1 3 0 1 6 0 9",
        "9 1 2 0 1 7 8 3 9 0 1 8 3 1 0 0 1 1 0 1 9 0 1 8 3 1 8 0 1 6 8 2",
        "9 1 9 0 1 0 0 1 10 0 1 9 0 1 0 0 1 9 0 1 10 0 1 9 0 1 9 0 1 6 8 1",
        "1 9 5 0 1 6 7 2 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 3 0 4 3 3 4",
        "7 3 4 0 1 4 0 1 1 0 1 1 0 1 5 0 1 4 0 1 1 0 1 1 0 1 1 0 1 5 10 1",
        "9 0 4 0 1 5 0 1 5 0 1 5 0 1 4 0 1 5 0 1 5 0 1 4 0 1 4 0 1",
        "9 0 15 0 1 4 0 1 1 0 1 15 0 1 1 0 1 1 0 1 15 0 1 4 0 1 4 0 1",
        "9 0 17 0 1 15 0 1 1 0 1 17 0 1 15 0 1 15 0 1 17 0 1 1 0 1 4 0 1",
        "9 0 16 0 1 17 0 1 15 0 1 16 0 1 17 0 1 17 0 1 16 0 1 1 0 1 4 0 1",
        "9 2 3 0 1 16 0 1 17 0 1 7 8 1 16 0 1 16 0 1 7 8 1 1 0 1 4 0 1 6 8 2 4 8 1",
        "9 1 3 0 1 3 0 1 16 0 1 5 10 1 3 0 1 2 0 1 3 0 1 1 0 1 1 0 1 6 8 1",
        "9 2 7 8 1 7 8 1 2 0 1 3 0 1 2 0 1 7 8 1 3 0 1 1 0 1 1 0 1 6 8 3 5 10 1",
        "9 1 4 0 1 1 0 1 2 0 1 7 10 1 7 8 1 4 0 1 3 0 1 9 0 1 9 0 1 6 8 1",
        "9 0 4 0 1 1 0 1 7 8 1 17 0 1 3 0 1 1 0 1 3 0 1 4 0 1 1 0 1",
        "9 0 1 0 1 1 0 1 4 0 1 4 0 1 3 0 1 1 0 1 3 0 1 8 3 1 9 0 1",
        "9 0 9 0 1 9 0 1 4 0 1 5 10 1 3 0 1 9 0 1 1 0 1 9 0 1 1 0 1",
        "9 0 4 0 1 1 0 1 4 0 1 1 0 1 3 0 1 4 0 1 8 3 1 2 0 1 8 0 1",
        "9 0 9 0 1 9 0 1 1 0 1 1 0 1 1 0 1 9 0 1 9 0 1 9 0 1 9 0 1",
        "9 0 2 0 1 3 0 1 3 0 1 7 10 1 1 0 1 4 0 1 1 0 1 3 0 1 1 0 1",
        "9 0 9 0 1 9 0 1 3 0 1 17 0 1 1 0 1 9 0 1 8 3 1 9 0 1 8 0 1",
        "9 0 4 0 1 3 0 1 1 0 1 3 0 1 8 3 1 3 0 1 9 0 1 3 0 1 9 0 1",
        "9 0 9 0 1 9 0 1 1 0 1 3 0 1 9 0 1 3 0 1 1 0 1 9 0 1 3 0 1",
        "9 0 0 0 1 3 0 1 1 0 1 4 0 1 4 0 1 3 0 1 8 0 1 1 0 1 0 0 1",
        "9 1 0 0 1 9 0 1 9 0 1 4 0 1 9 0 1 3 0 1 9 0 1 9 0 1 0 0 1 6 8 1",
        "9 0 0 0 1 3 0 1 0 0 1 2 0 1 0 0 1 2 0 1 1 0 1 0 0 1 0 0 1",
        "9 0 0 0 1 9 0 1 0 0 1 17 0 1 0 0 1 16 0 1 8 0 1 0 0 1 0 0 1",
        "9 0 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 17 0 1 9 0 1 0 0 1 0 0 1",
        "1 8 1 0 1 6 8 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 3 0 4 3 3 1",
        "6 5 10 0 1 5 0 5 5 0 4 3 0 1 3 0 1 3 0 1 1 0 1 1 0 1 1 0 1 1 0 1 3 3 1",
        "10 0 2 0 1 15 0 1 15 0 1 1 0 1 1 0 1 4 0 1 3 0 1 10 0 1 3 0 1 3 0 1",
        "10 6 7 6 6 17 0 1 17 0 1 1 0 1 1 0 1 1 0 1 3 0 1 7 6 6 3 0 1 1 0 1 6 6 12 1 0 1 4 0 3 3 3 2 5 10 1 5 11 2",
        "11 1 5 0 4 4 0 1 5 10 1 2 0 1 4 0 1 0 0 1 1 0 1 3 0 1 3 0 1 1 0 1 4 0 1 4 0 3",
        "11 0 1 0 1 15 0 1 3 0 1 5 11 2 1 0 1 0 0 1 1 0 1 3 0 1 1 0 1 1 0 1 4 0 1",
        "11 1 15 0 1 17 0 1 1 0 1 3 0 1 1 0 1 0 0 1 1 0 1 3 0 1 1 0 1 1 0 1 4 0 1 4 0 3",
        "11 0 17 0 1 16 0 1 7 10 1 3 0 1 1 0 1 0 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1",
        "11 1 16 0 1 1 0 1 17 0 1 7 11 1 9 0 1 0 0 1 9 0 1 9 0 1 1 0 1 9 0 1 9 0 1 4 0 3",
        "11 0 1 0 1 15 0 1 3 0 1 17 0 1 10 0 1 3 0 1 4 0 1 1 0 1 9 0 1 10 0 1 4 0 1",
        "11 1 15 0 1 17 0 1 3 0 1 4 0 1 8 3 1 2 0 1 9 0 1 9 0 1 10 0 1 8 3 1 9 0 1 4 0 3",
        "11 0 17 0 1 16 0 1 9 0 1 1 0 1 9 0 1 5 0 1 4 0 1 3 0 1 8 3 1 9 0 1 1 0 1",
        "11 1 16 0 1 3 0 1 2 0 1 1 0 1 4 0 1 3 0 1 9 0 1 9 0 1 9 0 1 4 0 1 9 0 1 4 0 3",
        "11 0 3 0 1 3 0 1 9 0 1 7 11 1 4 0 1 3 0 1 4 0 1 4 0 1 1 0 1 4 0 1 3 0 1",
        "11 1 15 0 1 3 0 1 3 0 1 17 0 1 9 0 1 15 0 1 4 0 1 4 0 1 9 0 1 9 0 1 3 0 1 4 0 3",
        "11 0 17 0 1 2 0 1 9 0 1 3 0 1 2 0 1 4 0 1 9 0 1 4 0 1 10 0 1 4 0 1 1 0 1",
        "11 0 16 0 1 15 0 1 1 0 1 4 0 1 9 0 1 4 0 1 2 0 1 4 0 1 8 3 1 4 0 1 3 0 1",
        "11 1 2 0 1 17 0 1 9 0 1 3 0 1 4 0 1 5 0 1 9 0 1 4 0 1 9 0 1 9 0 1 4 0 1 6 0 2",
        "11 0 15 0 1 16 0 1 1 0 1 4 0 1 4 0 1 3 0 1 2 0 1 9 0 1 3 0 1 4 0 1 4 0 1",
        "11 0 17 0 1 4 0 1 9 0 1 4 0 1 9 0 1 1 0 1 9 0 1 4 0 1 9 0 1 9 0 1 9 0 1",
        "11 1 16 0 1 7 8 3 1 0 1 0 0 1 4 0 1 1 0 1 2 0 1 4 0 1 10 0 1 0 0 1 2 0 1 6 8 3",
        "11 0 2 0 1 4 0 1 9 0 1 0 0 1 9 0 1 15 0 1 16 0 1 9 0 1 8 0 1 0 0 1 9 0 1",
        "11 1 7 8 4 16 0 1 4 0 1 0 0 1 2 0 1 0 0 1 17 0 1 2 0 1 9 0 1 0 0 1 0 0 1 6 8 4",
        "11 0 16 0 1 6 0 1 9 0 1 0 0 1 9 0 1 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1 0 0 1",
        "1 10 4 0 1 3 0 4 3 3 4 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1",
        "9 4 1 0 1 5 0 3 5 0 4 4 0 1 4 0 1 5 0 5 4 0 1 4 0 1 4 0 1 6 8 1 1 0 1 5 11 1 4 8 1",
        "10 2 3 0 1 4 0 1 15 0 1 4 0 1 4 0 1 15 0 1 3 0 1 4 0 1 4 0 1 4 0 1 6 8 1 4 0 3",
        "10 0 3 0 1 15 0 1 17 0 1 4 0 1 4 0 1 17 0 1 5 11 1 4 0 1 4 0 1 4 0 1",
        "10 1 3 0 1 17 0 1 16 0 1 4 0 1 4 0 1 16 0 1 3 0 1 1 0 1 1 0 1 1 0 1 4 0 3",
        "10 1 3 0 1 16 0 1 7 8 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 6 8 1",
        "10 1 3 0 1 1 0 1 3 0 1 1 0 1 1 0 1 15 0 1 1 0 1 1 0 1 9 0 1 10 0 1 4 0 3",
        "10 0 3 0 1 15 0 1 15 0 1 9 0 1 1 0 1 17 0 1 7 11 1 1 0 1 4 0 1 2 0 1",
        "10 1 1 0 1 17 0 1 17 0 1 1 0 1 9 0 1 16 0 1 17 0 1 9 0 1 9 0 1 10 0 1 4 0 3",
        "10 0 1 0 1 16 0 1 16 0 1 9 0 1 3 0 1 1 0 1 3 0 1 1 0 1 2 0 1 3 0 1",
        "10 3 9 0 1 4 0 1 1 0 1 1 0 1 9 0 1 15 0 1 9 0 1 9 0 1 9 0 1 7 7 8 6 7 8 4 0 3 5 11 1",
        "10 0 10 0 1 2 0 1 15 0 1 9 0 1 1 0 1 17 0 1 1 0 1 3 0 1 4 0 1 3 0 1",
        "10 1 8 0 1 15 0 1 17 0 1 10 0 1 9 0 1 16 0 1 9 0 1 9 0 1 9 0 1 3 0 1 4 0 3",
        "10 0 9 0 1 17 0 1 16 0 1 8 0 1 3 0 1 3 0 1 3 0 1 3 0 1 0 0 1 3 0 1",
        "10 1 1 0 1 16 0 1 3 0 1 9 0 1 2 0 1 15 0 1 9 0 1 9 0 1 0 0 1 3 0 1 4 0 3",
        "10 0 9 0 1 3 0 1 2 0 1 1 0 1 9 0 1 17 0 1 2 0 1 3 0 1 0 0 1 9 0 1",
        "10 0 10 0 1 3 0 1 15 0 1 9 0 1 1 0 1 16 0 1 9 0 1 9 0 1 0 0 1 4 0 1",
        "10 1 8 0 1 7 8 3 17 0 1 10 0 1 9 0 1 2 0 1 2 0 1 3 0 1 0 0 1 1 0 1 6 8 3",
        "10 0 9 0 1 3 0 1 16 0 1 8 0 1 3 0 1 15 0 1 9 0 1 9 0 1 0 0 1 9 0 1",
        "10 0 2 0 1 5 0 1 4 0 1 9 0 1 9 0 1 17 0 1 3 0 1 3 0 1 0 0 1 0 0 1",
        "10 0 2 0 1 3 0 1 4 0 1 0 0 1 3 0 1 16 0 1 9 0 1 9 0 1 0 0 1 0 0 1",
        "10 2 2 0 1 1 0 1 7 8 3 0 0 1 9 0 1 2 0 1 1 0 1 3 0 1 0 0 1 0 0 1 6 8 3 6 0 2",
        "10 1 2 0 1 1 0 1 0 0 1 0 0 1 3 0 1 7 8 5 9 0 1 9 0 1 0 0 1 0 0 1 6 8 5",
        "10 0 9 0 1 15 0 1 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1",
        "1 10 1 0 1 3 0 4 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1",
        "10 4 4 0 1 4 0 1 4 0 1 4 0 1 4 0 1 1 0 1 4 0 1 4 0 1 1 0 1 4 0 1 1 0 1 1 0 1 5 11 2 4 8 3",
        "12 2 4 0 1 4 0 1 1 0 1 4 0 1 4 0 1 1 0 1 4 0 1 4 0 1 5 0 5 4 0 1 4 0 1 4 0 1 6 8 3 4 0 5",
        "12 0 4 0 1 4 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 15 0 1 4 0 1 1 0 1 4 0 1",
        "12 1 9 0 1 4 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 17 0 1 9 0 1 5 0 5 1 0 1 4 0 1",
        "12 0 10 0 1 9 0 1 9 0 1 1 0 1 1 0 1 9 0 1 9 0 1 9 0 1 16 0 1 10 0 1 15 0 1 1 0 1",
        "12 0 3 0 1 10 0 1 10 0 1 9 0 1 1 0 1 10 0 1 10 0 1 10 0 1 1 0 1 3 0 1 17 0 1 1 0 1",
        "12 0 3 0 1 3 0 1 2 0 1 10 0 1 1 0 1 2 0 1 3 0 1 3 0 1 15 0 1 3 0 1 16 0 1 9 0 1",
        "12 0 3 0 1 3 0 1 2 0 1 3 0 1 9 0 1 2 0 1 2 0 1 3 0 1 17 0 1 3 0 1 1 0 1 10 0 1",
        "12 3 2 0 1 3 0 1 2 0 1 3 0 1 10 0 1 2 0 1 2 0 1 2 0 1 16 0 1 7 4 6 15 0 1 3 0 1 6 4 6 4 0 14 4 8 5",
        "12 2 7 4 6 3 0 1 7 4 6 2 0 1 3 0 1 2 0 1 7 4 6 7 4 6 3 0 1 5 0 3 17 0 1 2 0 1 6 4 24 4 0 5",
        "12 1 1 0 1 7 4 6 1 0 1 2 0 1 2 0 1 7 4 6 4 0 1 4 0 1 15 0 1 4 0 1 16 0 1 2 0 1 6 4 12",
        "12 2 1 0 1 5 11 1 1 0 1 7 4 6 2 0 1 4 0 1 4 0 1 4 0 1 17 0 1 15 0 1 1 0 1 2 0 1 6 4 6 4 0 5",
        "12 1 10 0 1 5 0 1 1 0 1 5 11 1 2 0 1 1 0 1 1 0 1 1 0 1 16 0 1 17 0 1 15 0 1 7 4 6 6 4 6",
        "12 1 2 0 1 4 0 1 1 0 1 5 0 1 2 0 1 1 0 1 14 0 1 1 0 1 2 0 1 16 0 1 17 0 1 5 11 1 4 0 5",
        "12 1 10 0 1 4 0 1 13 0 1 4 0 1 7 4 6 1 0 1 4 0 1 8 0 1 15 0 1 1 0 1 16 0 1 5 0 1 6 4 6",
        "12 1 2 0 1 4 0 1 3 0 1 1 0 1 0 0 1 8 0 1 8 0 1 9 0 1 17 0 1 15 0 1 3 0 1 1 0 1 4 0 5",
        "12 0 10 0 1 14 0 1 3 0 1 1 0 1 0 0 1 9 0 1 9 0 1 1 0 1 16 0 1 17 0 1 15 0 1 1 0 1",
        "12 2 7 6 12 7 11 1 3 0 1 14 0 1 0 0 1 1 0 1 1 0 1 9 0 1 3 0 1 16 0 1 17 0 1 1 0 1 6 6 12 6 8 5",
        "12 0 0 0 1 15 0 1 3 0 1 7 11 1 0 0 1 8 0 1 9 0 1 10 0 1 15 0 1 4 0 1 16 0 1 14 0 1",
        "12 0 0 0 1 17 0 1 9 0 1 15 0 1 0 0 1 9 0 1 10 0 1 8 0 1 17 0 1 2 0 1 3 0 1 7 11 1",
        "12 1 0 0 1 4 0 1 0 0 1 17 0 1 0 0 1 0 0 1 8 0 1 9 0 1 16 0 1 15 0 1 15 0 1 15 0 1 6 0 3",
        "12 0 0 0 1 8 0 1 0 0 1 0 0 1 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1 17 0 1 17 0 1 17 0 1",
        "12 0 0 0 1 9 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 16 0 1 16 0 1 0 0 1",
        "1 10 4 0 1 6 4 12 6 8 13 3 0 11 3 1 1 3 3 9 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1",
        "6 9 4 0 1 3 0 1 5 0 3 4 0 1 4 0 1 5 0 5 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 2 0 1 5 11 1 4 8 1",
        "12 2 10 0 1 3 0 1 3 0 1 8 3 1 8 3 1 4 0 1 4 0 1 5 0 5 2 0 1 4 0 1 5 11 1 3 0 1 6 8 1 4 0 3",
        "12 0 3 0 1 3 0 1 1 0 1 9 0 1 9 0 1 15 0 1 2 0 1 15 0 1 8 3 1 4 0 1 4 0 1 3 0 1",
        "12 1 3 0 1 1 0 1 15 0 1 4 0 1 4 0 1 17 0 1 2 0 1 17 0 1 9 0 1 4 0 1 4 0 1 3 0 1 4 0 3",
        "12 1 7 6 6 1 0 1 17 0 1 8 3 1 2 0 1 16 0 1 8 3 1 16 0 1 4 0 1 1 0 1 1 0 1 9 0 1 6 6 6",
        "12 1 4 0 1 9 0 1 16 0 1 9 0 1 8 3 1 1 0 1 9 0 1 1 0 1 2 0 1 1 0 1 7 11 1 3 0 1 4 0 3",
        "12 0 4 0 1 1 0 1 1 0 1 4 0 1 9 0 1 15 0 1 2 0 1 15 0 1 8 3 1 1 0 1 17 0 1 9 0 1",
        "12 1 4 0 1 1 0 1 15 0 1 8 3 1 4 0 1 17 0 1 8 3 1 17 0 1 9 0 1 9 0 1 4 0 1 1 0 1 4 0 3",
        "12 0 4 0 1 9 0 1 17 0 1 9 0 1 8 3 1 16 0 1 9 0 1 16 0 1 4 0 1 3 0 1 4 0 1 9 0 1",
        "12 1 9 0 1 4 0 1 16 0 1 2 0 1 9 0 1 4 0 1 2 0 1 1 0 1 8 3 1 3 0 1 9 0 1 1 0 1 4 0 3",
        "12 0 1 0 1 9 0 1 3 0 1 8 3 1 2 0 1 2 0 1 8 0 1 15 0 1 9 0 1 3 0 1 1 0 1 9 0 1",
        "12 1 1 0 1 4 0 1 2 0 1 9 0 1 2 0 1 15 0 1 9 0 1 17 0 1 4 0 1 16 0 1 9 0 1 1 0 1 4 0 3",
        "12 0 1 0 1 9 0 1 2 0 1 4 0 1 8 0 1 17 0 1 4 0 1 16 0 1 8 0 1 17 0 1 1 0 1 9 0 1",
        "12 1 1 0 1 2 0 1 15 0 1 8 0 1 9 0 1 16 0 1 8 0 1 1 0 1 9 0 1 2 0 1 9 0 1 1 0 1 4 0 3",
        "12 0 9 0 1 9 0 1 17 0 1 9 0 1 3 0 1 4 0 1 9 0 1 15 0 1 4 0 1 16 0 1 3 0 1 9 0 1",
        "12 0 10 0 1 3 0 1 16 0 1 1 0 1 8 3 1 15 0 1 4 0 1 17 0 1 8 0 1 17 0 1 9 0 1 10 0 1",
        "12 0 3 0 1 9 0 1 1 0 1 8 0 1 9 0 1 17 0 1 8 0 1 16 0 1 9 0 1 2 0 1 1 0 1 4 0 1",
        "12 0 3 0 1 3 0 1 9 0 1 9 0 1 0 0 1 16 0 1 9 0 1 4 0 1 2 0 1 16 0 1 9 0 1 9 0 1",
        "12 0 2 0 1 9 0 1 3 0 1 3 0 1 0 0 1 3 0 1 4 0 1 2 0 1 8 0 1 17 0 1 3 0 1 10 0 1",
        "12 0 9 0 1 3 0 1 9 0 1 1 0 1 0 0 1 1 0 1 8 0 1 15 0 1 9 0 1 3 0 1 9 0 1 0 0 1",
        "12 1 3 0 1 9 0 1 1 0 1 1 0 1 0 0 1 15 0 1 9 0 1 17 0 1 3 0 1 16 0 1 3 0 1 0 0 1 6 0 9",
        "12 0 1 0 1 0 0 1 9 0 1 1 0 1 0 0 1 4 0 1 0 0 1 16 0 1 8 0 1 17 0 1 2 0 1 0 0 1",
        "12 0 9 0 1 0 0 1 0 0 1 9 0 1 0 0 1 9 0 1 0 0 1 0 0 1 9 0 1 0 0 1 9 0 1 0 0 1",
        "1 10 1 0 1 3 0 9 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1",
        "10 1 4 0 1 5 0 5 5 0 5 4 0 1 4 0 1 5 0 5 3 0 1 4 0 1 4 0 1 2 0 1 6 8 14",
        "10 0 10 0 1 4 0 1 15 0 1 1 0 1 4 0 1 15 0 1 3 0 1 4 0 1 4 0 1 9 0 1",
        "10 0 3 0 1 15 0 1 17 0 1 10 0 1 4 0 1 17 0 1 3 0 1 4 0 1 4 0 1 4 0 1",
        "10 0 2 0 1 17 0 1 16 0 1 3 0 1 4 0 1 16 0 1 3 0 1 4 0 1 4 0 1 2 0 1",
        "10 1 7 7 4 16 0 1 1 0 1 7 7 4 4 0 1 1 0 1 1 0 1 1 0 1 4 0 1 9 0 1 6 7 8",
        "10 0 1 0 1 1 0 1 15 0 1 3 0 1 1 0 1 15 0 1 1 0 1 1 0 1 2 0 1 3 0 1",
        "10 0 10 0 1 15 0 1 17 0 1 5 0 2 1 0 1 17 0 1 1 0 1 1 0 1 2 0 1 9 0 1",
        "10 0 2 0 1 17 0 1 16 0 1 3 0 1 1 0 1 16 0 1 9 0 1 1 0 1 2 0 1 2 0 1",
        "10 0 10 0 1 16 0 1 1 0 1 15 0 1 1 0 1 1 0 1 10 0 1 1 0 1 2 0 1 9 0 1",
        "10 1 7 6 6 4 0 1 15 0 1 17 0 1 9 0 1 15 0 1 8 0 1 8 0 1 8 0 1 2 0 1 6 6 6",
        "10 0 4 0 1 15 0 1 17 0 1 16 0 1 10 0 1 17 0 1 9 0 1 9 0 1 9 0 1 2 0 1",
        "10 1 2 0 1 17 0 1 16 0 1 3 0 1 8 0 1 16 0 1 1 0 1 3 0 1 1 0 1 9 0 1 6 8 2",
        "10 0 9 0 1 16 0 1 3 0 1 15 0 1 9 0 1 1 0 1 8 0 1 3 0 1 9 0 1 4 0 1",
        "10 0 4 0 1 2 0 1 15 0 1 17 0 1 3 0 1 15 0 1 9 0 1 3 0 1 1 0 1 9 0 1",
        "10 0 9 0 1 15 0 1 17 0 1 16 0 1 3 0 1 17 0 1 4 0 1 9 0 1 9 0 1 4 0 1",
        "10 0 4 0 1 17 0 1 16 0 1 0 0 1 9 0 1 16 0 1 8 0 1 10 0 1 1 0 1 9 0 1",
        "10 0 4 0 1 16 0 1 2 0 1 0 0 1 10 0 1 4 0 1 9 0 1 8 0 1 9 0 1 4 0 1",
        "10 0 9 0 1 4 0 1 15 0 1 0 0 1 8 0 1 2 0 1 0 0 1 9 0 1 3 0 1 9 0 1",
        "10 0 1 0 1 15 0 1 17 0 1 0 0 1 9 0 1 15 0 1 0 0 1 2 0 1 2 0 1 1 0 1",
        "10 0 9 0 1 17 0 1 16 0 1 0 0 1 2 0 1 17 0 1 0 0 1 9 0 1 9 0 1 9 0 1",
        "10 1 0 0 1 16 0 1 0 0 1 0 0 1 9 0 1 16 0 1 0 0 1 0 0 1 0 0 1 3 0 1 6 0 9",
        "10 0 0 0 1 1 0 1 0 0 1 0 0 1 4 0 1 0 0 1 0 0 1 0 0 1 0 0 1 9 0 1",
        "10 0 0 0 1 9 0 1 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1",
        "1 10 5 0 5 6 8 17 3 0 9 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1",
        "9 2 4 0 1 5 0 5 4 0 1 4 0 1 5 0 5 4 0 1 4 0 1 4 0 1 5 0 5 1 0 1 1 0 1",
        "11 0 4 0 1 15 0 1 4 0 1 2 0 1 4 0 1 4 0 1 4 0 1 4 0 1 15 0 1 3 0 1 1 0 1",
        "11 0 10 0 1 17 0 1 4 0 1 2 0 1 15 0 1 1 0 1 2 0 1 4 0 1 17 0 1 3 0 1 1 0 1",
        "11 0 3 0 1 16 0 1 9 0 1 2 0 1 17 0 1 1 0 1 9 0 1 4 0 1 16 0 1 3 0 1 1 0 1",
        "11 0 3 0 1 1 0 1 2 0 1 9 0 1 16 0 1 1 0 1 2 0 1 1 0 1 1 0 1 1 0 1 9 0 1",
        "11 0 1 0 1 15 0 1 9 0 1 4 0 1 1 0 1 9 0 1 9 0 1 1 0 1 15 0 1 9 0 1 1 0 1",
        "11 0 1 0 1 17 0 1 4 0 1 9 0 1 15 0 1 10 0 1 3 0 1 9 0 1 17 0 1 3 0 1 9 0 1",
        "11 0 10 0 1 16 0 1 1 0 1 4 0 1 17 0 1 8 0 1 9 0 1 10 0 1 16 0 1 9 0 1 3 0 1",
        "11 0 2 0 1 1 0 1 1 0 1 4 0 1 16 0 1 9 0 1 4 0 1 8 0 1 1 0 1 1 0 1 9 0 1",
        "11 0 2 0 1 15 0 1 9 0 1 4 0 1 4 0 1 4 0 1 2 0 1 9 0 1 15 0 1 9 0 1 3 0 1",
        "11 1 7 6 6 17 0 1 10 0 1 9 0 1 15 0 1 2 0 1 9 0 1 3 0 1 17 0 1 1 0 1 9 0 1 6 6 6",
        "11 0 3 0 1 16 0 1 8 0 1 10 0 1 17 0 1 9 0 1 4 0 1 1 0 1 16 0 1 9 0 1 2 0 1",
        "11 0 3 0 1 3 0 1 9 0 1 8 0 1 16 0 1 10 0 1 9 0 1 1 0 1 1 0 1 0 0 1 9 0 1",
        "11 0 15 0 1 15 0 1 1 0 1 9 0 1 2 0 1 8 0 1 2 0 1 9 0 1 15 0 1 0 0 1 2 0 1",
        "11 0 17 0 1 17 0 1 9 0 1 3 0 1 15 0 1 9 0 1 9 0 1 3 0 1 17 0 1 0 0 1 9 0 1",
        "11 0 16 0 1 16 0 1 1 0 1 1 0 1 17 0 1 4 0 1 3 0 1 1 0 1 16 0 1 0 0 1 2 0 1",
        "11 0 3 0 1 2 0 1 9 0 1 9 0 1 16 0 1 9 0 1 9 0 1 9 0 1 4 0 1 0 0 1 9 0 1",
        "11 0 15 0 1 15 0 1 3 0 1 4 0 1 4 0 1 10 0 1 3 0 1 0 0 1 2 0 1 0 0 1 3 0 1",
        "11 0 17 0 1 17 0 1 1 0 1 9 0 1 15 0 1 8 0 1 9 0 1 0 0 1 15 0 1 0 0 1 9 0 1",
        "11 0 16 0 1 16 0 1 9 0 1 1 0 1 17 0 1 9 0 1 3 0 1 0 0 1 17 0 1 0 0 1 1 0 1",
        "11 1 0 0 1 1 0 1 3 0 1 9 0 1 16 0 1 1 0 1 9 0 1 0 0 1 16 0 1 0 0 1 9 0 1 6 0 9",
        "11 0 0 0 1 1 0 1 1 0 1 1 0 1 0 0 1 1 0 1 0 0 1 0 0 1 0 0 1 0 0 1 1 0 1",
        "11 0 0 0 1 9 0 1 9 0 1 9 0 1 0 0 1 9 0 1 0 0 1 0 0 1 0 0 1 0 0 1 9 0 1",
        "1 10 5 8 4 3 0 9 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1",
        "10 3 1 0 1 10 0 1 4 0 1 3 0 1 5 0 5 3 0 1 1 0 1 4 0 1 5 0 5 1 0 1 6 8 9 1 0 1 4 8 2",
        "11 2 4 0 1 7 6 6 9 0 1 1 0 1 15 0 1 3 0 1 1 0 1 9 0 1 10 0 1 10 0 1 1 0 1 6 6 6 6 8 1",
        "11 1 4 0 1 5 0 5 2 0 1 1 0 1 17 0 1 10 0 1 10 0 1 2 0 1 7 6 3 2 0 1 5 0 2 6 6 3",
        "11 1 4 0 1 15 0 1 9 0 1 10 0 1 16 0 1 4 0 1 2 0 1 9 0 1 4 0 1 7 6 6 3 0 1 6 6 6",
        "11 1 4 0 1 17 0 1 4 0 1 4 0 1 1 0 1 4 0 1 7 6 3 2 0 1 15 0 1 4 0 1 15 0 1 6 6 3",
        "11 1 11 0 1 16 0 1 4 0 1 2 0 1 15 0 1 7 7 6 4 0 1 9 0 1 17 0 1 4 0 1 17 0 1 6 7 6",
        "11 1 9 0 1 1 0 1 2 0 1 7 7 6 17 0 1 4 0 1 4 0 1 4 0 1 16 0 1 4 0 1 16 0 1 6 7 6",
        "11 0 1 0 1 15 0 1 9 0 1 4 0 1 16 0 1 4 0 1 2 0 1 4 0 1 1 0 1 2 0 1 3 0 1",
        "11 0 11 0 1 17 0 1 10 0 1 2 0 1 1 0 1 4 0 1 2 0 1 2 0 1 15 0 1 9 0 1 15 0 1",
        "11 0 9 0 1 16 0 1 8 0 1 2 0 1 15 0 1 4 0 1 9 0 1 9 0 1 17 0 1 4 0 1 17 0 1",
        "11 0 3 0 1 1 0 1 9 0 1 2 0 1 17 0 1 1 0 1 2 0 1 10 0 1 16 0 1 4 0 1 16 0 1",
        "11 0 1 0 1 15 0 1 2 0 1 2 0 1 16 0 1 9 0 1 9 0 1 8 0 1 4 0 1 2 0 1 3 0 1",
        "11 0 11 0 1 17 0 1 9 0 1 9 0 1 10 0 1 1 0 1 4 0 1 9 0 1 15 0 1 9 0 1 1 0 1",
        "11 0 9 0 1 16 0 1 10 0 1 4 0 1 1 0 1 9 0 1 1 0 1 2 0 1 17 0 1 10 0 1 1 0 1",
        "11 0 3 0 1 3 0 1 8 0 1 9 0 1 15 0 1 3 0 1 9 0 1 9 0 1 16 0 1 8 0 1 1 0 1",
        "11 0 1 0 1 15 0 1 9 0 1 1 0 1 17 0 1 9 0 1 1 0 1 10 0 1 2 0 1 9 0 1 1 0 1",
        "11 0 11 0 1 17 0 1 2 0 1 9 0 1 16 0 1 1 0 1 9 0 1 8 0 1 15 0 1 2 0 1 9 0 1",
        "11 0 9 0 1 16 0 1 9 0 1 0 0 1 4 0 1 9 0 1 4 0 1 9 0 1 17 0 1 9 0 1 3 0 1",
        "11 0 4 0 1 2 0 1 10 0 1 0 0 1 2 0 1 3 0 1 9 0 1 3 0 1 16 0 1 10 0 1 9 0 1",
        "11 0 4 0 1 15 0 1 8 0 1 0 0 1 15 0 1 9 0 1 1 0 1 9 0 1 4 0 1 8 0 1 2 0 1",
        "11 1 9 0 1 17 0 1 9 0 1 0 0 1 17 0 1 1 0 1 9 0 1 3 0 1 15 0 1 9 0 1 9 0 1 6 0 9",
        "11 0 2 0 1 16 0 1 4 0 1 0 0 1 16 0 1 9 0 1 0 0 1 9 0 1 17 0 1 2 0 1 0 0 1",
        "11 0 9 0 1 0 0 1 9 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 16 0 1 9 0 1 0 0 1",
        "1 10 5 0 5 6 6 3 3 0 11 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1",
        "9 4 4 0 1 5 8 5 1 0 1 1 0 1 2 0 1 4 0 1 1 0 1 1 0 1 4 0 1 1 0 1 1 0 1 1 0 1 4 8 4",
        "12 1 4 0 1 1 0 1 3 0 1 5 8 3 2 0 1 5 0 5 5 0 5 5 0 5 4 0 1 1 0 1 4 0 1 4 0 1 6 8 7",
        "12 0 4 0 1 1 0 1 3 0 1 3 0 1 2 0 1 4 0 1 15 0 1 15 0 1 10 0 1 5 0 2 1 0 1 4 0 1",
        "12 0 4 0 1 1 0 1 1 0 1 3 0 1 2 0 1 15 0 1 17 0 1 17 0 1 3 0 1 3 0 1 10 0 1 4 0 1",
        "12 0 1 0 1 11 0 1 1 0 1 1 0 1 2 0 1 17 0 1 16 0 1 16 0 1 3 0 1 15 0 1 1 0 1 4 0 1",
        "12 0 10 0 1 9 0 1 1 0 1 11 0 1 9 0 1 16 0 1 1 0 1 1 0 1 3 0 1 17 0 1 10 0 1 4 0 1",
        "12 0 1 0 1 3 0 1 1 0 1 9 0 1 10 0 1 1 0 1 15 0 1 15 0 1 1 0 1 16 0 1 3 0 1 9 0 1",
        "12 1 10 0 1 11 0 1 9 0 1 3 0 1 8 0 1 15 0 1 17 0 1 17 0 1 1 0 1 3 0 1 3 0 1 10 0 1 6 0 14",
        "12 0 3 0 1 9 0 1 4 0 1 2 0 1 9 0 1 17 0 1 16 0 1 16 0 1 10 0 1 15 0 1 3 0 1 8 0 1",
        "12 0 1 0 1 3 0 1 9 0 1 11 0 1 4 0 1 16 0 1 1 0 1 1 0 1 3 0 1 17 0 1 1 0 1 9 0 1",
        "12 0 10 0 1 2 0 1 4 0 1 9 0 1 9 0 1 4 0 1 15 0 1 15 0 1 2 0 1 16 0 1 10 0 1 1 0 1",
        "12 1 3 0 1 11 0 1 12 0 1 3 0 1 10 0 1 15 0 1 17 0 1 17 0 1 2 0 1 1 0 1 4 0 1 9 0 1 6 8 11",
        "12 0 1 0 1 9 0 1 8 0 1 11 0 1 8 0 1 17 0 1 16 0 1 16 0 1 10 0 1 1 0 1 2 0 1 1 0 1",
        "12 0 10 0 1 3 0 1 9 0 1 9 0 1 9 0 1 16 0 1 1 0 1 3 0 1 4 0 1 1 0 1 2 0 1 1 0 1",
        "12 2 3 0 1 11 0 1 4 0 1 1 0 1 4 0 1 2 0 1 15 0 1 15 0 1 7 6 15 9 0 1 7 7 14 1 0 1 6 6 15 6 7 14",
        "12 0 3 0 1 9 0 1 4 0 1 9 0 1 4 0 1 15 0 1 17 0 1 17 0 1 4 0 1 1 0 1 4 0 1 9 0 1",
        "12 0 2 0 1 2 0 1 4 0 1 1 0 1 4 0 1 17 0 1 16 0 1 16 0 1 4 0 1 9 0 1 4 0 1 3 0 1",
        "12 0 2 0 1 11 0 1 9 0 1 9 0 1 9 0 1 16 0 1 4 0 1 2 0 1 1 0 1 3 0 1 4 0 1 2 0 1",
        "12 0 2 0 1 9 0 1 4 0 1 1 0 1 10 0 1 4 0 1 2 0 1 15 0 1 1 0 1 9 0 1 4 0 1 9 0 1",
        "12 0 2 0 1 1 0 1 9 0 1 1 0 1 8 0 1 15 0 1 15 0 1 17 0 1 1 0 1 10 0 1 1 0 1 3 0 1",
        "12 1 7 3 8 1 0 1 10 0 1 9 0 1 9 0 1 17 0 1 17 0 1 16 0 1 9 0 1 8 0 1 9 0 1 9 0 1 6 3 8",
        "12 0 2 0 1 9 0 1 8 0 1 10 0 1 1 0 1 16 0 1 16 0 1 0 0 1 1 0 1 9 0 1 0 0 1 1 0 1",
        "12 0 9 0 1 3 0 1 9 0 1 8 0 1 9 0 1 0 0 1 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1 9 0 1",
        "1 10 3 0 1 3 0 9 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1",
        "10 4 5 0 5 10 0 1 1 0 1 3 0 1 4 0 1 1 0 1 1 0 1 1 0 1 5 0 5 5 8 3 1 0 1 1 0 1 1 0 1 4 8 1",
        "13 2 1 0 1 7 6 3 5 0 5 4 0 1 4 0 1 3 0 1 5 8 1 5 0 5 15 0 1 3 0 1 2 0 1 4 0 1 4 0 1 6 6 3 6 8 10",
        "13 0 1 0 1 4 0 1 4 0 1 4 0 1 4 0 1 3 0 1 4 0 1 15 0 1 17 0 1 3 0 1 9 0 1 4 0 1 9 0 1",
        "13 0 1 0 1 4 0 1 15 0 1 4 0 1 10 0 1 10 0 1 4 0 1 17 0 1 16 0 1 3 0 1 2 0 1 1 0 1 4 0 1",
        "13 0 10 0 1 4 0 1 17 0 1 1 0 1 3 0 1 1 0 1 4 0 1 16 0 1 1 0 1 3 0 1 9 0 1 1 0 1 9 0 1",
        "13 0 3 0 1 4 0 1 16 0 1 1 0 1 3 0 1 10 0 1 1 0 1 1 0 1 15 0 1 1 0 1 2 0 1 1 0 1 2 0 1",
        "13 0 10 0 1 1 0 1 1 0 1 1 0 1 1 0 1 3 0 1 1 0 1 15 0 1 17 0 1 11 0 1 9 0 1 1 0 1 9 0 1",
        "13 0 4 0 1 9 0 1 15 0 1 1 0 1 1 0 1 10 0 1 1 0 1 17 0 1 16 0 1 9 0 1 4 0 1 9 0 1 3 0 1",
        "13 0 2 0 1 3 0 1 17 0 1 1 0 1 10 0 1 2 0 1 1 0 1 16 0 1 1 0 1 1 0 1 9 0 1 10 0 1 9 0 1",
        "13 0 2 0 1 1 0 1 16 0 1 9 0 1 3 0 1 10 0 1 11 0 1 1 0 1 15 0 1 11 0 1 4 0 1 8 0 1 2 0 1",
        "13 0 2 0 1 9 0 1 4 0 1 10 0 1 1 0 1 2 0 1 9 0 1 15 0 1 17 0 1 9 0 1 9 0 1 9 0 1 9 0 1",
        "13 2 7 3 4 10 0 1 15 0 1 8 0 1 10 0 1 10 0 1 3 0 1 17 0 1 16 0 1 4 0 1 4 0 1 4 0 1 4 0 1 6 3 4 6 8 4",
        "13 0 3 0 1 8 0 1 17 0 1 9 0 1 2 0 1 3 0 1 9 0 1 16 0 1 10 0 1 1 0 1 9 0 1 2 0 1 9 0 1",
        "13 0 15 0 1 9 0 1 16 0 1 3 0 1 2 0 1 10 0 1 2 0 1 3 0 1 1 0 1 11 0 1 4 0 1 9 0 1 4 0 1",
        "13 0 17 0 1 4 0 1 2 0 1 3 0 1 2 0 1 4 0 1 9 0 1 15 0 1 15 0 1 9 0 1 9 0 1 4 0 1 9 0 1",
        "13 1 16 0 1 9 0 1 15 0 1 3 0 1 7 7 18 4 0 1 10 0 1 17 0 1 17 0 1 3 0 1 10 0 1 2 0 1 4 0 1 6 7 18",
        "13 0 3 0 1 1 0 1 17 0 1 3 0 1 1 0 1 4 0 1 8 0 1 16 0 1 16 0 1 9 0 1 8 0 1 9 0 1 9 0 1",
        "13 1 15 0 1 9 0 1 16 0 1 3 0 1 10 0 1 4 0 1 9 0 1 2 0 1 4 0 1 10 0 1 9 0 1 4 0 1 1 0 1 6 0 6",
        "13 1 17 0 1 10 0 1 4 0 1 3 0 1 3 0 1 7 3 12 4 0 1 15 0 1 2 0 1 8 0 1 3 0 1 2 0 1 9 0 1 6 3 12",
        "13 0 16 0 1 8 0 1 15 0 1 12 0 1 10 0 1 4 0 1 9 0 1 17 0 1 15 0 1 9 0 1 2 0 1 9 0 1 3 0 1",
        "13 0 0 0 1 9 0 1 17 0 1 8 0 1 2 0 1 2 0 1 0 0 1 16 0 1 17 0 1 0 0 1 9 0 1 0 0 1 9 0 1",
        "13 0 0 0 1 0 0 1 16 0 1 9 0 1 10 0 1 9 0 1 0 0 1 0 0 1 16 0 1 0 0 1 3 0 1 0 0 1 1 0 1",
        "13 1 0 0 1 0 0 1 0 0 1 0 0 1 7 6 9 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 9 0 1 0 0 1 9 0 1 6 6 9",
        "1 10 5 0 5 3 0 9 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1",
        "10 5 4 0 1 3 0 1 1 0 1 1 0 1 4 0 1 5 8 4 4 0 1 4 0 1 5 0 5 1 0 1 6 6 3 1 0 1 1 0 1 1 0 1 4 8 4",
        "13 0 4 0 1 3 0 1 5 0 5 5 0 5 4 0 1 1 0 1 4 0 1 4 0 1 4 0 1 1 0 1 1 0 1 4 0 1 4 0 1",
        "13 0 4 0 1 3 0 1 15 0 1 15 0 1 1 0 1 1 0 1 1 0 1 4 0 1 15 0 1 10 0 1 5 0 2 4 0 1 2 0 1",
        "13 0 4 0 1 9 0 1 17 0 1 17 0 1 10 0 1 1 0 1 1 0 1 4 0 1 17 0 1 3 0 1 3 0 1 4 0 1 2 0 1",
        "13 1 1 0 1 3 0 1 16 0 1 16 0 1 3 0 1 9 0 1 1 0 1 1 0 1 16 0 1 2 0 1 15 0 1 4 0 1 2 0 1 6 8 10",
        "13 0 10 0 1 9 0 1 1 0 1 1 0 1 3 0 1 1 0 1 9 0 1 1 0 1 1 0 1 2 0 1 17 0 1 9 0 1 2 0 1",
        "13 0 1 0 1 4 0 1 15 0 1 15 0 1 3 0 1 11 0 1 10 0 1 9 0 1 15 0 1 10 0 1 16 0 1 2 0 1 9 0 1",
        "13 0 10 0 1 1 0 1 17 0 1 17 0 1 3 0 1 9 0 1 8 0 1 10 0 1 17 0 1 4 0 1 3 0 1 2 0 1 4 0 1",
        "13 1 3 0 1 9 0 1 16 0 1 16 0 1 10 0 1 3 0 1 9 0 1 8 0 1 16 0 1 7 6 6 15 0 1 9 0 1 9 0 1 6 6 6",
        "13 0 1 0 1 1 0 1 1 0 1 1 0 1 3 0 1 11 0 1 4 0 1 9 0 1 4 0 1 4 0 1 17 0 1 10 0 1 4 0 1",
        "13 0 10 0 1 1 0 1 15 0 1 15 0 1 2 0 1 9 0 1 4 0 1 4 0 1 15 0 1 4 0 1 16 0 1 8 0 1 4 0 1",
        "13 0 1 0 1 10 0 1 17 0 1 17 0 1 10 0 1 3 0 1 1 0 1 2 0 1 17 0 1 4 0 1 1 0 1 9 0 1 9 0 1",
        "13 0 10 0 1 3 0 1 16 0 1 16 0 1 4 0 1 11 0 1 1 0 1 9 0 1 16 0 1 2 0 1 9 0 1 3 0 1 10 0 1",
        "13 0 3 0 1 2 0 1 1 0 1 3 0 1 4 0 1 9 0 1 9 0 1 10 0 1 2 0 1 2 0 1 1 0 1 9 0 1 8 0 1",
        "13 1 10 0 1 10 0 1 15 0 1 15 0 1 7 7 10 2 0 1 3 0 1 8 0 1 15 0 1 2 0 1 9 0 1 0 0 1 9 0 1 6 7 10",
        "13 0 3 0 1 2 0 1 17 0 1 17 0 1 4 0 1 11 0 1 3 0 1 9 0 1 17 0 1 2 0 1 3 0 1 0 0 1 4 0 1",
        "13 0 3 0 1 10 0 1 16 0 1 16 0 1 2 0 1 9 0 1 3 0 1 2 0 1 16 0 1 2 0 1 9 0 1 0 0 1 9 0 1",
        "13 1 2 0 1 4 0 1 4 0 1 2 0 1 9 0 1 4 0 1 3 0 1 2 0 1 10 0 1 9 0 1 1 0 1 0 0 1 3 0 1 6 0 6",
        "13 0 2 0 1 4 0 1 2 0 1 15 0 1 0 0 1 9 0 1 9 0 1 9 0 1 4 0 1 10 0 1 1 0 1 0 0 1 1 0 1",
        "13 0 2 0 1 4 0 1 15 0 1 17 0 1 0 0 1 0 0 1 4 0 1 0 0 1 15 0 1 8 0 1 9 0 1 0 0 1 9 0 1",
        "13 0 2 0 1 4 0 1 17 0 1 16 0 1 0 0 1 0 0 1 2 0 1 0 0 1 17 0 1 9 0 1 0 0 1 0 0 1 10 0 1",
        "13 1 7 3 10 2 0 1 16 0 1 0 0 1 0 0 1 0 0 1 9 0 1 0 0 1 16 0 1 1 0 1 0 0 1 0 0 1 8 0 1 6 3 10",
        "13 1 0 0 1 7 3 6 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1 9 0 1 6 3 6",
        "1 10 5 0 5 3 0 9 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1",
        "10 6 15 0 1 1 0 1 4 0 1 4 0 1 5 8 4 5 0 2 1 0 1 4 0 1 10 0 1 5 0 5 6 6 6 6 7 4 1 0 1 1 0 1 1 0 1 4 8 4",
        "13 0 4 0 1 1 0 1 9 0 1 2 0 1 4 0 1 3 0 1 5 0 4 4 0 1 5 0 5 15 0 1 4 0 1 4 0 1 10 0 1",
        "13 0 1 0 1 1 0 1 2 0 1 9 0 1 4 0 1 3 0 1 4 0 1 4 0 1 1 0 1 17 0 1 2 0 1 9 0 1 7 6 3",
        "13 0 10 0 1 1 0 1 9 0 1 4 0 1 4 0 1 1 0 1 15 0 1 9 0 1 15 0 1 16 0 1 2 0 1 5 8 1 3 0 1",
        "13 0 2 0 1 10 0 1 2 0 1 4 0 1 4 0 1 10 0 1 17 0 1 4 0 1 17 0 1 1 0 1 9 0 1 4 0 1 3 0 1",
        "13 1 10 0 1 2 0 1 9 0 1 9 0 1 1 0 1 3 0 1 16 0 1 9 0 1 16 0 1 15 0 1 2 0 1 11 0 1 3 0 1 6 6 3",
        "13 0 3 0 1 10 0 1 4 0 1 2 0 1 11 0 1 1 0 1 4 0 1 1 0 1 4 0 1 17 0 1 9 0 1 3 0 1 3 0 1",
        "13 1 7 7 6 3 0 1 9 0 1 2 0 1 9 0 1 10 0 1 4 0 1 1 0 1 15 0 1 16 0 1 4 0 1 5 8 2 1 0 1 6 7 6",
        "13 0 3 0 1 10 0 1 4 0 1 9 0 1 1 0 1 2 0 1 15 0 1 1 0 1 17 0 1 10 0 1 9 0 1 11 0 1 9 0 1",
        "13 0 3 0 1 1 0 1 9 0 1 10 0 1 11 0 1 10 0 1 17 0 1 9 0 1 16 0 1 1 0 1 2 0 1 2 0 1 1 0 1",
        "13 0 3 0 1 10 0 1 10 0 1 8 0 1 9 0 1 2 0 1 16 0 1 3 0 1 1 0 1 15 0 1 9 0 1 11 0 1 9 0 1",
        "13 0 15 0 1 3 0 1 8 0 1 9 0 1 3 0 1 10 0 1 3 0 1 1 0 1 15 0 1 16 0 1 10 0 1 1 0 1 1 0 1",
        "13 0 17 0 1 10 0 1 9 0 1 3 0 1 1 0 1 3 0 1 3 0 1 9 0 1 17 0 1 4 0 1 8 0 1 5 8 2 9 0 1",
        "13 1 16 0 1 2 0 1 1 0 1 3 0 1 11 0 1 10 0 1 3 0 1 4 0 1 16 0 1 15 0 1 9 0 1 2 0 1 4 0 1 6 8 10",
        "13 0 4 0 1 10 0 1 9 0 1 2 0 1 9 0 1 4 0 1 3 0 1 4 0 1 4 0 1 17 0 1 4 0 1 2 0 1 9 0 1",
        "13 0 1 0 1 2 0 1 4 0 1 9 0 1 3 0 1 4 0 1 3 0 1 9 0 1 2 0 1 16 0 1 4 0 1 11 0 1 1 0 1",
        "13 0 1 0 1 10 0 1 9 0 1 1 0 1 1 0 1 4 0 1 15 0 1 1 0 1 15 0 1 10 0 1 4 0 1 3 0 1 9 0 1",
        "13 1 15 0 1 4 0 1 10 0 1 1 0 1 11 0 1 4 0 1 17 0 1 9 0 1 17 0 1 1 0 1 9 0 1 3 0 1 10 0 1 6 0 6",
        "13 1 17 0 1 4 0 1 8 0 1 1 0 1 9 0 1 7 3 10 16 0 1 10 0 1 16 0 1 15 0 1 10 0 1 3 0 1 8 0 1 6 3 10",
        "13 0 16 0 1 2 0 1 9 0 1 1 0 1 3 0 1 4 0 1 1 0 1 8 0 1 2 0 1 17 0 1 8 0 1 1 0 1 9 0 1",
        "13 0 10 0 1 2 0 1 1 0 1 5 8 2 9 0 1 16 0 1 15 0 1 9 0 1 15 0 1 16 0 1 9 0 1 1 0 1 3 0 1",
        "13 1 4 0 1 7 3 14 9 0 1 4 0 1 3 0 1 17 0 1 17 0 1 3 0 1 17 0 1 4 0 1 1 0 1 1 0 1 9 0 1 6 3 14",
        "13 0 17 0 1 0 0 1 0 0 1 2 0 1 9 0 1 1 0 1 16 0 1 9 0 1 16 0 1 9 0 1 9 0 1 1 0 1 0 0 1",
        "1 10 3 0 1 3 0 9 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1",
        "10 5 5 8 5 4 0 1 4 0 1 1 0 1 5 0 5 5 8 1 1 0 1 4 0 1 5 0 5 5 0 5 6 7 6 1 0 1 1 0 1 1 0 1 4 8 4",
        "13 0 1 0 1 4 0 1 4 0 1 4 0 1 4 0 1 3 0 1 3 0 1 2 0 1 15 0 1 15 0 1 4 0 1 4 0 1 1 0 1",
        "13 0 1 0 1 4 0 1 1 0 1 1 0 1 15 0 1 3 0 1 5 8 3 2 0 1 17 0 1 17 0 1 4 0 1 4 0 1 1 0 1",
        "13 0 1 0 1 1 0 1 1 0 1 1 0 1 17 0 1 1 0 1 3 0 1 2 0 1 16 0 1 16 0 1 4 0 1 4 0 1 1 0 1",
        "13 1 11 0 1 9 0 1 1 0 1 1 0 1 16 0 1 1 0 1 3 0 1 2 0 1 1 0 1 1 0 1 4 0 1 4 0 1 1 0 1 6 8 10",
        "13 1 9 0 1 1 0 1 9 0 1 10 0 1 1 0 1 1 0 1 1 0 1 9 0 1 15 0 1 15 0 1 4 0 1 1 0 1 1 0 1 6 6 6",
        "13 1 3 0 1 1 0 1 4 0 1 2 0 1 15 0 1 9 0 1 11 0 1 10 0 1 17 0 1 17 0 1 9 0 1 1 0 1 9 0 1 6 6 3",
        "13 0 11 0 1 9 0 1 4 0 1 2 0 1 17 0 1 3 0 1 9 0 1 8 0 1 16 0 1 16 0 1 10 0 1 1 0 1 4 0 1",
        "13 0 9 0 1 10 0 1 9 0 1 2 0 1 16 0 1 10 0 1 3 0 1 9 0 1 10 0 1 1 0 1 8 0 1 1 0 1 9 0 1",
        "13 1 3 0 1 1 0 1 10 0 1 7 7 4 4 0 1 3 0 1 2 0 1 4 0 1 1 0 1 15 0 1 9 0 1 9 0 1 10 0 1 6 7 4",
        "13 0 2 0 1 10 0 1 2 0 1 3 0 1 15 0 1 2 0 1 11 0 1 4 0 1 15 0 1 17 0 1 3 0 1 10 0 1 8 0 1",
        "13 0 11 0 1 3 0 1 9 0 1 5 0 2 17 0 1 10 0 1 9 0 1 9 0 1 17 0 1 16 0 1 3 0 1 8 0 1 9 0 1",
        "13 0 9 0 1 9 0 1 10 0 1 3 0 1 16 0 1 2 0 1 3 0 1 4 0 1 16 0 1 10 0 1 3 0 1 9 0 1 3 0 1",
        "13 0 3 0 1 10 0 1 3 0 1 15 0 1 2 0 1 11 0 1 11 0 1 9 0 1 1 0 1 3 0 1 3 0 1 3 0 1 3 0 1",
        "13 0 11 0 1 3 0 1 3 0 1 17 0 1 15 0 1 9 0 1 9 0 1 1 0 1 15 0 1 15 0 1 5 8 3 2 0 1 9 0 1",
        "13 1 9 0 1 3 0 1 3 0 1 16 0 1 17 0 1 10 0 1 1 0 1 9 0 1 17 0 1 17 0 1 4 0 1 9 0 1 3 0 1 6 6 9",
        "13 0 2 0 1 2 0 1 3 0 1 10 0 1 16 0 1 4 0 1 1 0 1 4 0 1 16 0 1 16 0 1 4 0 1 3 0 1 9 0 1",
        "13 1 11 0 1 2 0 1 2 0 1 3 0 1 10 0 1 4 0 1 1 0 1 9 0 1 4 0 1 2 0 1 11 0 1 1 0 1 3 0 1 6 0 6",
        "13 1 9 0 1 2 0 1 7 3 4 15 0 1 4 0 1 4 0 1 9 0 1 10 0 1 2 0 1 15 0 1 4 0 1 9 0 1 3 0 1 6 3 4",
        "13 0 0 0 1 2 0 1 4 0 1 17 0 1 15 0 1 4 0 1 10 0 1 8 0 1 15 0 1 17 0 1 11 0 1 3 0 1 9 0 1",
        "13 1 0 0 1 7 3 6 4 0 1 16 0 1 17 0 1 2 0 1 8 0 1 9 0 1 17 0 1 16 0 1 3 0 1 9 0 1 10 0 1 6 3 6",
        "13 1 0 0 1 0 0 1 4 0 1 0 0 1 16 0 1 7 3 6 9 0 1 1 0 1 16 0 1 0 0 1 3 0 1 1 0 1 8 0 1 6 3 6",
        "13 0 0 0 1 0 0 1 10 0 1 0 0 1 4 0 1 0 0 1 0 0 1 9 0 1 10 0 1 0 0 1 2 0 1 9 0 1 9 0 1",
        "1 10 5 0 5 3 0 9 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1",
        "10 4 3 0 1 1 0 1 5 8 5 1 0 1 5 0 5 3 0 1 5 8 2 4 0 1 5 0 5 5 0 2 1 0 1 1 0 1 1 0 1 4 8 4",
        "13 0 15 0 1 1 0 1 4 0 1 5 8 2 4 0 1 3 0 1 2 0 1 4 0 1 15 0 1 3 0 1 4 0 1 4 0 1 5 8 1",
        "13 0 17 0 1 1 0 1 2 0 1 3 0 1 15 0 1 1 0 1 2 0 1 1 0 1 17 0 1 15 0 1 4 0 1 4 0 1 4 0 1",
        "13 0 16 0 1 1 0 1 11 0 1 3 0 1 17 0 1 10 0 1 2 0 1 1 0 1 16 0 1 17 0 1 4 0 1 4 0 1 4 0 1",
        "13 1 10 0 1 10 0 1 9 0 1 3 0 1 16 0 1 3 0 1 11 0 1 1 0 1 10 0 1 16 0 1 4 0 1 4 0 1 4 0 1 6 8 10",
        "13 2 1 0 1 2 0 1 4 0 1 1 0 1 1 0 1 1 0 1 9 0 1 1 0 1 1 0 1 3 0 1 4 0 1 4 0 1 1 0 1 6 6 6 6 7 6",
        "13 2 15 0 1 10 0 1 11 0 1 1 0 1 15 0 1 10 0 1 4 0 1 9 0 1 15 0 1 15 0 1 1 0 1 2 0 1 1 0 1 6 6 6 6 7 2",
        "13 1 17 0 1 3 0 1 9 0 1 1 0 1 17 0 1 2 0 1 11 0 1 10 0 1 17 0 1 17 0 1 12 0 1 9 0 1 1 0 1 6 0 6",
        "13 0 16 0 1 10 0 1 4 0 1 11 0 1 16 0 1 10 0 1 9 0 1 8 0 1 16 0 1 16 0 1 8 0 1 2 0 1 1 0 1",
        "13 0 10 0 1 1 0 1 11 0 1 9 0 1 4 0 1 2 0 1 4 0 1 9 0 1 1 0 1 10 0 1 9 0 1 9 0 1 11 0 1",
        "13 0 1 0 1 10 0 1 9 0 1 3 0 1 15 0 1 10 0 1 9 0 1 1 0 1 15 0 1 3 0 1 3 0 1 10 0 1 9 0 1",
        "13 0 15 0 1 3 0 1 3 0 1 2 0 1 17 0 1 3 0 1 4 0 1 9 0 1 17 0 1 1 0 1 3 0 1 8 0 1 4 0 1",
        "13 2 17 0 1 10 0 1 2 0 1 11 0 1 16 0 1 10 0 1 9 0 1 10 0 1 16 0 1 1 0 1 2 0 1 9 0 1 9 0 1 6 6 9 6 7 4",
        "13 0 16 0 1 2 0 1 11 0 1 9 0 1 10 0 1 4 0 1 10 0 1 8 0 1 1 0 1 1 0 1 9 0 1 3 0 1 3 0 1",
        "13 0 3 0 1 10 0 1 9 0 1 2 0 1 2 0 1 4 0 1 8 0 1 9 0 1 15 0 1 1 0 1 4 0 1 9 0 1 2 0 1",
        "13 0 15 0 1 2 0 1 3 0 1 9 0 1 15 0 1 4 0 1 9 0 1 4 0 1 16 0 1 9 0 1 9 0 1 3 0 1 9 0 1",
        "13 0 17 0 1 10 0 1 11 0 1 4 0 1 17 0 1 4 0 1 2 0 1 2 0 1 4 0 1 4 0 1 1 0 1 3 0 1 4 0 1",
        "13 1 16 0 1 4 0 1 9 0 1 4 0 1 16 0 1 7 3 10 9 0 1 9 0 1 2 0 1 11 0 1 1 0 1 2 0 1 2 0 1 6 3 10",
        "13 0 2 0 1 4 0 1 3 0 1 4 0 1 4 0 1 4 0 1 10 0 1 10 0 1 15 0 1 4 0 1 1 0 1 2 0 1 9 0 1",
        "13 0 15 0 1 2 0 1 9 0 1 4 0 1 15 0 1 2 0 1 8 0 1 8 0 1 17 0 1 11 0 1 9 0 1 9 0 1 2 0 1",
        "13 0 17 0 1 2 0 1 1 0 1 4 0 1 17 0 1 9 0 1 9 0 1 9 0 1 16 0 1 4 0 1 10 0 1 4 0 1 9 0 1",
        "13 1 16 0 1 7 3 14 9 0 1 10 0 1 16 0 1 4 0 1 4 0 1 1 0 1 4 0 1 4 0 1 8 0 1 9 0 1 3 0 1 6 3 14",
        "13 0 10 0 1 5 8 1 0 0 1 1 0 1 0 0 1 9 0 1 9 0 1 9 0 1 9 0 1 2 0 1 9 0 1 0 0 1 9 0 1",
        "1 10 4 0 1 3 0 9 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1",
        "10 5 4 0 1 5 0 4 5 0 5 4 0 1 4 0 1 5 0 5 5 8 2 4 0 1 4 0 1 4 0 1 6 7 10 1 0 1 1 0 1 1 0 1 4 8 1",
        "13 0 2 0 1 4 0 1 15 0 1 2 0 1 2 0 1 15 0 1 3 0 1 4 0 1 3 0 1 4 0 1 3 0 1 3 0 1 4 0 1",
        "13 0 10 0 1 15 0 1 17 0 1 2 0 1 2 0 1 17 0 1 1 0 1 2 0 1 1 0 1 1 0 1 3 0 1 3 0 1 4 0 1",
        "13 0 4 0 1 17 0 1 16 0 1 10 0 1 2 0 1 16 0 1 1 0 1 2 0 1 1 0 1 1 0 1 3 0 1 3 0 1 10 0 1",
        "13 1 10 0 1 16 0 1 1 0 1 3 0 1 2 0 1 1 0 1 1 0 1 2 0 1 1 0 1 9 0 1 1 0 1 1 0 1 3 0 1 6 8 10",
        "13 2 2 0 1 4 0 1 15 0 1 10 0 1 9 0 1 15 0 1 9 0 1 2 0 1 10 0 1 10 0 1 9 0 1 1 0 1 10 0 1 6 6 6 6 7 2",
        "13 1 10 0 1 15 0 1 17 0 1 2 0 1 4 0 1 17 0 1 4 0 1 9 0 1 3 0 1 8 0 1 3 0 1 9 0 1 1 0 1 6 6 6",
        "13 0 3 0 1 17 0 1 16 0 1 10 0 1 9 0 1 16 0 1 9 0 1 10 0 1 16 0 1 9 0 1 9 0 1 4 0 1 10 0 1",
        "13 0 10 0 1 16 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 8 0 1 17 0 1 4 0 1 4 0 1 9 0 1 1 0 1",
        "13 0 2 0 1 4 0 1 15 0 1 1 0 1 10 0 1 15 0 1 11 0 1 9 0 1 10 0 1 2 0 1 1 0 1 1 0 1 1 0 1",
        "13 0 10 0 1 15 0 1 17 0 1 10 0 1 4 0 1 17 0 1 9 0 1 4 0 1 2 0 1 9 0 1 1 0 1 9 0 1 9 0 1",
        "13 0 3 0 1 17 0 1 16 0 1 1 0 1 9 0 1 16 0 1 3 0 1 4 0 1 16 0 1 10 0 1 1 0 1 3 0 1 4 0 1",
        "13 2 1 0 1 16 0 1 4 0 1 7 3 8 4 0 1 10 0 1 3 0 1 9 0 1 17 0 1 8 0 1 1 0 1 9 0 1 1 0 1 6 6 9 6 3 8",
        "13 0 10 0 1 3 0 1 4 0 1 5 8 1 1 0 1 1 0 1 2 0 1 10 0 1 3 0 1 9 0 1 9 0 1 1 0 1 10 0 1",
        "13 0 1 0 1 3 0 1 2 0 1 2 0 1 9 0 1 15 0 1 11 0 1 8 0 1 2 0 1 4 0 1 10 0 1 10 0 1 4 0 1",
        "13 0 10 0 1 3 0 1 15 0 1 2 0 1 4 0 1 17 0 1 9 0 1 9 0 1 16 0 1 1 0 1 8 0 1 3 0 1 10 0 1",
        "13 0 3 0 1 3 0 1 17 0 1 11 0 1 1 0 1 16 0 1 1 0 1 1 0 1 17 0 1 1 0 1 9 0 1 2 0 1 2 0 1",
        "13 2 10 0 1 3 0 1 16 0 1 0 0 1 9 0 1 4 0 1 9 0 1 9 0 1 4 0 1 9 0 1 4 0 1 10 0 1 10 0 1 6 8 14 6 0 24",
        "13 1 7 3 16 15 0 1 4 0 1 0 0 1 0 0 1 2 0 1 3 0 1 1 0 1 4 0 1 1 0 1 4 0 1 2 0 1 4 0 1 6 3 16",
        "13 0 0 0 1 17 0 1 15 0 1 0 0 1 0 0 1 15 0 1 3 0 1 1 0 1 4 0 1 9 0 1 9 0 1 10 0 1 2 0 1",
        "13 1 0 0 1 16 0 1 17 0 1 0 0 1 0 0 1 17 0 1 9 0 1 1 0 1 2 0 1 10 0 1 4 0 1 0 0 1 10 0 1 6 7 6",
        "13 0 0 0 1 10 0 1 16 0 1 0 0 1 0 0 1 16 0 1 2 0 1 9 0 1 2 0 1 8 0 1 4 0 1 0 0 1 2 0 1",
        "13 0 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 9 0 1 0 0 1 11 0 1 9 0 1 9 0 1 0 0 1 10 0 1",
        "1 10 5 0 5 3 0 9 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1",
        "10 5 15 0 1 1 0 1 5 8 4 1 0 1 5 0 5 3 0 1 2 0 1 4 0 1 4 0 1 5 0 5 6 7 4 1 0 1 1 0 1 1 0 1 4 8 4",
        "13 1 4 0 1 1 0 1 11 0 1 5 0 2 1 0 1 3 0 1 9 0 1 2 0 1 4 0 1 15 0 1 3 0 1 4 0 1 4 0 1 6 8 10",
        "13 0 15 0 1 1 0 1 9 0 1 3 0 1 15 0 1 1 0 1 4 0 1 2 0 1 1 0 1 17 0 1 3 0 1 1 0 1 4 0 1",
        "13 0 17 0 1 1 0 1 4 0 1 3 0 1 17 0 1 10 0 1 4 0 1 9 0 1 1 0 1 16 0 1 3 0 1 16 0 1 4 0 1",
        "13 0 16 0 1 10 0 1 11 0 1 15 0 1 16 0 1 3 0 1 9 0 1 2 0 1 1 0 1 10 0 1 1 0 1 17 0 1 4 0 1",
        "13 3 4 0 1 2 0 1 9 0 1 17 0 1 4 0 1 1 0 1 3 0 1 9 0 1 9 0 1 1 0 1 1 0 1 10 0 1 9 0 1 6 3 6 6 6 6 6 7 6",
        "13 3 4 0 1 10 0 1 4 0 1 16 0 1 15 0 1 10 0 1 9 0 1 4 0 1 4 0 1 15 0 1 1 0 1 1 0 1 1 0 1 6 3 6 6 6 6 6 7 2",
        "13 1 15 0 1 3 0 1 11 0 1 4 0 1 17 0 1 2 0 1 2 0 1 4 0 1 4 0 1 17 0 1 1 0 1 10 0 1 12 0 1 6 3 6",
        "13 0 17 0 1 10 0 1 9 0 1 1 0 1 16 0 1 10 0 1 9 0 1 9 0 1 9 0 1 16 0 1 9 0 1 1 0 1 8 0 1",
        "13 0 16 0 1 1 0 1 4 0 1 1 0 1 1 0 1 2 0 1 2 0 1 10 0 1 10 0 1 10 0 1 3 0 1 10 0 1 9 0 1",
        "13 1 3 0 1 10 0 1 11 0 1 15 0 1 15 0 1 10 0 1 9 0 1 8 0 1 8 0 1 1 0 1 1 0 1 4 0 1 1 0 1 6 0 1",
        "13 1 3 0 1 3 0 1 9 0 1 17 0 1 17 0 1 3 0 1 2 0 1 9 0 1 9 0 1 15 0 1 9 0 1 10 0 1 12 0 1 6 8 6",
        "13 2 3 0 1 10 0 1 2 0 1 16 0 1 16 0 1 10 0 1 9 0 1 1 0 1 3 0 1 17 0 1 10 0 1 4 0 1 8 0 1 6 3 18 6 6 9",
        "13 1 3 0 1 2 0 1 9 0 1 3 0 1 4 0 1 4 0 1 10 0 1 9 0 1 12 0 1 16 0 1 8 0 1 4 0 1 9 0 1 6 0 3",
        "13 0 3 0 1 10 0 1 4 0 1 3 0 1 2 0 1 4 0 1 8 0 1 4 0 1 8 0 1 4 0 1 9 0 1 2 0 1 3 0 1",
        "13 0 15 0 1 2 0 1 9 0 1 3 0 1 15 0 1 4 0 1 9 0 1 9 0 1 9 0 1 15 0 1 2 0 1 2 0 1 9 0 1",
        "13 0 17 0 1 10 0 1 10 0 1 9 0 1 17 0 1 4 0 1 3 0 1 10 0 1 3 0 1 17 0 1 9 0 1 10 0 1 1 0 1",
        "13 1 16 0 1 4 0 1 8 0 1 2 0 1 16 0 1 7 3 10 9 0 1 8 0 1 1 0 1 16 0 1 0 0 1 4 0 1 1 0 1 6 3 10",
        "13 0 1 0 1 4 0 1 9 0 1 9 0 1 2 0 1 0 0 1 0 0 1 9 0 1 12 0 1 1 0 1 0 0 1 2 0 1 9 0 1",
        "13 1 15 0 1 2 0 1 2 0 1 0 0 1 15 0 1 0 0 1 0 0 1 2 0 1 8 0 1 15 0 1 0 0 1 9 0 1 3 0 1 6 7 8",
        "13 0 17 0 1 2 0 1 9 0 1 0 0 1 17 0 1 0 0 1 0 0 1 9 0 1 9 0 1 17 0 1 0 0 1 0 0 1 3 0 1",
        "13 1 16 0 1 7 3 14 2 0 1 0 0 1 16 0 1 0 0 1 0 0 1 2 0 1 3 0 1 16 0 1 0 0 1 0 0 1 3 0 1 6 3 14",
        "13 0 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1 0 0 1 0 0 1 9 0 1 9 0 1 10 0 1 0 0 1 0 0 1 9 0 1",
        "1 10 5 0 5 6 7 11 6 8 14 3 0 9 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1",
        "8 6 4 0 1 5 0 5 4 0 1 1 0 1 5 0 5 4 0 1 4 0 1 4 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 4 8 4",
        "13 1 15 0 1 15 0 1 4 0 1 5 8 1 3 0 1 5 0 5 4 0 1 2 0 1 3 0 1 4 0 1 4 0 1 4 0 1 3 0 1 6 8 4",
        "13 0 17 0 1 17 0 1 4 0 1 3 0 1 3 0 1 15 0 1 2 0 1 2 0 1 3 0 1 4 0 1 4 0 1 4 0 1 3 0 1",
        "13 0 16 0 1 16 0 1 10 0 1 1 0 1 15 0 1 17 0 1 2 0 1 2 0 1 1 0 1 4 0 1 4 0 1 1 0 1 3 0 1",
        "13 1 1 0 1 1 0 1 3 0 1 1 0 1 17 0 1 16 0 1 2 0 1 2 0 1 1 0 1 4 0 1 2 0 1 1 0 1 1 0 1 6 8 2",
        "13 1 15 0 1 15 0 1 10 0 1 1 0 1 16 0 1 1 0 1 2 0 1 9 0 1 12 0 1 9 0 1 10 0 1 9 0 1 12 0 1 6 6 6",
        "13 1 17 0 1 17 0 1 3 0 1 1 0 1 10 0 1 15 0 1 9 0 1 10 0 1 8 0 1 10 0 1 4 0 1 3 0 1 8 0 1 6 6 6",
        "13 1 16 0 1 16 0 1 10 0 1 11 0 1 3 0 1 17 0 1 4 0 1 8 0 1 9 0 1 8 0 1 10 0 1 1 0 1 9 0 1 6 6 3",
        "13 0 4 0 1 1 0 1 2 0 1 9 0 1 15 0 1 16 0 1 9 0 1 9 0 1 1 0 1 9 0 1 4 0 1 9 0 1 1 0 1",
        "13 0 15 0 1 15 0 1 10 0 1 2 0 1 17 0 1 1 0 1 10 0 1 1 0 1 12 0 1 1 0 1 9 0 1 3 0 1 12 0 1",
        "13 0 17 0 1 17 0 1 3 0 1 12 0 1 16 0 1 15 0 1 8 0 1 10 0 1 8 0 1 1 0 1 1 0 1 3 0 1 8 0 1",
        "13 0 16 0 1 16 0 1 10 0 1 8 0 1 10 0 1 17 0 1 9 0 1 4 0 1 9 0 1 1 0 1 1 0 1 12 0 1 9 0 1",
        "13 1 2 0 1 10 0 1 2 0 1 9 0 1 3 0 1 16 0 1 4 0 1 10 0 1 3 0 1 1 0 1 9 0 1 8 0 1 1 0 1 6 6 6",
        "13 0 15 0 1 3 0 1 10 0 1 3 0 1 12 0 1 1 0 1 9 0 1 1 0 1 3 0 1 1 0 1 1 0 1 9 0 1 1 0 1",
        "13 0 17 0 1 15 0 1 1 0 1 9 0 1 8 0 1 15 0 1 1 0 1 10 0 1 10 0 1 9 0 1 9 0 1 1 0 1 9 0 1",
        "13 1 16 0 1 17 0 1 1 0 1 3 0 1 9 0 1 17 0 1 9 0 1 4 0 1 2 0 1 3 0 1 3 0 1 9 0 1 4 0 1 6 0 2",
        "13 0 10 0 1 16 0 1 10 0 1 3 0 1 3 0 1 16 0 1 10 0 1 10 0 1 10 0 1 10 0 1 3 0 1 4 0 1 9 0 1",
        "13 1 4 0 1 2 0 1 7 3 14 9 0 1 12 0 1 4 0 1 8 0 1 4 0 1 0 0 1 3 0 1 10 0 1 9 0 1 0 0 1 6 3 14",
        "13 0 15 0 1 15 0 1 0 0 1 10 0 1 8 0 1 2 0 1 9 0 1 9 0 1 0 0 1 2 0 1 4 0 1 10 0 1 0 0 1",
        "13 0 17 0 1 17 0 1 0 0 1 8 0 1 9 0 1 15 0 1 3 0 1 4 0 1 0 0 1 9 0 1 1 0 1 8 0 1 0 0 1",
        "13 0 16 0 1 16 0 1 0 0 1 9 0 1 0 0 1 17 0 1 9 0 1 9 0 1 0 0 1 0 0 1 9 0 1 9 0 1 0 0 1",
        "13 0 1 0 1 10 0 1 0 0 1 4 0 1 0 0 1 16 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 4 0 1 0 0 1",
        "13 0 9 0 1 0 0 1 0 0 1 10 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 9 0 1 0 0 1",
        "1 10 2 0 1 6 6 27 3 0 7 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1",
        "9 5 5 8 6 5 0 5 5 0 5 4 0 1 5 0 5 5 0 2 5 8 3 4 0 1 4 0 1 1 0 1 1 0 1 1 0 1 1 0 1 4 8 4",
        "13 0 9 0 1 15 0 1 15 0 1 3 0 1 4 0 1 3 0 1 2 0 1 4 0 1 1 0 1 4 0 1 4 0 1 4 0 1 4 0 1",
        "13 0 2 0 1 17 0 1 17 0 1 1 0 1 15 0 1 15 0 1 2 0 1 9 0 1 10 0 1 4 0 1 4 0 1 4 0 1 4 0 1",
        "13 0 11 0 1 16 0 1 16 0 1 5 8 2 17 0 1 17 0 1 11 0 1 4 0 1 2 0 1 4 0 1 4 0 1 4 0 1 1 0 1",
        "13 0 9 0 1 10 0 1 10 0 1 1 0 1 16 0 1 16 0 1 9 0 1 9 0 1 10 0 1 4 0 1 4 0 1 4 0 1 1 0 1",
        "13 3 4 0 1 1 0 1 1 0 1 1 0 1 1 0 1 3 0 1 2 0 1 3 0 1 3 0 1 4 0 1 9 0 1 9 0 1 1 0 1 6 3 6 6 7 6 6 8 9",
        "13 2 11 0 1 15 0 1 15 0 1 1 0 1 15 0 1 15 0 1 11 0 1 3 0 1 7 7 8 2 0 1 1 0 1 10 0 1 9 0 1 6 3 6 6 7 4",
        "13 2 9 0 1 17 0 1 17 0 1 1 0 1 17 0 1 17 0 1 9 0 1 3 0 1 1 0 1 2 0 1 1 0 1 8 0 1 10 0 1 6 3 6 6 7 6",
        "13 2 4 0 1 16 0 1 16 0 1 10 0 1 16 0 1 16 0 1 4 0 1 3 0 1 10 0 1 9 0 1 1 0 1 9 0 1 8 0 1 6 3 1 6 7 2",
        "13 1 11 0 1 1 0 1 10 0 1 11 0 1 4 0 1 3 0 1 11 0 1 3 0 1 1 0 1 10 0 1 9 0 1 1 0 1 9 0 1 6 7 18",
        "13 0 9 0 1 15 0 1 1 0 1 3 0 1 15 0 1 1 0 1 9 0 1 3 0 1 10 0 1 8 0 1 10 0 1 1 0 1 4 0 1",
        "13 0 4 0 1 17 0 1 15 0 1 3 0 1 17 0 1 1 0 1 4 0 1 3 0 1 3 0 1 9 0 1 8 0 1 9 0 1 9 0 1",
        "13 1 11 0 1 16 0 1 17 0 1 2 0 1 16 0 1 1 0 1 9 0 1 1 0 1 3 0 1 3 0 1 9 0 1 1 0 1 10 0 1 6 3 14",
        "13 0 9 0 1 1 0 1 16 0 1 10 0 1 2 0 1 12 0 1 4 0 1 1 0 1 10 0 1 3 0 1 1 0 1 9 0 1 8 0 1",
        "13 0 3 0 1 15 0 1 3 0 1 11 0 1 15 0 1 8 0 1 9 0 1 12 0 1 3 0 1 3 0 1 9 0 1 1 0 1 9 0 1",
        "13 0 2 0 1 17 0 1 15 0 1 1 0 1 17 0 1 9 0 1 10 0 1 8 0 1 2 0 1 2 0 1 3 0 1 9 0 1 2 0 1",
        "13 0 11 0 1 16 0 1 17 0 1 10 0 1 16 0 1 3 0 1 8 0 1 9 0 1 9 0 1 2 0 1 1 0 1 10 0 1 9 0 1",
        "13 1 9 0 1 4 0 1 16 0 1 4 0 1 4 0 1 1 0 1 9 0 1 1 0 1 3 0 1 9 0 1 9 0 1 8 0 1 4 0 1 6 0 9",
        "13 0 3 0 1 2 0 1 2 0 1 10 0 1 15 0 1 9 0 1 1 0 1 12 0 1 2 0 1 4 0 1 3 0 1 9 0 1 2 0 1",
        "13 0 11 0 1 15 0 1 15 0 1 4 0 1 17 0 1 4 0 1 9 0 1 8 0 1 9 0 1 9 0 1 9 0 1 3 0 1 9 0 1",
        "13 0 9 0 1 17 0 1 17 0 1 2 0 1 16 0 1 9 0 1 4 0 1 9 0 1 0 0 1 4 0 1 10 0 1 12 0 1 4 0 1",
        "13 0 0 0 1 16 0 1 16 0 1 9 0 1 0 0 1 0 0 1 1 0 1 0 0 1 0 0 1 4 0 1 8 0 1 8 0 1 9 0 1",
        "13 0 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1 9 0 1 9 0 1 9 0 1 0 0 1",
        "1 10 5 0 5 6 7 3 6 8 16 3 0 17 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1",
        "8 6 4 0 1 5 0 5 4 0 1 4 0 1 3 0 1 5 0 2 10 0 1 4 0 1 6 6 6 1 0 1 1 0 1 1 0 1 1 0 1 4 8 2",
        "12 1 15 0 1 4 0 1 4 0 1 2 0 1 5 0 5 3 0 1 7 3 2 4 0 1 3 0 1 1 0 1 4 0 1 4 0 1 6 8 2",
        "12 0 16 0 1 15 0 1 4 0 1 2 0 1 15 0 1 15 0 1 2 0 1 4 0 1 3 0 1 1 0 1 4 0 1 5 8 1",
        "12 1 1 0 1 17 0 1 4 0 1 2 0 1 17 0 1 17 0 1 10 0 1 1 0 1 1 0 1 1 0 1 1 0 1 4 0 1 6 8 1",
        "12 0 15 0 1 16 0 1 9 0 1 2 0 1 16 0 1 16 0 1 4 0 1 1 0 1 1 0 1 1 0 1 1 0 1 10 0 1",
        "12 2 17 0 1 1 0 1 3 0 1 9 0 1 1 0 1 10 0 1 10 0 1 1 0 1 1 0 1 1 0 1 1 0 1 11 0 1 6 3 6 6 6 6",
        "12 2 16 0 1 15 0 1 1 0 1 4 0 1 15 0 1 3 0 1 2 0 1 9 0 1 9 0 1 12 0 1 1 0 1 4 0 1 6 3 3 6 6 3",
        "12 0 4 0 1 17 0 1 1 0 1 4 0 1 17 0 1 15 0 1 10 0 1 10 0 1 3 0 1 8 1 1 9 0 1 10 0 1",
        "12 0 15 0 1 16 0 1 9 0 1 9 0 1 16 0 1 17 0 1 3 0 1 8 0 1 12 0 1 9 0 1 10 0 1 2 0 1",
        "12 0 17 0 1 1 0 1 10 0 1 10 0 1 1 0 1 16 0 1 10 0 1 9 0 1 8 1 1 3 0 1 8 0 1 10 0 1",
        "12 0 16 0 1 15 0 1 8 0 1 8 0 1 15 0 1 3 0 1 2 0 1 4 0 1 9 0 1 12 0 1 9 0 1 2 0 1",
        "12 0 2 0 1 17 0 1 9 0 1 9 0 1 17 0 1 1 0 1 10 0 1 1 0 1 2 0 1 8 1 1 3 0 1 10 0 1",
        "12 1 15 0 1 16 0 1 4 0 1 4 0 1 16 0 1 9 0 1 4 0 1 9 0 1 9 0 1 9 0 1 3 0 1 4 0 1 6 3 14",
        "12 1 17 0 1 1 0 1 1 0 1 9 0 1 10 0 1 3 0 1 10 0 1 10 0 1 3 0 1 3 0 1 9 0 1 9 0 1 6 6 9",
        "12 0 16 0 1 15 0 1 9 0 1 4 0 1 3 0 1 2 0 1 4 0 1 8 0 1 9 0 1 12 0 1 2 0 1 1 0 1",
        "12 1 10 0 1 17 0 1 10 0 1 9 0 1 15 0 1 9 0 1 9 0 1 9 0 1 3 0 1 8 1 1 10 0 1 10 0 1 6 0 7",
        "12 0 4 0 1 16 0 1 8 0 1 10 0 1 17 0 1 4 0 1 3 0 1 3 0 1 1 0 1 9 0 1 2 0 1 4 0 1",
        "12 1 15 0 1 4 0 1 9 0 1 8 1 1 16 0 1 9 0 1 2 0 1 3 0 1 9 0 1 3 0 1 2 0 1 9 0 1 6 0 6",
        "12 0 17 0 1 2 0 1 1 0 1 9 0 1 2 0 1 4 0 1 9 0 1 9 0 1 1 0 1 9 0 1 2 0 1 1 0 1",
        "12 1 16 0 1 15 0 1 9 0 1 1 0 1 15 0 1 1 0 1 0 0 1 3 0 1 9 0 1 10 0 1 7 7 3 1 0 1 6 7 3",
        "12 0 10 0 1 17 0 1 10 0 1 9 0 1 17 0 1 9 0 1 0 0 1 3 0 1 10 0 1 8 0 1 4 0 1 1 0 1",
        "12 0 2 0 1 16 0 1 8 0 1 0 0 1 16 0 1 0 0 1 0 0 1 9 0 1 8 1 1 9 0 1 17 0 1 9 0 1",
        "12 0 10 0 1 10 0 1 9 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1 0 0 1",
        "1 10 5 0 5 6 8 5 3 0 9 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1",
        "9 4 3 0 1 5 0 5 5 8 3 4 0 1 5 0 5 4 0 1 4 0 1 4 0 1 5 0 5 1 0 1 1 0 1 1 0 1 4 8 4",
        "12 1 15 0 1 4 0 1 11 0 1 2 0 1 4 0 1 1 0 1 9 0 1 2 0 1 15 0 1 3 0 1 4 0 1 5 0 2 6 8 4",
        "12 0 17 0 1 4 0 1 9 0 1 9 0 1 4 0 1 1 0 1 2 0 1 2 0 1 17 0 1 1 0 1 1 0 1 3 0 1",
        "12 0 16 0 1 15 0 1 4 0 1 2 0 1 1 0 1 1 0 1 9 0 1 9 0 1 16 0 1 1 0 1 1 0 1 15 0 1",
        "12 1 10 0 1 17 0 1 4 0 1 2 0 1 10 0 1 1 0 1 4 0 1 4 0 1 10 0 1 1 0 1 10 0 1 17 0 1 6 8 2",
        "12 3 1 0 1 16 0 1 11 0 1 9 0 1 3 0 1 9 0 1 9 0 1 9 0 1 1 0 1 1 0 1 17 0 1 16 0 1 6 3 6 6 6 6 6 7 6",
        "12 4 15 0 1 1 0 1 9 0 1 4 0 1 3 0 1 10 0 1 2 0 1 2 0 1 15 0 1 9 0 1 1 0 1 3 0 1 6 3 6 6 6 3 6 7 3 6 8 2",
        "12 2 17 0 1 15 0 1 4 0 1 9 0 1 3 0 1 8 0 1 9 0 1 2 0 1 16 0 1 10 0 1 10 0 1 15 0 1 6 3 6 6 0 6",
        "12 2 16 0 1 17 0 1 11 0 1 4 0 1 3 0 1 9 0 1 4 0 1 9 0 1 1 0 1 8 0 1 4 0 1 17 0 1 6 3 6 6 8 1",
        "12 2 10 0 1 16 0 1 9 0 1 9 0 1 10 0 1 4 0 1 9 0 1 10 0 1 15 0 1 9 0 1 1 0 1 16 0 1 6 7 9 6 8 1",
        "12 1 1 0 1 4 0 1 4 0 1 10 0 1 3 0 1 9 0 1 10 0 1 8 0 1 17 0 1 3 0 1 9 0 1 1 0 1 6 8 2",
        "12 1 15 0 1 15 0 1 1 0 1 8 0 1 2 0 1 4 0 1 8 0 1 9 0 1 16 0 1 3 0 1 3 0 1 1 0 1 6 0 7",
        "12 3 17 0 1 17 0 1 9 0 1 9 0 1 10 0 1 2 0 1 9 0 1 4 0 1 1 0 1 9 0 1 3 0 1 9 0 1 6 3 14 6 6 9 6 8 1",
        "12 0 16 0 1 16 0 1 1 0 1 4 0 1 4 0 1 9 0 1 1 0 1 4 0 1 15 0 1 3 0 1 9 0 1 10 0 1",
        "12 0 3 0 1 2 0 1 9 0 1 9 0 1 4 0 1 4 0 1 9 0 1 9 0 1 17 0 1 9 0 1 1 0 1 8 0 1",
        "12 1 15 0 1 15 0 1 10 0 1 4 0 1 7 7 9 2 0 1 4 0 1 10 0 1 16 0 1 10 0 1 9 0 1 9 0 1 6 7 9",
        "12 0 17 0 1 17 0 1 8 0 1 9 0 1 3 0 1 9 0 1 9 0 1 8 0 1 4 0 1 8 0 1 4 0 1 3 0 1",
        "12 0 16 0 1 16 0 1 9 0 1 10 0 1 3 0 1 1 0 1 10 0 1 9 0 1 2 0 1 9 0 1 4 0 1 9 0 1",
        "12 0 2 0 1 4 0 1 1 0 1 8 0 1 3 0 1 1 0 1 8 0 1 3 0 1 15 0 1 2 0 1 4 0 1 10 0 1",
        "12 0 15 0 1 15 0 1 9 0 1 9 0 1 9 0 1 9 0 1 9 0 1 9 0 1 17 0 1 9 0 1 9 0 1 8 0 1",
        "12 0 17 0 1 17 0 1 0 0 1 1 0 1 3 0 1 4 0 1 1 0 1 3 0 1 16 0 1 2 0 1 4 0 1 9 0 1",
        "12 0 16 0 1 1 0 1 0 0 1 9 0 1 9 0 1 9 0 1 9 0 1 3 0 1 4 0 1 9 0 1 2 0 1 2 0 1",
        "12 0 3 0 1 9 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 9 0 1 9 0 1 0 0 1 9 0 1 9 0 1",
        "1 10 4 0 1 6 6 15 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1",
        "10 5 10 0 1 5 0 4 5 0 6 2 0 1 4 0 1 5 0 7 4 0 1 2 0 1 4 0 1 4 0 1 6 3 10 6 7 3 1 0 1 1 0 1 4 8 2",
        "12 0 2 0 1 5 0 2 15 0 1 4 0 1 4 0 1 4 0 1 3 0 1 4 0 1 2 0 1 1 0 1 1 0 1 3 0 1",
        "12 0 10 0 1 15 0 1 17 0 1 2 0 1 4 0 1 15 0 1 3 0 1 10 0 1 10 0 1 10 0 1 1 0 1 3 0 1",
        "12 0 3 0 1 17 0 1 16 0 1 10 0 1 10 0 1 16 0 1 3 0 1 12 0 1 4 0 1 3 0 1 1 0 1 1 0 1",
        "12 0 10 0 1 16 0 1 1 0 1 12 0 1 12 0 1 4 0 1 3 0 1 8 0 1 2 0 1 3 0 1 10 0 1 9 0 1",
        "12 2 7 3 4 1 0 1 15 0 1 8 0 1 8 0 1 15 0 1 9 0 1 9 0 1 2 0 1 3 0 1 4 0 1 10 0 1 6 3 4 6 8 13",
        "12 0 1 0 1 15 0 1 17 0 1 9 0 1 9 0 1 17 0 1 10 0 1 4 0 1 10 0 1 1 0 1 4 0 1 8 0 1",
        "12 1 7 7 4 17 0 1 16 0 1 3 0 1 4 0 1 16 0 1 8 0 1 10 0 1 12 0 1 10 0 1 4 0 1 9 0 1 6 7 4",
        "12 0 4 0 1 16 0 1 1 0 1 10 0 1 10 0 1 10 0 1 9 0 1 12 0 1 4 0 1 4 0 1 9 0 1 3 0 1",
        "12 0 4 0 1 1 0 1 15 0 1 12 0 1 12 0 1 1 0 1 3 0 1 8 0 1 4 0 1 2 0 1 4 0 1 9 0 1",
        "12 0 4 0 1 15 0 1 17 0 1 8 0 1 8 0 1 15 0 1 9 0 1 9 0 1 9 0 1 2 0 1 9 0 1 10 0 1",
        "12 2 4 0 1 17 0 1 16 0 1 9 0 1 9 0 1 4 0 1 10 0 1 4 0 1 4 0 1 7 7 8 1 0 1 8 0 1 6 7 8 6 0 27",
        "12 0 9 0 1 16 0 1 3 0 1 2 0 1 4 0 1 2 0 1 8 1 1 10 0 1 2 0 1 1 0 1 9 0 1 9 0 1",
        "12 0 3 0 1 1 0 1 15 0 1 10 0 1 9 0 1 15 0 1 9 0 1 12 0 1 10 0 1 1 0 1 1 0 1 4 0 1",
        "12 0 1 0 1 15 0 1 2 0 1 12 0 1 10 0 1 3 0 1 1 0 1 8 0 1 1 0 1 1 0 1 9 0 1 1 0 1",
        "12 0 9 0 1 16 0 1 15 0 1 8 0 1 8 1 1 3 0 1 9 0 1 9 0 1 1 0 1 9 0 1 10 0 1 1 0 1",
        "12 0 4 0 1 4 0 1 16 0 1 9 0 1 9 0 1 3 0 1 1 0 1 3 0 1 9 0 1 10 0 1 3 0 1 9 0 1",
        "12 0 1 0 1 2 0 1 2 0 1 2 0 1 1 0 1 3 0 1 9 0 1 2 0 1 10 0 1 8 0 1 9 0 1 1 0 1",
        "12 0 9 0 1 15 0 1 15 0 1 9 0 1 1 0 1 3 0 1 10 0 1 10 0 1 0 0 1 9 0 1 3 0 1 9 0 1",
        "12 0 1 0 1 2 0 1 17 0 1 10 0 1 1 0 1 3 0 1 4 0 1 12 0 1 0 0 1 3 0 1 9 0 1 3 0 1",
        "12 1 1 0 1 15 0 1 16 0 1 0 0 1 1 0 1 15 0 1 1 0 1 8 1 1 0 0 1 1 0 1 2 0 1 9 0 1 6 6 3",
        "12 0 9 0 1 16 0 1 10 0 1 0 0 1 9 0 1 16 0 1 9 0 1 9 0 1 0 0 1 9 0 1 9 0 1 3 0 1",
        "12 0 10 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 10 0 1 0 0 1 0 0 1 0 0 1 4 0 1 10 0 1",
        "1 10 10 0 1 6 0 25 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1",
        "10 4 7 6 3 3 0 1 4 0 1 4 0 1 4 0 1 4 0 1 12 0 1 1 0 1 4 0 1 4 0 1 6 6 9 1 0 1 1 0 1 4 8 4",
        "12 2 1 0 1 1 0 1 4 0 1 4 0 1 4 0 1 4 0 1 2 0 1 4 0 1 3 0 1 3 0 1 4 0 1 4 0 1 6 1 2 6 8 15",
        "12 0 1 0 1 1 0 1 4 0 1 4 0 1 4 0 1 4 0 1 2 0 1 4 0 1 3 0 1 1 0 1 8 0 1 4 0 1",
        "12 0 10 0 1 1 0 1 4 0 1 4 0 1 10 0 1 1 0 1 2 0 1 1 0 1 3 0 1 1 0 1 9 0 1 2 0 1",
        "12 0 2 0 1 9 0 1 2 0 1 2 0 1 3 0 1 1 0 1 9 0 1 1 0 1 3 0 1 1 0 1 2 0 1 12 0 1",
        "12 2 10 0 1 1 0 1 9 0 1 2 0 1 3 0 1 9 0 1 1 0 1 1 0 1 1 0 1 9 0 1 12 0 1 8 0 1 6 3 6 6 6 3",
        "12 1 3 0 1 9 0 1 1 0 1 9 0 1 1 0 1 10 0 1 9 0 1 9 0 1 1 0 1 3 0 1 8 0 1 9 0 1 6 3 6",
        "12 1 10 0 1 10 0 1 1 0 1 1 0 1 1 0 1 8 0 1 4 0 1 10 0 1 9 0 1 3 0 1 9 0 1 4 0 1 6 3 6",
        "12 1 2 0 1 3 0 1 1 0 1 9 0 1 10 0 1 9 0 1 9 0 1 8 0 1 3 0 1 3 0 1 4 0 1 2 0 1 6 3 4",
        "12 0 10 0 1 10 0 1 9 0 1 1 0 1 3 0 1 4 0 1 4 0 1 9 0 1 9 0 1 3 0 1 9 0 1 2 0 1",
        "12 1 7 6 12 2 0 1 1 0 1 9 0 1 1 0 1 2 0 1 4 0 1 3 0 1 2 0 1 9 0 1 4 0 1 2 0 1 6 6 9",
        "12 1 16 0 1 9 0 1 1 0 1 4 0 1 10 0 1 9 0 1 2 0 1 1 0 1 2 0 1 10 0 1 9 0 1 9 0 1 6 6 3",
        "12 2 1 0 1 10 0 1 9 0 1 1 0 1 2 0 1 10 0 1 9 0 1 9 0 1 9 0 1 4 0 1 1 0 1 3 0 1 6 3 22 6 8 1",
        "12 0 16 0 1 4 0 1 10 0 1 9 0 1 2 0 1 8 0 1 10 0 1 3 0 1 3 0 1 1 0 1 9 0 1 2 0 1",
        "12 1 1 0 1 4 0 1 3 0 1 10 0 1 2 0 1 9 0 1 4 0 1 9 0 1 1 0 1 9 0 1 0 0 1 9 0 1 6 8 1",
        "12 1 16 0 1 2 0 1 9 0 1 3 0 1 7 7 12 1 0 1 9 0 1 4 0 1 9 0 1 10 0 1 0 0 1 4 0 1 6 7 12",
        "12 1 4 0 1 2 0 1 10 0 1 3 0 1 16 0 1 9 0 1 10 0 1 4 0 1 10 0 1 0 0 1 0 0 1 9 0 1 6 8 1",
        "12 1 16 0 1 2 0 1 3 0 1 16 0 1 17 0 1 10 0 1 0 0 1 9 0 1 4 0 1 0 0 1 0 0 1 10 0 1 6 8 1",
        "12 2 1 0 1 7 1 7 9 0 1 3 0 1 1 0 1 4 0 1 0 0 1 10 0 1 9 0 1 0 0 1 0 0 1 4 0 1 6 1 7 6 8 2",
        "12 0 16 0 1 3 0 1 10 0 1 16 0 1 16 0 1 9 0 1 0 0 1 0 0 1 4 0 1 0 0 1 0 0 1 9 0 1",
        "12 1 0 0 1 16 0 1 1 0 1 1 0 1 0 0 1 10 0 1 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1 10 0 1 6 8 1",
        "12 0 0 0 1 1 0 1 9 0 1 16 0 1 0 0 1 0 0 1 0 0 1 0 0 1 2 0 1 0 0 1 0 0 1 0 0 1",
        "12 0 0 0 1 16 0 1 10 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 16 0 1 0 0 1 0 0 1 0 0 1",
        "1 10 4 0 1 6 0 75 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1",
        "10 3 4 0 1 4 0 1 4 0 1 4 0 1 3 0 1 4 0 1 3 0 1 4 0 1 4 0 1 4 0 1 1 0 1 1 0 1 4 8 2",
        "12 1 4 0 1 4 0 1 1 0 1 2 0 1 3 0 1 4 0 1 1 0 1 4 0 1 4 0 1 4 0 1 1 0 1 3 0 1 6 8 14",
        "12 0 2 0 1 4 0 1 1 0 1 9 0 1 3 0 1 1 0 1 1 0 1 4 0 1 4 0 1 10 0 1 1 0 1 3 0 1",
        "12 0 9 0 1 4 0 1 1 0 1 10 0 1 3 0 1 10 0 1 1 0 1 4 0 1 9 0 1 3 0 1 1 0 1 1 0 1",
        "12 0 10 0 1 1 0 1 1 0 1 2 0 1 1 0 1 3 0 1 9 0 1 9 0 1 10 0 1 3 0 1 1 0 1 1 0 1",
        "12 0 2 0 1 9 0 1 9 0 1 9 0 1 9 0 1 3 0 1 10 0 1 10 0 1 2 0 1 3 0 1 2 0 1 1 0 1",
        "12 0 9 0 1 10 0 1 10 0 1 10 0 1 10 0 1 3 0 1 3 0 1 3 0 1 9 0 1 1 0 1 2 0 1 9 0 1",
        "12 1 10 0 1 2 0 1 3 0 1 2 0 1 4 0 1 3 0 1 3 0 1 3 0 1 10 0 1 1 0 1 2 0 1 10 0 1 6 1 1",
        "12 0 2 0 1 2 0 1 2 0 1 2 0 1 4 0 1 10 0 1 2 0 1 3 0 1 2 0 1 10 0 1 2 0 1 3 0 1",
        "12 0 9 0 1 2 0 1 9 0 1 9 0 1 4 0 1 3 0 1 2 0 1 3 0 1 2 0 1 3 0 1 4 0 1 9 0 1",
        "12 1 10 0 1 9 0 1 10 0 1 10 0 1 4 0 1 2 0 1 9 0 1 6 0 1 9 0 1 2 0 1 2 0 1 10 0 1 6 6 3",
        "12 1 3 0 1 10 0 1 2 0 1 3 0 1 6 0 1 10 0 1 10 0 1 4 0 1 10 0 1 2 0 1 2 0 1 4 0 1 6 1 4",
        "12 0 3 0 1 3 0 1 2 0 1 1 0 1 1 0 1 4 0 1 2 0 1 4 0 1 3 0 1 10 0 1 2 0 1 2 0 1",
        "12 0 3 0 1 3 0 1 2 0 1 1 0 1 1 0 1 4 0 1 9 0 1 2 0 1 3 0 1 4 0 1 9 0 1 9 0 1",
        "12 2 1 0 1 3 0 1 6 0 1 1 0 1 1 0 1 6 0 1 10 0 1 2 0 1 1 0 1 6 0 1 10 0 1 10 0 1 6 7 3 6 0 5",
        "12 1 1 0 1 3 0 1 4 0 1 1 0 1 1 0 1 4 0 1 4 0 1 9 0 1 1 0 1 16 0 1 2 0 1 4 0 1 6 6 3",
        "12 2 6 0 1 1 0 1 4 0 1 6 0 1 12 0 1 1 0 1 4 0 1 10 0 1 1 0 1 17 0 1 9 0 1 4 0 1 6 0 14 6 8 1",
        "12 1 4 0 1 6 0 1 1 0 1 1 0 1 4 0 1 1 0 1 4 0 1 3 0 1 6 0 1 3 0 1 10 0 1 2 0 1 6 0 13",
        "12 1 9 0 1 9 0 1 16 0 1 16 0 1 4 0 1 16 0 1 6 0 1 3 0 1 1 0 1 16 0 1 1 0 1 6 0 1 6 0 15",
        "12 1 1 0 1 2 0 1 4 0 1 6 0 1 2 0 1 4 0 1 3 0 1 1 0 1 1 0 1 17 0 1 1 0 1 1 0 1 6 8 1",
        "12 0 16 0 1 9 0 1 4 0 1 17 0 1 9 0 1 4 0 1 3 0 1 1 0 1 16 0 1 1 0 1 1 0 1 16 0 1",
        "12 2 0 0 1 0 0 1 9 0 1 0 0 1 3 0 1 9 0 1 16 0 1 6 0 1 17 0 1 16 0 1 6 0 1 17 0 1 6 6 3 6 0 11",
    },
    {
        "1 1 0 0 1 4 0 13",
        "1 10 1 0 1 6 0 8 3 0 7 3 4 12 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 5 10 2 5 11 2",
        "6 1 4 0 1 5 10 1 4 0 1 1 0 1 4 0 1 5 10 1 6 0 1",
        "6 1 4 0 1 1 0 1 5 11 1 1 0 1 1 0 1 14 0 1 4 0 1",
        "6 2 8 4 1 14 0 1 5 0 1 1 0 1 5 11 1 7 10 1 6 0 1 4 0 1",
        "6 2 9 0 1 7 10 1 4 0 1 1 0 1 5 0 1 17 0 1 6 0 1 4 0 1",
        "6 2 4 0 1 17 0 1 14 0 1 8 4 1 4 0 1 4 0 1 6 0 1 4 0 1",
        "6 2 8 4 1 4 0 1 7 11 1 9 0 1 1 0 1 4 0 1 6 0 1 4 0 1",
        "6 2 9 0 1 1 0 1 15 0 1 4 0 1 14 0 1 4 0 1 6 0 1 4 0 1",
        "6 2 3 0 1 8 4 1 17 0 1 4 0 1 7 11 1 8 4 1 6 0 1 4 0 1",
        "6 2 3 0 1 9 0 1 1 0 1 4 0 1 15 0 1 9 0 1 6 0 1 4 0 1",
        "6 2 17 0 1 4 0 1 1 0 1 4 0 1 17 0 1 4 0 1 6 0 1 4 0 1",
        "6 0 0 0 1 8 4 1 1 0 1 8 0 1 4 0 1 8 4 1",
        "6 0 4 0 1 9 0 1 8 4 1 9 0 1 1 0 1 9 0 1",
        "6 0 3 0 1 4 0 1 9 0 1 1 0 1 1 0 1 1 0 1",
        "6 0 0 0 1 8 4 1 1 0 1 8 0 1 8 4 1 8 0 1",
        "6 0 4 0 1 9 0 1 8 4 1 9 0 1 9 0 1 9 0 1",
        "6 0 3 0 1 4 0 1 9 0 1 3 0 1 4 0 1 0 0 1",
        "6 0 0 0 1 8 0 1 3 0 1 8 0 1 8 0 1 0 0 1",
        "6 0 4 0 1 9 0 1 8 4 1 9 0 1 9 0 1 3 0 1",
        "6 0 0 0 1 0 0 1 9 0 1 3 0 1 0 0 1 0 0 1",
        "6 0 0 0 1 0 0 1 0 0 1 8 0 1 0 0 1 0 0 1",
        "6 0 0 0 1 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1",
        "6 0 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1",
        "1 4 5 0 1 1 0 1 1 0 1 1 0 1 1 0 1",
        "5 0 4 0 1 4 0 1 4 0 1 4 0 1 5 0 1",
        "5 0 1 0 1 5 0 1 4 0 1 1 0 1 1 0 1",
        "5 0 15 0 1 15 0 1 1 0 1 1 0 1 15 0 1",
        "5 0 17 0 1 17 0 1 14 0 1 1 0 1 17 0 1",
        "5 0 16 0 1 16 0 1 4 0 1 14 0 1 16 0 1",
        "5 2 3 0 1 7 8 1 4 0 1 0 0 1 2 0 1 6 8 1 4 0 3",
        "5 2 2 0 1 4 0 1 1 0 1 2 0 1 7 8 1 6 8 1 4 0 4",
        "5 2 7 8 1 16 0 1 9 0 1 2 0 1 4 0 1 6 8 1 4 0 2",
        "5 0 0 0 1 17 0 1 1 0 1 5 0 1 17 0 1",
        "5 0 0 0 1 3 0 1 9 0 1 4 0 1 0 0 1",
        "5 0 0 0 1 6 0 1 3 0 1 15 0 1 0 0 1",
        "5 0 0 0 1 0 0 1 1 0 1 0 0 1 0 0 1",
        "5 0 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1",
        "5 0 0 0 1 0 0 1 4 0 1 0 0 1 0 0 1",
        "5 0 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1",
        "5 0 0 0 1 0 0 1 1 0 1 0 0 1 0 0 1",
        "5 0 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1",
        "5 0 0 0 1 0 0 1 3 0 1 0 0 1 0 0 1",
        "5 0 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1",
        "5 0 0 0 1 0 0 1 3 0 1 0 0 1 0 0 1",
        "5 0 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1",
        "5 0 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1",
        "5 0 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1",
        "1 6 5 0 4 6 8 1 1 0 1 1 0 1 1 0 1 1 0 1 3 0 5",
        "5 0 15 0 1 4 0 1 4 0 1 4 0 1 4 0 1",
        "5 1 17 0 1 4 0 1 4 0 1 1 0 1 1 0 1 6 0 2",
        "5 0 16 0 1 1 0 1 4 0 1 1 0 1 1 0 1",
        "5 0 1 0 1 1 0 1 4 0 1 1 0 1 9 0 1",
        "5 0 15 0 1 1 0 1 1 0 1 1 0 1 1 0 1",
        "5 0 17 0 1 1 0 1 9 0 1 9 0 1 9 0 1",
        "5 0 16 0 1 9 0 1 3 0 1 1 0 1 4 0 1",
        "5 0 4 0 1 3 0 1 9 0 1 9 0 1 9 0 1",
        "5 0 15 0 1 4 0 1 1 0 1 4 0 1 4 0 1",
        "5 0 17 0 1 4 0 1 9 0 1 9 0 1 4 0 1",
        "5 0 16 0 1 4 0 1 1 0 1 4 0 1 9 0 1",
        "5 0 2 0 1 2 0 1 9 0 1 4 0 1 10 0 1",
        "5 0 15 0 1 3 0 1 3 0 1 9 0 1 8 0 1",
        "5 0 17 0 1 2 0 1 9 0 1 10 0 1 9 0 1",
        "5 0 16 0 1 2 0 1 2 0 1 8 0 1 1 0 1",
        "5 0 3 0 1 9 0 1 9 0 1 9 0 1 9 0 1",
        "5 2 7 8 4 1 0 1 4 0 1 3 0 1 10 0 1 6 8 4 5 10 1",
        "5 0 5 10 1 1 0 1 4 0 1 9 0 1 8 0 1",
        "5 0 1 0 1 4 0 1 9 0 1 4 0 1 9 0 1",
        "5 0 1 0 1 9 0 1 1 0 1 4 0 1 3 0 1",
        "5 0 7 10 1 4 0 1 9 0 1 0 0 1 2 0 1",
        "5 0 17 0 1 0 0 1 0 0 1 0 0 1 9 0 1",
        "5 0 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1",
        "1 6 5 0 3 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 3 0 5",
        "6 0 4 0 1 4 0 1 4 0 1 4 0 1 4 0 1 4 0 1",
        "6 1 15 0 1 4 0 1 4 0 1 1 0 1 4 0 1 4 0 1 6 0 2",
        "6 0 17 0 1 4 0 1 4 0 1 1 0 1 4 0 1 4 0 1",
        "6 0 16 0 1 1 0 1 1 0 1 1 0 1 4 0 1 1 0 1",
        "6 0 1 0 1 9 0 1 1 0 1 1 0 1 1 0 1 1 0 1",
        "6 0 15 0 1 4 0 1 1 0 1 9 0 1 9 0 1 1 0 1",
        "6 0 17 0 1 9 0 1 1 0 1 1 0 1 10 0 1 1 0 1",
        "6 0 16 0 1 2 0 1 9 0 1 9 0 1 8 0 1 9 0 1",
        "6 0 3 0 1 9 0 1 10 0 1 4 0 1 9 0 1 10 0 1",
        "6 0 1 0 1 4 0 1 8 0 1 9 0 1 1 0 1 8 0 1",
        "6 0 15 0 1 9 0 1 9 0 1 2 0 1 9 0 1 9 0 1",
        "6 0 17 0 1 3 0 1 1 0 1 9 0 1 10 0 1 2 0 1",
        "6 0 16 0 1 3 0 1 9 0 1 2 0 1 8 0 1 9 0 1",
        "6 0 2 0 1 3 0 1 3 0 1 9 0 1 9 0 1 2 0 1",
        "6 0 2 0 1 3 0 1 3 0 1 0 0 1 1 0 1 9 0 1",
        "6 2 7 8 3 1 0 1 3 0 1 0 0 1 9 0 1 4 0 1 6 8 3 5 10 1",
        "6 0 16 0 1 17 0 1 2 0 1 3 0 1 1 0 1 9 0 1",
        "6 1 7 8 1 2 0 1 2 0 1 2 0 1 9 0 1 3 0 1 6 8 1",
        "6 0 17 0 1 17 0 1 2 0 1 2 0 1 0 0 1 3 0 1",
        "6 0 1 0 1 0 0 1 2 0 1 5 10 1 0 0 1 3 0 1",
        "6 0 16 0 1 0 0 1 6 0 1 4 0 1 0 0 1 2 0 1",
        "6 0 17 0 1 0 0 1 0 0 1 4 0 1 0 0 1 2 0 1",
        "6 0 0 0 1 0 0 1 0 0 1 7 10 1 0 0 1 6 0 1",
        "1 6 5 0 5 1 0 1 1 0 1 1 0 1 1 0 1 3 0 5 3 1 3",
        "5 0 15 0 1 4 0 1 4 0 1 4 0 1 4 0 1",
        "5 0 17 0 1 4 0 1 4 0 1 4 0 1 4 0 1",
        "5 1 16 0 1 1 0 1 4 0 1 1 0 1 4 0 1 6 8 1",
        "5 1 1 0 1 17 0 1 1 0 1 1 0 1 4 0 1 3 3 1",
        "5 1 15 0 1 2 0 1 1 0 1 1 0 1 1 0 1 6 0 2",
        "5 0 17 0 1 17 0 1 1 0 1 9 0 1 1 0 1",
        "5 0 16 0 1 3 0 1 1 0 1 3 0 1 1 0 1",
        "5 0 4 0 1 1 0 1 1 0 1 1 0 1 9 0 1",
        "5 0 15 0 1 1 0 1 9 0 1 9 0 1 10 0 1",
        "5 0 17 0 1 17 0 1 10 0 1 2 0 1 8 0 1",
        "5 0 16 0 1 4 0 1 8 0 1 16 0 1 9 0 1",
        "5 1 2 0 1 4 0 1 9 0 1 17 0 1 1 0 1 4 0 1",
        "5 0 15 0 1 2 0 1 3 0 1 2 0 1 9 0 1",
        "5 1 17 0 1 2 0 1 9 0 1 2 0 1 10 0 1 4 0 1",
        "5 1 16 0 1 17 0 1 3 0 1 7 8 1 8 0 1 6 8 1",
        "5 1 4 0 1 4 0 1 3 0 1 0 0 1 9 0 1 4 0 1",
        "5 0 15 0 1 0 0 1 2 0 1 0 0 1 2 0 1",
        "5 1 17 0 1 0 0 1 2 0 1 0 0 1 2 0 1 4 0 1",
        "5 0 16 0 1 0 0 1 2 0 1 0 0 1 2 0 1",
        "5 1 3 0 1 0 0 1 2 0 1 0 0 1 9 0 1 4 0 1",
        "5 0 3 0 1 0 0 1 6 0 1 0 0 1 0 0 1",
        "5 3 7 8 5 0 0 1 0 0 1 0 0 1 0 0 1 6 8 4 4 0 1 3 3 3",
        "5 0 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1",
        "1 5 5 0 5 6 8 1 1 0 1 1 0 1 1 0 1 3 0 4",
        "4 2 4 0 1 4 0 1 4 0 1 4 0 1 1 0 1 1 0 1",
        "6 0 15 0 1 5 0 4 4 0 1 4 0 1 4 0 1 4 0 1",
        "6 2 17 0 1 15 0 1 1 0 1 4 0 1 4 0 1 4 0 1 6 0 2 3 3 1",
        "6 0 16 0 1 17 0 1 1 0 1 1 0 1 4 0 1 1 0 1",
        "6 0 4 0 1 16 0 1 1 0 1 1 0 1 4 0 1 1 0 1",
        "6 0 15 0 1 1 0 1 9 0 1 9 0 1 4 0 1 1 0 1",
        "6 0 17 0 1 15 0 1 1 0 1 4 0 1 9 0 1 1 0 1",
        "6 0 16 0 1 17 0 1 1 0 1 4 0 1 3 0 1 1 0 1",
        "6 0 3 0 1 16 0 1 9 0 1 9 0 1 9 0 1 9 0 1",
        "6 0 3 0 1 1 0 1 10 0 1 10 0 1 1 0 1 3 0 1",
        "6 2 7 8 1 15 0 1 8 3 1 8 3 1 9 0 1 9 0 1 6 8 1 3 3 1",
        "6 0 1 0 1 17 0 1 9 0 1 9 0 1 1 0 1 4 0 1",
        "6 0 1 0 1 16 0 1 2 0 1 1 0 1 9 0 1 4 0 1",
        "6 0 1 0 1 4 0 1 9 0 1 9 0 1 1 0 1 2 0 1",
        "6 0 1 0 1 2 0 1 3 0 1 10 0 1 9 0 1 3 0 1",
        "6 0 9 0 1 15 0 1 9 0 1 8 3 1 10 0 1 9 0 1",
        "6 0 4 0 1 17 0 1 2 0 1 9 0 1 8 3 1 4 0 1",
        "6 0 9 0 1 16 0 1 9 0 1 1 0 1 9 0 1 4 0 1",
        "6 0 3 0 1 3 0 1 3 0 1 9 0 1 1 0 1 0 0 1",
        "6 0 2 0 1 2 0 1 2 0 1 0 0 1 9 0 1 0 0 1",
        "6 2 9 0 1 7 8 4 2 0 1 0 0 1 4 0 1 0 0 1 6 8 4 3 3 2",
        "6 0 0 0 1 0 0 1 6 0 1 0 0 1 9 0 1 0 0 1",
        "6 0 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1",
        "1 10 4 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 3 0 2 3 1 1 3 3 1",
        "8 3 1 0 1 5 0 1 4 0 1 0 0 1 4 0 1 5 0 5 0 0 1 4 0 1 6 8 1 1 0 1 3 3 1",
        "9 0 10 0 1 5 0 3 4 0 1 0 0 1 4 0 1 4 0 1 4 0 1 0 0 1 4 0 1",
        "9 0 2 0 1 15 0 1 4 0 1 0 0 1 4 0 1 15 0 1 4 0 1 0 0 1 4 0 1",
        "9 0 10 0 1 17 0 1 4 0 1 0 0 1 4 0 1 17 0 1 1 0 1 0 0 1 4 0 1",
        "9 0 3 0 1 16 0 1 1 0 1 0 0 1 1 0 1 16 0 1 1 0 1 0 0 1 1 0 1",
        "9 7 7 7 10 7 8 1 1 0 1 0 0 1 9 0 1 4 0 1 9 0 1 0 0 1 1 0 1 6 7 10 6 8 1 4 0 2 3 3 2 2 0 1 5 10 2 4 8 1",
        "9 2 3 0 1 1 0 1 3 0 1 3 0 1 3 0 1 15 0 1 3 0 1 3 0 1 3 0 1 6 8 1 4 8 1",
        "9 2 5 10 1 15 0 1 3 0 1 1 0 1 3 0 1 17 0 1 3 0 1 3 0 1 3 0 1 6 8 1 4 0 2",
        "9 0 5 0 1 17 0 1 3 0 1 5 10 1 3 0 1 16 0 1 1 0 1 3 0 1 3 0 1",
        "9 1 1 0 1 16 0 1 3 0 1 5 0 1 3 0 1 3 0 1 1 0 1 1 0 1 3 0 1 4 0 1",
        "9 0 14 0 1 1 0 1 14 0 1 14 0 1 3 0 1 3 0 1 8 0 1 1 0 1 1 0 1",
        "9 2 7 10 1 15 0 1 1 0 1 7 10 1 14 0 1 7 8 1 9 0 1 1 0 1 1 0 1 6 8 1 4 0 3",
        "9 1 15 0 1 17 0 1 8 3 1 15 0 1 3 0 1 7 8 1 4 0 1 14 0 1 8 3 1 6 8 1",
        "9 1 17 0 1 16 0 1 9 0 1 17 0 1 14 0 1 4 0 1 9 0 1 3 0 1 9 0 1 4 0 2",
        "9 0 4 0 1 4 0 1 4 0 1 3 0 1 3 0 1 4 0 1 4 0 1 1 0 1 1 0 1",
        "9 0 4 0 1 2 0 1 9 0 1 1 0 1 8 3 1 4 0 1 9 0 1 8 0 1 8 0 1",
        "9 0 4 0 1 15 0 1 4 0 1 14 0 1 9 0 1 1 0 1 4 0 1 9 0 1 9 0 1",
        "9 0 9 0 1 17 0 1 9 0 1 3 0 1 3 0 1 1 0 1 4 0 1 2 0 1 3 0 1",
        "9 0 4 0 1 16 0 1 4 0 1 8 3 1 8 3 1 9 0 1 9 0 1 8 3 1 8 0 1",
        "9 0 9 0 1 3 0 1 4 0 1 9 0 1 9 0 1 3 0 1 10 0 1 9 0 1 9 0 1",
        "9 1 4 0 1 2 0 1 4 0 1 3 0 1 0 0 1 9 0 1 4 0 1 3 0 1 3 0 1 6 0 9",
        "9 1 2 0 1 7 8 3 9 0 1 8 3 1 0 0 1 1 0 1 9 0 1 8 3 1 8 0 1 6 8 2",
        "9 1 9 0 1 0 0 1 10 0 1 9 0 1 0 0 1 9 0 1 10 0 1 9 0 1 9 0 1 6 8 1",
        "1 9 5 0 1 6 7 2 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 3 0 4 3 3 4",
        "7 3 4 0 1 4 0 1 1 0 1 1 0 1 5 0 1 4 0 1 1 0 1 1 0 1 1 0 1 5 10 1",
        "9 0 4 0 1 5 0 1 5 0 1 5 0 1 4 0 1 5 0 1 5 0 1 4 0 1 4 0 1",
        "9 0 15 0 1 4 0 1 1 0 1 15 0 1 1 0 1 1 0 1 15 0 1 4 0 1 4 0 1",
        "9 0 17 0 1 15 0 1 1 0 1 17 0 1 15 0 1 15 0 1 17 0 1 1 0 1 4 0 1",
        "9 0 16 0 1 17 0 1 15 0 1 16 0 1 17 0 1 17 0 1 16 0 1 1 0 1 4 0 1",
        "9 2 3 0 1 16 0 1 17 0 1 7 8 1 16 0 1 16 0 1 7 8 1 1 0 1 4 0 1 6 8 2 4 8 1",
        "9 1 3 0 1 3 0 1 16 0 1 5 10 1 3 0 1 2 0 1 3 0 1 1 0 1 1 0 1 6 8 1",
        "9 2 7 8 1 7 8 1 2 0 1 3 0 1 2 0 1 7 8 1 3 0 1 1 0 1 1 0 1 6 8 3 5 10 1",
        "9 1 4 0 1 1 0 1 2 0 1 7 10 1 7 8 1 4 0 1 3 0 1 9 0 1 9 0 1 6 8 1",
        "9 0 4 0 1 1 0 1 7 8 1 17 0 1 3 0 1 1 0 1 3 0 1 4 0 1 1 0 1",
        "9 0 1 0 1 1 0 1 4 0 1 4 0 1 3 0 1 1 0 1 3 0 1 8 3 1 9 0 1",
        "9 0 9 0 1 9 0 1 4 0 1 5 10 1 3 0 1 9 0 1 1 0 1 9 0 1 1 0 1",
        "9 0 4 0 1 1 0 1 4 0 1 1 0 1 3 0 1 4 0 1 8 3 1 2 0 1 8 0 1",
        "9 0 9 0 1 9 0 1 1 0 1 1 0 1 1 0 1 9 0 1 9 0 1 9 0 1 9 0 1",
        "9 0 2 0 1 3 0 1 3 0 1 7 10 1 1 0 1 4 0 1 1 0 1 3 0 1 1 0 1",
        "9 0 9 0 1 9 0 1 3 0 1 17 0 1 1 0 1 9 0 1 8 3 1 9 0 1 8 0 1",
        "9 0 4 0 1 3 0 1 1 0 1 3 0 1 8 3 1 3 0 1 9 0 1 3 0 1 9 0 1",
        "9 0 9 0 1 9 0 1 1 0 1 3 0 1 9 0 1 3 0 1 1 0 1 9 0 1 3 0 1",
        "9 0 0 0 1 3 0 1 1 0 1 4 0 1 4 0 1 3 0 1 8 0 1 1 0 1 0 0 1",
        "9 1 0 0 1 9 0 1 9 0 1 4 0 1 9 0 1 3 0 1 9 0 1 9 0 1 0 0 1 6 8 1",
        "9 0 0 0 1 3 0 1 0 0 1 2 0 1 0 0 1 2 0 1 1 0 1 0 0 1 0 0 1",
        "9 0 0 0 1 9 0 1 0 0 1 17 0 1 0 0 1 16 0 1 8 0 1 0 0 1 0 0 1",
        "9 0 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 17 0 1 9 0 1 0 0 1 0 0 1",
        "1 8 1 0 1 6 8 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 3 0 4 3 3 1",
        "6 5 10 0 1 5 0 5 5 0 4 3 0 1 3 0 1 3 0 1 1 0 1 1 0 1 1 0 1 1 0 1 3 3 1",
        "10 0 2 0 1 15 0 1 15 0 1 1 0 1 1 0 1 4 0 1 3 0 1 10 0 1 3 0 1 3 0 1",
        "10 6 7 6 6 17 0 1 17 0 1 1 0 1 1 0 1 1 0 1 3 0 1 7 6 6 3 0 1 1 0 1 6 6 12 1 0 1 4 0 3 3 3 2 5 10 1 5 11 2",
        "11 1 5 0 4 4 0 1 5 10 1 2 0 1 4 0 1 0 0 1 1 0 1 3 0 1 3 0 1 1 0 1 4 0 1 4 0 3",
        "11 0 1 0 1 15 0 1 3 0 1 5 11 2 1 0 1 0 0 1 1 0 1 3 0 1 1 0 1 1 0 1 4 0 1",
        "11 1 15 0 1 17 0 1 1 0 1 3 0 1 1 0 1 0 0 1 1 0 1 3 0 1 1 0 1 1 0 1 4 0 1 4 0 3",
        "11 0 17 0 1 16 0 1 7 10 1 3 0 1 1 0 1 0 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1",
        "11 1 16 0 1 1 0 1 17 0 1 7 11 1 9 0 1 0 0 1 9 0 1 9 0 1 1 0 1 9 0 1 9 0 1 4 0 3",
        "11 0 1 0 1 15 0 1 3 0 1 17 0 1 10 0 1 3 0 1 4 0 1 1 0 1 9 0 1 10 0 1 4 0 1",
        "11 1 15 0 1 17 0 1 3 0 1 4 0 1 8 3 1 2 0 1 9 0 1 9 0 1 10 0 1 8 3 1 9 0 1 4 0 3",
        "11 0 17 0 1 16 0 1 9 0 1 1 0 1 9 0 1 5 0 1 4 0 1 3 0 1 8 3 1 9 0 1 1 0 1",
        "11 1 16 0 1 3 0 1 2 0 1 1 0 1 4 0 1 3 0 1 9 0 1 9 0 1 9 0 1 4 0 1 9 0 1 4 0 3",
        "11 0 3 0 1 3 0 1 9 0 1 7 11 1 4 0 1 3 0 1 4 0 1 4 0 1 1 0 1 4 0 1 3 0 1",
        "11 1 15 0 1 3 0 1 3 0 1 17 0 1 9 0 1 15 0 1 4 0 1 4 0 1 9 0 1 9 0 1 3 0 1 4 0 3",
        "11 0 17 0 1 2 0 1 9 0 1 3 0 1 2 0 1 4 0 1 9 0 1 4 0 1 10 0 1 4 0 1 1 0 1",
        "11 0 16 0 1 15 0 1 1 0 1 4 0 1 9 0 1 4 0 1 2 0 1 4 0 1 8 3 1 4 0 1 3 0 1",
        "11 1 2 0 1 17 0 1 9 0 1 3 0 1 4 0 1 5 0 1 9 0 1 4 0 1 9 0 1 9 0 1 4 0 1 6 0 2",
        "11 0 15 0 1 16 0 1 1 0 1 4 0 1 4 0 1 3 0 1 2 0 1 9 0 1 3 0 1 4 0 1 4 0 1",
        "11 0 17 0 1 4 0 1 9 0 1 4 0 1 9 0 1 1 0 1 9 0 1 4 0 1 9 0 1 9 0 1 9 0 1",
        "11 1 16 0 1 7 8 3 1 0 1 0 0 1 4 0 1 1 0 1 2 0 1 4 0 1 10 0 1 0 0 1 2 0 1 6 8 3",
        "11 0 2 0 1 4 0 1 9 0 1 0 0 1 9 0 1 15 0 1 16 0 1 9 0 1 8 0 1 0 0 1 9 0 1",
        "11 1 7 8 4 16 0 1 4 0 1 0 0 1 2 0 1 0 0 1 17 0 1 2 0 1 9 0 1 0 0 1 0 0 1 6 8 4",
        "11 0 16 0 1 6 0 1 9 0 1 0 0 1 9 0 1 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1 0 0 1",
        "1 10 4 0 1 3 0 4 3 3 4 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1",
        "9 4 1 0 1 5 0 3 5 0 4 4 0 1 4 0 1 5 0 5 4 0 1 4 0 1 4 0 1 6 8 1 1 0 1 5 11 1 4 8 1",
        "10 2 3 0 1 4 0 1 15 0 1 4 0 1 4 0 1 15 0 1 3 0 1 4 0 1 4 0 1 4 0 1 6 8 1 4 0 3",
        "10 0 3 0 1 15 0 1 17 0 1 4 0 1 4 0 1 17 0 1 5 11 1 4 0 1 4 0 1 4 0 1",
        "10 1 3 0 1 17 0 1 16 0 1 4 0 1 4 0 1 16 0 1 3 0 1 1 0 1 1 0 1 1 0 1 4 0 3",
        "10 1 3 0 1 16 0 1 7 8 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 6 8 1",
        "10 1 3 0 1 1 0 1 3 0 1 1 0 1 1 0 1 15 0 1 1 0 1 1 0 1 9 0 1 10 0 1 4 0 3",
        "10 0 3 0 1 15 0 1 15 0 1 9 0 1 1 0 1 17 0 1 7 11 1 1 0 1 4 0 1 2 0 1",
        "10 1 1 0 1 17 0 1 17 0 1 1 0 1 9 0 1 16 0 1 17 0 1 9 0 1 9 0 1 10 0 1 4 0 3",
        "10 0 1 0 1 16 0 1 16 0 1 9 0 1 3 0 1 1 0 1 3 0 1 1 0 1 2 0 1 3 0 1",
        "10 3 9 0 1 4 0 1 1 0 1 1 0 1 9 0 1 15 0 1 9 0 1 9 0 1 9 0 1 7 7 8 6 7 8 4 0 3 5 11 1",
        "10 0 10 0 1 2 0 1 15 0 1 9 0 1 1 0 1 17 0 1 1 0 1 3 0 1 4 0 1 3 0 1",
        "10 1 8 0 1 15 0 1 17 0 1 10 0 1 9 0 1 16 0 1 9 0 1 9 0 1 9 0 1 3 0 1 4 0 3",
        "10 0 9 0 1 17 0 1 16 0 1 8 0 1 3 0 1 3 0 1 3 0 1 3 0 1 0 0 1 3 0 1",
        "10 1 1 0 1 16 0 1 3 0 1 9 0 1 2 0 1 15 0 1 9 0 1 9 0 1 0 0 1 3 0 1 4 0 3",
        "10 0 9 0 1 3 0 1 2 0 1 1 0 1 9 0 1 17 0 1 2 0 1 3 0 1 0 0 1 9 0 1",
        "10 0 10 0 1 3 0 1 15 0 1 9 0 1 1 0 1 16 0 1 9 0 1 9 0 1 0 0 1 4 0 1",
        "10 1 8 0 1 7 8 3 17 0 1 10 0 1 9 0 1 2 0 1 2 0 1 3 0 1 0 0 1 1 0 1 6 8 3",
        "10 0 9 0 1 3 0 1 16 0 1 8 0 1 3 0 1 15 0 1 9 0 1 9 0 1 0 0 1 9 0 1",
        "10 0 2 0 1 5 0 1 4 0 1 9 0 1 9 0 1 17 0 1 3 0 1 3 0 1 0 0 1 0 0 1",
        "10 0 2 0 1 3 0 1 4 0 1 0 0 1 3 0 1 16 0 1 9 0 1 9 0 1 0 0 1 0 0 1",
        "10 2 2 0 1 1 0 1 7 8 3 0 0 1 9 0 1 2 0 1 1 0 1 3 0 1 0 0 1 0 0 1 6 8 3 6 0 2",
        "10 1 2 0 1 1 0 1 0 0 1 0 0 1 3 0 1 7 8 5 9 0 1 9 0 1 0 0 1 0 0 1 6 8 5",
        "10 0 9 0 1 15 0 1 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1",
        "1 10 1 0 1 3 0 4 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1",
        "10 4 4 0 1 4 0 1 4 0 1 4 0 1 4 0 1 1 0 1 4 0 1 4 0 1 1 0 1 4 0 1 1 0 1 1 0 1 5 11 2 4 8 3",
        "12 2 4 0 1 4 0 1 1 0 1 4 0 1 4 0 1 1 0 1 4 0 1 4 0 1 5 0 5 4 0 1 4 0 1 4 0 1 6 8 3 4 0 5",
        "12 0 4 0 1 4 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 15 0 1 4 0 1 1 0 1 4 0 1",
        "12 1 9 0 1 4 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 17 0 1 9 0 1 5 0 5 1 0 1 4 0 1",
        "12 0 10 0 1 9 0 1 9 0 1 1 0 1 1 0 1 9 0 1 9 0 1 9 0 1 16 0 1 10 0 1 15 0 1 1 0 1",
        "12 0 3 0 1 10 0 1 10 0 1 9 0 1 1 0 1 10 0 1 10 0 1 10 0 1 1 0 1 3 0 1 17 0 1 1 0 1",
        "12 0 3 0 1 3 0 1 2 0 1 10 0 1 1 0 1 2 0 1 3 0 1 3 0 1 15 0 1 3 0 1 16 0 1 9 0 1",
        "12 0 3 0 1 3 0 1 2 0 1 3 0 1 9 0 1 2 0 1 2 0 1 3 0 1 17 0 1 3 0 1 1 0 1 10 0 1",
        "12 3 2 0 1 3 0 1 2 0 1 3 0 1 10 0 1 2 0 1 2 0 1 2 0 1 16 0 1 7 4 6 15 0 1 3 0 1 6 4 6 4 0 14 4 8 5",
        "12 2 7 4 6 3 0 1 7 4 6 2 0 1 3 0 1 2 0 1 7 4 6 7 4 6 3 0 1 5 0 3 17 0 1 2 0 1 6 4 24 4 0 5",
        "12 1 1 0 1 7 4 6 1 0 1 2 0 1 2 0 1 7 4 6 4 0 1 4 0 1 15 0 1 4 0 1 16 0 1 2 0 1 6 4 12",
        "12 2 1 0 1 5 11 1 1 0 1 7 4 6 2 0 1 4 0 1 4 0 1 4 0 1 17 0 1 15 0 1 1 0 1 2 0 1 6 4 6 4 0 5",
        "12 1 10 0 1 5 0 1 1 0 1 5 11 1 2 0 1 1 0 1 1 0 1 1 0 1 16 0 1 17 0 1 15 0 1 7 4 6 6 4 6",
        "12 1 2 0 1 4 0 1 1 0 1 5 0 1 2 0 1 1 0 1 14 0 1 1 0 1 2 0 1 16 0 1 17 0 1 5 11 1 4 0 5",
        "12 1 10 0 1 4 0 1 13 0 1 4 0 1 7 4 6 1 0 1 4 0 1 8 0 1 15 0 1 1 0 1 16 0 1 5 0 1 6 4 6",
        "12 1 2 0 1 4 0 1 3 0 1 1 0 1 0 0 1 8 0 1 8 0 1 9 0 1 17 0 1 15 0 1 3 0 1 1 0 1 4 0 5",
        "12 0 10 0 1 14 0 1 3 0 1 1 0 1 0 0 1 9 0 1 9 0 1 1 0 1 16 0 1 17 0 1 15 0 1 1 0 1",
        "12 2 7 6 12 7 11 1 3 0 1 14 0 1 0 0 1 1 0 1 1 0 1 9 0 1 3 0 1 16 0 1 17 0 1 1 0 1 6 6 12 6 8 5",
        "12 0 0 0 1 15 0 1 3 0 1 7 11 1 0 0 1 8 0 1 9 0 1 10 0 1 15 0 1 4 0 1 16 0 1 14 0 1",
        "12 0 0 0 1 17 0 1 9 0 1 15 0 1 0 0 1 9 0 1 10 0 1 8 0 1 17 0 1 2 0 1 3 0 1 7 11 1",
        "12 1 0 0 1 4 0 1 0 0 1 17 0 1 0 0 1 0 0 1 8 0 1 9 0 1 16 0 1 15 0 1 15 0 1 15 0 1 6 0 3",
        "12 0 0 0 1 8 0 1 0 0 1 0 0 1 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1 17 0 1 17 0 1 17 0 1",
        "12 0 0 0 1 9 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 16 0 1 16 0 1 0 0 1",
        "1 10 4 0 1 6 4 12 6 8 13 3 0 11 3 1 1 3 3 9 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1",
        "6 9 4 0 1 3 0 1 5 0 3 4 0 1 4 0 1 5 0 5 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 2 0 1 5 11 1 4 8 1",
        "12 2 10 0 1 3 0 1 3 0 1 8 3 1 8 3 1 4 0 1 4 0 1 5 0 5 2 0 1 4 0 1 5 11 1 3 0 1 6 8 1 4 0 3",
        "12 0 3 0 1 3 0 1 1 0 1 9 0 1 9 0 1 15 0 1 2 0 1 15 0 1 8 3 1 4 0 1 4 0 1 3 0 1",
        "12 1 3 0 1 1 0 1 15 0 1 4 0 1 4 0 1 17 0 1 2 0 1 17 0 1 9 0 1 4 0 1 4 0 1 3 0 1 4 0 3",
        "12 1 7 6 6 1 0 1 17 0 1 8 3 1 2 0 1 16 0 1 8 3 1 16 0 1 4 0 1 1 0 1 1 0 1 9 0 1 6 6 6",
        "12 1 4 0 1 9 0 1 16 0 1 9 0 1 8 3 1 1 0 1 9 0 1 1 0 1 2 0 1 1 0 1 7 11 1 3 0 1 4 0 3",
        "12 0 4 0 1 1 0 1 1 0 1 4 0 1 9 0 1 15 0 1 2 0 1 15 0 1 8 3 1 1 0 1 17 0 1 9 0 1",
        "12 1 4 0 1 1 0 1 15 0 1 8 3 1 4 0 1 17 0 1 8 3 1 17 0 1 9 0 1 9 0 1 4 0 1 1 0 1 4 0 3",
        "12 0 4 0 1 9 0 1 17 0 1 9 0 1 8 3 1 16 0 1 9 0 1 16 0 1 4 0 1 3 0 1 4 0 1 9 0 1",
        "12 1 9 0 1 4 0 1 16 0 1 2 0 1 9 0 1 4 0 1 2 0 1 1 0 1 8 3 1 3 0 1 9 0 1 1 0 1 4 0 3",
        "12 0 1 0 1 9 0 1 3 0 1 8 3 1 2 0 1 2 0 1 8 0 1 15 0 1 9 0 1 3 0 1 1 0 1 9 0 1",
        "12 1 1 0 1 4 0 1 2 0 1 9 0 1 2 0 1 15 0 1 9 0 1 17 0 1 4 0 1 16 0 1 9 0 1 1 0 1 4 0 3",
        "12 0 1 0 1 9 0 1 2 0 1 4 0 1 8 0 1 17 0 1 4 0 1 16 0 1 8 0 1 17 0 1 1 0 1 9 0 1",
        "12 1 1 0 1 2 0 1 15 0 1 8 0 1 9 0 1 16 0 1 8 0 1 1 0 1 9 0 1 2 0 1 9 0 1 1 0 1 4 0 3",
        "12 0 9 0 1 9 0 1 17 0 1 9 0 1 3 0 1 4 0 1 9 0 1 15 0 1 4 0 1 16 0 1 3 0 1 9 0 1",
        "12 0 10 0 1 3 0 1 16 0 1 1 0 1 8 3 1 15 0 1 4 0 1 17 0 1 8 0 1 17 0 1 9 0 1 10 0 1",
        "12 0 3 0 1 9 0 1 1 0 1 8 0 1 9 0 1 17 0 1 8 0 1 16 0 1 9 0 1 2 0 1 1 0 1 4 0 1",
        "12 0 3 0 1 3 0 1 9 0 1 9 0 1 0 0 1 16 0 1 9 0 1 4 0 1 2 0 1 16 0 1 9 0 1 9 0 1",
        "12 0 2 0 1 9 0 1 3 0 1 3 0 1 0 0 1 3 0 1 4 0 1 2 0 1 8 0 1 17 0 1 3 0 1 10 0 1",
        "12 0 9 0 1 3 0 1 9 0 1 1 0 1 0 0 1 1 0 1 8 0 1 15 0 1 9 0 1 3 0 1 9 0 1 0 0 1",
        "12 1 3 0 1 9 0 1 1 0 1 1 0 1 0 0 1 15 0 1 9 0 1 17 0 1 3 0 1 16 0 1 3 0 1 0 0 1 6 0 9",
        "12 0 1 0 1 0 0 1 9 0 1 1 0 1 0 0 1 4 0 1 0 0 1 16 0 1 8 0 1 17 0 1 2 0 1 0 0 1",
        "12 0 9 0 1 0 0 1 0 0 1 9 0 1 0 0 1 9 0 1 0 0 1 0 0 1 9 0 1 0 0 1 9 0 1 0 0 1",
        "1 10 1 0 1 3 0 9 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1",
        "10 1 4 0 1 5 0 5 5 0 5 4 0 1 4 0 1 5 0 5 3 0 1 4 0 1 4 0 1 2 0 1 6 8 14",
        "10 0 10 0 1 4 0 1 15 0 1 1 0 1 4 0 1 15 0 1 3 0 1 4 0 1 4 0 1 9 0 1",
        "10 0 3 0 1 15 0 1 17 0 1 10 0 1 4 0 1 17 0 1 3 0 1 4 0 1 4 0 1 4 0 1",
        "10 0 2 0 1 17 0 1 16 0 1 3 0 1 4 0 1 16 0 1 3 0 1 4 0 1 4 0 1 2 0 1",
        "10 1 7 7 4 16 0 1 1 0 1 7 7 4 4 0 1 1 0 1 1 0 1 1 0 1 4 0 1 9 0 1 6 7 8",
        "10 0 1 0 1 1 0 1 15 0 1 3 0 1 1 0 1 15 0 1 1 0 1 1 0 1 2 0 1 3 0 1",
        "10 0 10 0 1 15 0 1 17 0 1 5 0 2 1 0 1 17 0 1 1 0 1 1 0 1 2 0 1 9 0 1",
        "10 0 2 0 1 17 0 1 16 0 1 3 0 1 1 0 1 16 0 1 9 0 1 1 0 1 2 0 1 2 0 1",
        "10 0 10 0 1 16 0 1 1 0 1 15 0 1 1 0 1 1 0 1 10 0 1 1 0 1 2 0 1 9 0 1",
        "10 1 7 6 6 4 0 1 15 0 1 17 0 1 9 0 1 15 0 1 8 0 1 8 0 1 8 0 1 2 0 1 6 6 6",
        "10 0 4 0 1 15 0 1 17 0 1 16 0 1 10 0 1 17 0 1 9 0 1 9 0 1 9 0 1 2 0 1",
        "10 1 2 0 1 17 0 1 16 0 1 3 0 1 8 0 1 16 0 1 1 0 1 3 0 1 1 0 1 9 0 1 6 8 2",
        "10 0 9 0 1 16 0 1 3 0 1 15 0 1 9 0 1 1 0 1 8 0 1 3 0 1 9 0 1 4 0 1",
        "10 0 4 0 1 2 0 1 15 0 1 17 0 1 3 0 1 15 0 1 9 0 1 3 0 1 1 0 1 9 0 1",
        "10 0 9 0 1 15 0 1 17 0 1 16 0 1 3 0 1 17 0 1 4 0 1 9 0 1 9 0 1 4 0 1",
        "10 0 4 0 1 17 0 1 16 0 1 0 0 1 9 0 1 16 0 1 8 0 1 10 0 1 1 0 1 9 0 1",
        "10 0 4 0 1 16 0 1 2 0 1 0 0 1 10 0 1 4 0 1 9 0 1 8 0 1 9 0 1 4 0 1",
        "10 0 9 0 1 4 0 1 15 0 1 0 0 1 8 0 1 2 0 1 0 0 1 9 0 1 3 0 1 9 0 1",
        "10 0 1 0 1 15 0 1 17 0 1 0 0 1 9 0 1 15 0 1 0 0 1 2 0 1 2 0 1 1 0 1",
        "10 0 9 0 1 17 0 1 16 0 1 0 0 1 2 0 1 17 0 1 0 0 1 9 0 1 9 0 1 9 0 1",
        "10 1 0 0 1 16 0 1 0 0 1 0 0 1 9 0 1 16 0 1 0 0 1 0 0 1 0 0 1 3 0 1 6 0 9",
        "10 0 0 0 1 1 0 1 0 0 1 0 0 1 4 0 1 0 0 1 0 0 1 0 0 1 0 0 1 9 0 1",
        "10 0 0 0 1 9 0 1 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1",
        "1 10 5 0 5 6 8 17 3 0 9 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1",
        "9 2 4 0 1 5 0 5 4 0 1 4 0 1 5 0 5 4 0 1 4 0 1 4 0 1 5 0 5 1 0 1 1 0 1",
        "11 0 4 0 1 15 0 1 4 0 1 2 0 1 4 0 1 4 0 1 4 0 1 4 0 1 15 0 1 3 0 1 1 0 1",
        "11 0 10 0 1 17 0 1 4 0 1 2 0 1 15 0 1 1 0 1 2 0 1 4 0 1 17 0 1 3 0 1 1 0 1",
        "11 0 3 0 1 16 0 1 9 0 1 2 0 1 17 0 1 1 0 1 9 0 1 4 0 1 16 0 1 3 0 1 1 0 1",
        "11 0 3 0 1 1 0 1 2 0 1 9 0 1 16 0 1 1 0 1 2 0 1 1 0 1 1 0 1 1 0 1 9 0 1",
        "11 0 1 0 1 15 0 1 9 0 1 4 0 1 1 0 1 9 0 1 9 0 1 1 0 1 15 0 1 9 0 1 1 0 1",
        "11 0 1 0 1 17 0 1 4 0 1 9 0 1 15 0 1 10 0 1 3 0 1 9 0 1 17 0 1 3 0 1 9 0 1",
        "11 0 10 0 1 16 0 1 1 0 1 4 0 1 17 0 1 8 0 1 9 0 1 10 0 1 16 0 1 9 0 1 3 0 1",
        "11 0 2 0 1 1 0 1 1 0 1 4 0 1 16 0 1 9 0 1 4 0 1 8 0 1 1 0 1 1 0 1 9 0 1",
        "11 0 2 0 1 15 0 1 9 0 1 4 0 1 4 0 1 4 0 1 2 0 1 9 0 1 15 0 1 9 0 1 3 0 1",
        "11 1 7 6 6 17 0 1 10 0 1 9 0 1 15 0 1 2 0 1 9 0 1 3 0 1 17 0 1 1 0 1 9 0 1 6 6 6",
        "11 0 3 0 1 16 0 1 8 0 1 10 0 1 17 0 1 9 0 1 4 0 1 1 0 1 16 0 1 9 0 1 2 0 1",
        "11 0 3 0 1 3 0 1 9 0 1 8 0 1 16 0 1 10 0 1 9 0 1 1 0 1 1 0 1 0 0 1 9 0 1",
        "11 0 15 0 1 15 0 1 1 0 1 9 0 1 2 0 1 8 0 1 2 0 1 9 0 1 15 0 1 0 0 1 2 0 1",
        "11 0 17 0 1 17 0 1 9 0 1 3 0 1 15 0 1 9 0 1 9 0 1 3 0 1 17 0 1 0 0 1 9 0 1",
        "11 0 16 0 1 16 0 1 1 0 1 1 0 1 17 0 1 4 0 1 3 0 1 1 0 1 16 0 1 0 0 1 2 0 1",
        "11 0 3 0 1 2 0 1 9 0 1 9 0 1 16 0 1 9 0 1 9 0 1 9 0 1 4 0 1 0 0 1 9 0 1",
        "11 0 15 0 1 15 0 1 3 0 1 4 0 1 4 0 1 10 0 1 3 0 1 0 0 1 2 0 1 0 0 1 3 0 1",
        "11 0 17 0 1 17 0 1 1 0 1 9 0 1 15 0 1 8 0 1 9 0 1 0 0 1 15 0 1 0 0 1 9 0 1",
        "11 0 16 0 1 16 0 1 9 0 1 1 0 1 17 0 1 9 0 1 3 0 1 0 0 1 17 0 1 0 0 1 1 0 1",
        "11 1 0 0 1 1 0 1 3 0 1 9 0 1 16 0 1 1 0 1 9 0 1 0 0 1 16 0 1 0 0 1 9 0 1 6 0 9",
        "11 0 0 0 1 1 0 1 1 0 1 1 0 1 0 0 1 1 0 1 0 0 1 0 0 1 0 0 1 0 0 1 1 0 1",
        "11 0 0 0 1 9 0 1 9 0 1 9 0 1 0 0 1 9 0 1 0 0 1 0 0 1 0 0 1 0 0 1 9 0 1",
        "1 10 5 8 4 3 0 9 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1",
        "10 3 1 0 1 10 0 1 4 0 1 3 0 1 5 0 5 3 0 1 1 0 1 4 0 1 5 0 5 1 0 1 6 8 9 1 0 1 4 8 2",
        "11 2 4 0 1 7 6 6 9 0 1 1 0 1 15 0 1 3 0 1 1 0 1 9 0 1 10 0 1 10 0 1 1 0 1 6 6 6 6 8 1",
        "11 1 4 0 1 5 0 5 2 0 1 1 0 1 17 0 1 10 0 1 10 0 1 2 0 1 7 6 3 2 0 1 5 0 2 6 6 3",
        "11 1 4 0 1 15 0 1 9 0 1 10 0 1 16 0 1 4 0 1 2 0 1 9 0 1 4 0 1 7 6 6 3 0 1 6 6 6",
        "11 1 4 0 1 17 0 1 4 0 1 4 0 1 1 0 1 4 0 1 7 6 3 2 0 1 15 0 1 4 0 1 15 0 1 6 6 3",
        "11 1 11 0 1 16 0 1 4 0 1 2 0 1 15 0 1 7 7 6 4 0 1 9 0 1 17 0 1 4 0 1 17 0 1 6 7 6",
        "11 1 9 0 1 1 0 1 2 0 1 7 7 6 17 0 1 4 0 1 4 0 1 4 0 1 16 0 1 4 0 1 16 0 1 6 7 6",
        "11 0 1 0 1 15 0 1 9 0 1 4 0 1 16 0 1 4 0 1 2 0 1 4 0 1 1 0 1 2 0 1 3 0 1",
        "11 0 11 0 1 17 0 1 10 0 1 2 0 1 1 0 1 4 0 1 2 0 1 2 0 1 15 0 1 9 0 1 15 0 1",
        "11 0 9 0 1 16 0 1 8 0 1 2 0 1 15 0 1 4 0 1 9 0 1 9 0 1 17 0 1 4 0 1 17 0 1",
        "11 0 3 0 1 1 0 1 9 0 1 2 0 1 17 0 1 1 0 1 2 0 1 10 0 1 16 0 1 4 0 1 16 0 1",
        "11 0 1 0 1 15 0 1 2 0 1 2 0 1 16 0 1 9 0 1 9 0 1 8 0 1 4 0 1 2 0 1 3 0 1",
        "11 0 11 0 1 17 0 1 9 0 1 9 0 1 10 0 1 1 0 1 4 0 1 9 0 1 15 0 1 9 0 1 1 0 1",
        "11 0 9 0 1 16 0 1 10 0 1 4 0 1 1 0 1 9 0 1 1 0 1 2 0 1 17 0 1 10 0 1 1 0 1",
        "11 0 3 0 1 3 0 1 8 0 1 9 0 1 15 0 1 3 0 1 9 0 1 9 0 1 16 0 1 8 0 1 1 0 1",
        "11 0 1 0 1 15 0 1 9 0 1 1 0 1 17 0 1 9 0 1 1 0 1 10 0 1 2 0 1 9 0 1 1 0 1",
        "11 0 11 0 1 17 0 1 2 0 1 9 0 1 16 0 1 1 0 1 9 0 1 8 0 1 15 0 1 2 0 1 9 0 1",
        "11 0 9 0 1 16 0 1 9 0 1 0 0 1 4 0 1 9 0 1 4 0 1 9 0 1 17 0 1 9 0 1 3 0 1",
        "11 0 4 0 1 2 0 1 10 0 1 0 0 1 2 0 1 3 0 1 9 0 1 3 0 1 16 0 1 10 0 1 9 0 1",
        "11 0 4 0 1 15 0 1 8 0 1 0 0 1 15 0 1 9 0 1 1 0 1 9 0 1 4 0 1 8 0 1 2 0 1",
        "11 1 9 0 1 17 0 1 9 0 1 0 0 1 17 0 1 1 0 1 9 0 1 3 0 1 15 0 1 9 0 1 9 0 1 6 0 9",
        "11 0 2 0 1 16 0 1 4 0 1 0 0 1 16 0 1 9 0 1 0 0 1 9 0 1 17 0 1 2 0 1 0 0 1",
        "11 0 9 0 1 0 0 1 9 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 16 0 1 9 0 1 0 0 1",
        "1 10 3 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 3 0 11",
        "10 4 5 8 5 5 0 5 4 0 1 1 0 1 5 0 5 10 0 1 4 0 1 1 0 1 4 0 1 5 0 2 6 7 1 1 0 1 1 0 1 4 8 2",
        "12 1 1 0 1 4 0 1 1 0 1 5 8 3 3 0 1 4 0 1 4 0 1 3 0 1 10 0 1 1 0 1 2 0 1 1 0 1 6 8 6",
        "12 0 1 0 1 15 0 1 1 0 1 3 0 1 15 0 1 5 0 5 4 0 1 1 0 1 3 0 1 10 0 1 2 0 1 1 0 1",
        "12 2 1 0 1 17 0 1 10 0 1 3 0 1 17 0 1 15 0 1 1 0 1 1 0 1 7 7 4 2 0 1 2 0 1 1 0 1 6 7 3 6 8 1",
        "12 1 11 0 1 16 0 1 3 0 1 1 0 1 16 0 1 17 0 1 1 0 1 10 0 1 1 0 1 7 7 2 2 0 1 1 0 1 6 7 2",
        "12 1 9 0 1 1 0 1 2 0 1 11 0 1 1 0 1 16 0 1 1 0 1 4 0 1 1 0 1 7 7 2 9 0 1 1 0 1 6 7 2",
        "12 1 3 0 1 15 0 1 7 7 4 9 0 1 15 0 1 1 0 1 9 0 1 2 0 1 1 0 1 3 0 1 10 0 1 9 0 1 6 7 4",
        "12 0 11 0 1 17 0 1 4 0 1 3 0 1 17 0 1 15 0 1 1 0 1 2 0 1 1 0 1 15 0 1 8 0 1 3 0 1",
        "12 1 9 0 1 16 0 1 4 0 1 2 0 1 16 0 1 17 0 1 1 0 1 7 7 6 12 0 1 17 0 1 9 0 1 9 0 1 6 7 6",
        "12 1 3 0 1 4 0 1 4 0 1 11 0 1 1 0 1 16 0 1 9 0 1 4 0 1 8 0 1 16 0 1 4 0 1 3 0 1 6 8 5",
        "12 0 2 0 1 15 0 1 4 0 1 9 0 1 15 0 1 1 0 1 4 0 1 3 0 1 9 0 1 10 0 1 9 0 1 9 0 1",
        "12 0 11 0 1 17 0 1 2 0 1 3 0 1 17 0 1 15 0 1 9 0 1 3 0 1 4 0 1 3 0 1 10 0 1 3 0 1",
        "12 0 9 0 1 16 0 1 9 0 1 11 0 1 16 0 1 17 0 1 10 0 1 3 0 1 2 0 1 15 0 1 8 0 1 9 0 1",
        "12 0 3 0 1 2 0 1 10 0 1 9 0 1 10 0 1 16 0 1 8 0 1 1 0 1 9 0 1 17 0 1 9 0 1 10 0 1",
        "12 1 11 0 1 15 0 1 8 0 1 1 0 1 3 0 1 1 0 1 9 0 1 1 0 1 1 0 1 16 0 1 4 0 1 8 0 1 6 0 7",
        "12 0 9 0 1 17 0 1 9 0 1 9 0 1 15 0 1 15 0 1 3 0 1 1 0 1 9 0 1 4 0 1 4 0 1 9 0 1",
        "12 0 2 0 1 16 0 1 1 0 1 1 0 1 17 0 1 17 0 1 2 0 1 9 0 1 4 0 1 4 0 1 4 0 1 3 0 1",
        "12 0 11 0 1 10 0 1 9 0 1 9 0 1 16 0 1 16 0 1 10 0 1 3 0 1 10 0 1 6 0 1 9 0 1 9 0 1",
        "12 0 9 0 1 4 0 1 1 0 1 4 0 1 2 0 1 4 0 1 4 0 1 9 0 1 2 0 1 4 0 1 10 0 1 10 0 1",
        "12 0 4 0 1 15 0 1 10 0 1 1 0 1 15 0 1 2 0 1 9 0 1 3 0 1 9 0 1 4 0 1 8 0 1 8 0 1",
        "12 1 4 0 1 17 0 1 3 0 1 9 0 1 17 0 1 15 0 1 2 0 1 1 0 1 2 0 1 1 0 1 9 0 1 9 0 1 6 6 7",
        "12 1 0 0 1 16 0 1 9 0 1 4 0 1 16 0 1 17 0 1 10 0 1 2 0 1 9 0 1 1 0 1 1 0 1 2 0 1 6 6 5",
        "12 0 0 0 1 0 0 1 0 0 1 9 0 1 0 0 1 16 0 1 0 0 1 9 0 1 0 0 1 0 0 1 9 0 1 9 0 1",
        "1 10 3 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 3 0 8",
        "10 4 3 0 1 4 0 1 1 0 1 1 0 1 5 0 5 1 0 1 4 0 1 1 0 1 5 0 5 5 8 3 6 3 8 1 0 1 1 0 1 4 8 2",
        "12 1 3 0 1 4 0 1 5 8 1 5 0 5 15 0 1 1 0 1 2 0 1 5 0 2 4 0 1 3 0 1 9 0 1 4 0 1 6 8 10",
        "12 0 1 0 1 1 0 1 4 0 1 15 0 1 16 0 1 1 0 1 9 0 1 3 0 1 15 0 1 3 0 1 2 0 1 4 0 1",
        "12 0 10 0 1 1 0 1 4 0 1 17 0 1 10 0 1 10 0 1 4 0 1 15 0 1 17 0 1 3 0 1 9 0 1 9 0 1",
        "12 1 1 0 1 1 0 1 4 0 1 16 0 1 1 0 1 3 0 1 9 0 1 16 0 1 16 0 1 3 0 1 2 0 1 4 0 1 6 7 4",
        "12 0 10 0 1 9 0 1 1 0 1 1 0 1 15 0 1 10 0 1 4 0 1 3 0 1 1 0 1 1 0 1 9 0 1 9 0 1",
        "12 0 3 0 1 10 0 1 1 0 1 15 0 1 17 0 1 4 0 1 9 0 1 15 0 1 15 0 1 11 0 1 4 0 1 4 0 1",
        "12 0 10 0 1 8 0 1 1 0 1 17 0 1 16 0 1 2 0 1 4 0 1 17 0 1 17 0 1 9 0 1 9 0 1 9 0 1",
        "12 1 2 0 1 9 0 1 1 0 1 16 0 1 1 0 1 2 0 1 9 0 1 16 0 1 16 0 1 1 0 1 4 0 1 1 0 1 6 6 8",
        "12 1 10 0 1 4 0 1 11 0 1 1 0 1 15 0 1 2 0 1 2 0 1 4 0 1 4 0 1 11 0 1 4 0 1 10 0 1 6 8 5",
        "12 1 2 0 1 9 0 1 9 0 1 15 0 1 17 0 1 7 3 4 9 0 1 4 0 1 15 0 1 9 0 1 9 0 1 3 0 1 6 3 4",
        "12 0 10 0 1 2 0 1 3 0 1 17 0 1 16 0 1 4 0 1 2 0 1 4 0 1 17 0 1 4 0 1 3 0 1 3 0 1",
        "12 1 3 0 1 9 0 1 9 0 1 16 0 1 1 0 1 4 0 1 9 0 1 1 0 1 16 0 1 1 0 1 9 0 1 1 0 1 6 6 7",
        "12 1 10 0 1 10 0 1 3 0 1 3 0 1 15 0 1 4 0 1 10 0 1 10 0 1 2 0 1 11 0 1 2 0 1 1 0 1 6 0 2",
        "12 0 4 0 1 8 0 1 9 0 1 15 0 1 17 0 1 4 0 1 8 0 1 1 0 1 15 0 1 9 0 1 9 0 1 10 0 1",
        "12 1 4 0 1 9 0 1 10 0 1 17 0 1 16 0 1 4 0 1 9 0 1 1 0 1 17 0 1 3 0 1 3 0 1 3 0 1 6 0 3",
        "12 0 4 0 1 4 0 1 8 0 1 16 0 1 4 0 1 1 0 1 3 0 1 1 0 1 16 0 1 9 0 1 9 0 1 1 0 1",
        "12 0 4 0 1 9 0 1 9 0 1 2 0 1 2 0 1 1 0 1 9 0 1 9 0 1 4 0 1 10 0 1 3 0 1 10 0 1",
        "12 1 7 3 12 2 0 1 2 0 1 15 0 1 15 0 1 1 0 1 2 0 1 4 0 1 15 0 1 8 0 1 9 0 1 2 0 1 6 3 12",
        "12 0 4 0 1 9 0 1 9 0 1 17 0 1 17 0 1 9 0 1 9 0 1 4 0 1 17 0 1 9 0 1 2 0 1 2 0 1",
        "12 0 1 0 1 2 0 1 10 0 1 16 0 1 16 0 1 10 0 1 3 0 1 4 0 1 16 0 1 4 0 1 9 0 1 2 0 1",
        "12 1 1 0 1 9 0 1 8 0 1 2 0 1 4 0 1 8 0 1 9 0 1 4 0 1 1 0 1 1 0 1 4 0 1 7 7 14 6 7 14",
        "12 2 10 0 1 2 0 1 9 0 1 17 0 1 9 0 1 9 0 1 0 0 1 9 0 1 9 0 1 9 0 1 9 0 1 17 0 1 6 6 3 6 8 2",
        "1 10 4 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 3 0 9",
        "10 4 4 0 1 5 0 5 3 0 1 4 0 1 1 0 1 3 0 1 5 8 4 4 0 1 4 0 1 5 0 5 6 7 4 6 8 5 1 0 1 1 0 1",
        "12 0 4 0 1 4 0 1 1 0 1 4 0 1 5 0 2 3 0 1 1 0 1 4 0 1 1 0 1 3 0 1 4 0 1 4 0 1",
        "12 0 4 0 1 15 0 1 1 0 1 4 0 1 3 0 1 1 0 1 1 0 1 4 0 1 5 0 5 15 0 1 4 0 1 4 0 1",
        "12 1 1 0 1 17 0 1 1 0 1 4 0 1 15 0 1 10 0 1 1 0 1 4 0 1 15 0 1 17 0 1 4 0 1 2 0 1 6 8 2",
        "12 1 10 0 1 16 0 1 9 0 1 1 0 1 17 0 1 3 0 1 9 0 1 9 0 1 17 0 1 16 0 1 4 0 1 2 0 1 6 8 1",
        "12 1 1 0 1 1 0 1 3 0 1 9 0 1 16 0 1 2 0 1 1 0 1 2 0 1 16 0 1 1 0 1 1 0 1 2 0 1 6 0 7",
        "12 0 10 0 1 15 0 1 3 0 1 10 0 1 10 0 1 10 0 1 11 0 1 2 0 1 1 0 1 15 0 1 1 0 1 2 0 1",
        "12 0 3 0 1 17 0 1 10 0 1 8 0 1 3 0 1 4 0 1 9 0 1 9 0 1 15 0 1 17 0 1 9 0 1 9 0 1",
        "12 1 1 0 1 16 0 1 3 0 1 9 0 1 15 0 1 4 0 1 3 0 1 10 0 1 17 0 1 16 0 1 10 0 1 10 0 1 6 6 4",
        "12 2 10 0 1 4 0 1 2 0 1 2 0 1 17 0 1 7 7 6 11 0 1 8 0 1 16 0 1 1 0 1 8 0 1 8 0 1 6 7 6 6 8 3",
        "12 0 1 0 1 15 0 1 10 0 1 2 0 1 16 0 1 4 0 1 9 0 1 9 0 1 1 0 1 15 0 1 9 0 1 9 0 1",
        "12 0 10 0 1 17 0 1 2 0 1 9 0 1 1 0 1 1 0 1 3 0 1 2 0 1 15 0 1 17 0 1 3 0 1 4 0 1",
        "12 1 3 0 1 16 0 1 10 0 1 3 0 1 9 0 1 1 0 1 11 0 1 2 0 1 17 0 1 16 0 1 1 0 1 9 0 1 6 6 2",
        "12 1 10 0 1 2 0 1 4 0 1 2 0 1 1 0 1 1 0 1 9 0 1 9 0 1 16 0 1 10 0 1 9 0 1 10 0 1 6 6 3",
        "12 0 3 0 1 15 0 1 4 0 1 9 0 1 9 0 1 1 0 1 2 0 1 3 0 1 1 0 1 3 0 1 10 0 1 8 0 1",
        "12 0 3 0 1 17 0 1 4 0 1 3 0 1 3 0 1 9 0 1 11 0 1 3 0 1 15 0 1 15 0 1 8 0 1 9 0 1",
        "12 0 2 0 1 16 0 1 4 0 1 2 0 1 9 0 1 4 0 1 9 0 1 3 0 1 17 0 1 17 0 1 9 0 1 1 0 1",
        "12 0 2 0 1 10 0 1 2 0 1 9 0 1 2 0 1 4 0 1 3 0 1 3 0 1 16 0 1 16 0 1 2 0 1 9 0 1",
        "12 1 2 0 1 4 0 1 7 3 6 3 0 1 9 0 1 4 0 1 3 0 1 1 0 1 4 0 1 2 0 1 10 0 1 10 0 1 6 3 6",
        "12 0 2 0 1 15 0 1 3 0 1 2 0 1 2 0 1 4 0 1 1 0 1 1 0 1 2 0 1 15 0 1 3 0 1 8 0 1",
        "12 1 7 3 10 17 0 1 1 0 1 9 0 1 9 0 1 9 0 1 9 0 1 1 0 1 15 0 1 17 0 1 3 0 1 9 0 1 6 3 10",
        "12 0 2 0 1 16 0 1 0 0 1 3 0 1 3 0 1 0 0 1 4 0 1 1 0 1 17 0 1 16 0 1 2 0 1 0 0 1",
        "12 1 9 0 1 0 0 1 0 0 1 9 0 1 9 0 1 0 0 1 9 0 1 6 0 1 16 0 1 0 0 1 6 0 1 0 0 1 6 6 3",
        "1 10 5 0 5 3 0 9 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1",
        "10 6 15 0 1 1 0 1 4 0 1 4 0 1 5 8 4 5 0 2 1 0 1 4 0 1 10 0 1 5 0 5 6 6 6 6 7 4 1 0 1 1 0 1 1 0 1 4 8 4",
        "13 0 4 0 1 1 0 1 9 0 1 2 0 1 4 0 1 3 0 1 5 0 4 4 0 1 5 0 5 15 0 1 4 0 1 4 0 1 10 0 1",
        "13 0 1 0 1 1 0 1 2 0 1 9 0 1 4 0 1 3 0 1 4 0 1 4 0 1 1 0 1 17 0 1 2 0 1 9 0 1 7 6 3",
        "13 0 10 0 1 1 0 1 9 0 1 4 0 1 4 0 1 1 0 1 15 0 1 9 0 1 15 0 1 16 0 1 2 0 1 5 8 1 3 0 1",
        "13 0 2 0 1 10 0 1 2 0 1 4 0 1 4 0 1 10 0 1 17 0 1 4 0 1 17 0 1 1 0 1 9 0 1 4 0 1 3 0 1",
        "13 1 10 0 1 2 0 1 9 0 1 9 0 1 1 0 1 3 0 1 16 0 1 9 0 1 16 0 1 15 0 1 2 0 1 11 0 1 3 0 1 6 6 3",
        "13 0 3 0 1 10 0 1 4 0 1 2 0 1 11 0 1 1 0 1 4 0 1 1 0 1 4 0 1 17 0 1 9 0 1 3 0 1 3 0 1",
        "13 1 7 7 6 3 0 1 9 0 1 2 0 1 9 0 1 10 0 1 4 0 1 1 0 1 15 0 1 16 0 1 4 0 1 5 8 2 1 0 1 6 7 6",
        "13 0 3 0 1 10 0 1 4 0 1 9 0 1 1 0 1 2 0 1 15 0 1 1 0 1 17 0 1 10 0 1 9 0 1 11 0 1 9 0 1",
        "13 0 3 0 1 1 0 1 9 0 1 10 0 1 11 0 1 10 0 1 17 0 1 9 0 1 16 0 1 1 0 1 2 0 1 2 0 1 1 0 1",
        "13 0 3 0 1 10 0 1 10 0 1 8 0 1 9 0 1 2 0 1 16 0 1 3 0 1 1 0 1 15 0 1 9 0 1 11 0 1 9 0 1",
        "13 0 15 0 1 3 0 1 8 0 1 9 0 1 3 0 1 10 0 1 3 0 1 1 0 1 15 0 1 16 0 1 10 0 1 1 0 1 1 0 1",
        "13 0 17 0 1 10 0 1 9 0 1 3 0 1 1 0 1 3 0 1 3 0 1 9 0 1 17 0 1 4 0 1 8 0 1 5 8 2 9 0 1",
        "13 1 16 0 1 2 0 1 1 0 1 3 0 1 11 0 1 10 0 1 3 0 1 4 0 1 16 0 1 15 0 1 9 0 1 2 0 1 4 0 1 6 8 10",
        "13 0 4 0 1 10 0 1 9 0 1 2 0 1 9 0 1 4 0 1 3 0 1 4 0 1 4 0 1 17 0 1 4 0 1 2 0 1 9 0 1",
        "13 0 1 0 1 2 0 1 4 0 1 9 0 1 3 0 1 4 0 1 3 0 1 9 0 1 2 0 1 16 0 1 4 0 1 11 0 1 1 0 1",
        "13 0 1 0 1 10 0 1 9 0 1 1 0 1 1 0 1 4 0 1 15 0 1 1 0 1 15 0 1 10 0 1 4 0 1 3 0 1 9 0 1",
        "13 1 15 0 1 4 0 1 10 0 1 1 0 1 11 0 1 4 0 1 17 0 1 9 0 1 17 0 1 1 0 1 9 0 1 3 0 1 10 0 1 6 0 6",
        "13 1 17 0 1 4 0 1 8 0 1 1 0 1 9 0 1 7 3 10 16 0 1 10 0 1 16 0 1 15 0 1 10 0 1 3 0 1 8 0 1 6 3 10",
        "13 0 16 0 1 2 0 1 9 0 1 1 0 1 3 0 1 4 0 1 1 0 1 8 0 1 2 0 1 17 0 1 8 0 1 1 0 1 9 0 1",
        "13 0 10 0 1 2 0 1 1 0 1 5 8 2 9 0 1 16 0 1 15 0 1 9 0 1 15 0 1 16 0 1 9 0 1 1 0 1 3 0 1",
        "13 1 4 0 1 7 3 14 9 0 1 4 0 1 3 0 1 17 0 1 17 0 1 3 0 1 17 0 1 4 0 1 1 0 1 1 0 1 9 0 1 6 3 14",
        "13 0 17 0 1 0 0 1 0 0 1 2 0 1 9 0 1 1 0 1 16 0 1 9 0 1 16 0 1 9 0 1 9 0 1 1 0 1 0 0 1",
        "1 10 3 0 1 3 0 9 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1",
        "10 5 5 8 5 4 0 1 4 0 1 1 0 1 5 0 5 5 8 1 1 0 1 4 0 1 5 0 5 5 0 5 6 7 6 1 0 1 1 0 1 1 0 1 4 8 4",
        "13 0 1 0 1 4 0 1 4 0 1 4 0 1 4 0 1 3 0 1 3 0 1 2 0 1 15 0 1 15 0 1 4 0 1 4 0 1 1 0 1",
        "13 0 1 0 1 4 0 1 1 0 1 1 0 1 15 0 1 3 0 1 5 8 3 2 0 1 17 0 1 17 0 1 4 0 1 4 0 1 1 0 1",
        "13 0 1 0 1 1 0 1 1 0 1 1 0 1 17 0 1 1 0 1 3 0 1 2 0 1 16 0 1 16 0 1 4 0 1 4 0 1 1 0 1",
        "13 1 11 0 1 9 0 1 1 0 1 1 0 1 16 0 1 1 0 1 3 0 1 2 0 1 1 0 1 1 0 1 4 0 1 4 0 1 1 0 1 6 8 10",
        "13 1 9 0 1 1 0 1 9 0 1 10 0 1 1 0 1 1 0 1 1 0 1 9 0 1 15 0 1 15 0 1 4 0 1 1 0 1 1 0 1 6 6 6",
        "13 1 3 0 1 1 0 1 4 0 1 2 0 1 15 0 1 9 0 1 11 0 1 10 0 1 17 0 1 17 0 1 9 0 1 1 0 1 9 0 1 6 6 3",
        "13 0 11 0 1 9 0 1 4 0 1 2 0 1 17 0 1 3 0 1 9 0 1 8 0 1 16 0 1 16 0 1 10 0 1 1 0 1 4 0 1",
        "13 0 9 0 1 10 0 1 9 0 1 2 0 1 16 0 1 10 0 1 3 0 1 9 0 1 10 0 1 1 0 1 8 0 1 1 0 1 9 0 1",
        "13 1 3 0 1 1 0 1 10 0 1 7 7 4 4 0 1 3 0 1 2 0 1 4 0 1 1 0 1 15 0 1 9 0 1 9 0 1 10 0 1 6 7 4",
        "13 0 2 0 1 10 0 1 2 0 1 3 0 1 15 0 1 2 0 1 11 0 1 4 0 1 15 0 1 17 0 1 3 0 1 10 0 1 8 0 1",
        "13 0 11 0 1 3 0 1 9 0 1 5 0 2 17 0 1 10 0 1 9 0 1 9 0 1 17 0 1 16 0 1 3 0 1 8 0 1 9 0 1",
        "13 0 9 0 1 9 0 1 10 0 1 3 0 1 16 0 1 2 0 1 3 0 1 4 0 1 16 0 1 10 0 1 3 0 1 9 0 1 3 0 1",
        "13 0 3 0 1 10 0 1 3 0 1 15 0 1 2 0 1 11 0 1 11 0 1 9 0 1 1 0 1 3 0 1 3 0 1 3 0 1 3 0 1",
        "13 0 11 0 1 3 0 1 3 0 1 17 0 1 15 0 1 9 0 1 9 0 1 1 0 1 15 0 1 15 0 1 5 8 3 2 0 1 9 0 1",
        "13 1 9 0 1 3 0 1 3 0 1 16 0 1 17 0 1 10 0 1 1 0 1 9 0 1 17 0 1 17 0 1 4 0 1 9 0 1 3 0 1 6 6 9",
        "13 0 2 0 1 2 0 1 3 0 1 10 0 1 16 0 1 4 0 1 1 0 1 4 0 1 16 0 1 16 0 1 4 0 1 3 0 1 9 0 1",
        "13 1 11 0 1 2 0 1 2 0 1 3 0 1 10 0 1 4 0 1 1 0 1 9 0 1 4 0 1 2 0 1 11 0 1 1 0 1 3 0 1 6 0 6",
        "13 1 9 0 1 2 0 1 7 3 4 15 0 1 4 0 1 4 0 1 9 0 1 10 0 1 2 0 1 15 0 1 4 0 1 9 0 1 3 0 1 6 3 4",
        "13 0 0 0 1 2 0 1 4 0 1 17 0 1 15 0 1 4 0 1 10 0 1 8 0 1 15 0 1 17 0 1 11 0 1 3 0 1 9 0 1",
        "13 1 0 0 1 7 3 6 4 0 1 16 0 1 17 0 1 2 0 1 8 0 1 9 0 1 17 0 1 16 0 1 3 0 1 9 0 1 10 0 1 6 3 6",
        "13 1 0 0 1 0 0 1 4 0 1 0 0 1 16 0 1 7 3 6 9 0 1 1 0 1 16 0 1 0 0 1 3 0 1 1 0 1 8 0 1 6 3 6",
        "13 0 0 0 1 0 0 1 10 0 1 0 0 1 4 0 1 0 0 1 0 0 1 9 0 1 10 0 1 0 0 1 2 0 1 9 0 1 9 0 1",
        "1 10 5 0 5 3 0 9 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1",
        "10 4 3 0 1 1 0 1 5 8 5 1 0 1 5 0 5 3 0 1 5 8 2 4 0 1 5 0 5 5 0 2 1 0 1 1 0 1 1 0 1 4 8 4",
        "13 0 15 0 1 1 0 1 4 0 1 5 8 2 4 0 1 3 0 1 2 0 1 4 0 1 15 0 1 3 0 1 4 0 1 4 0 1 5 8 1",
        "13 0 17 0 1 1 0 1 2 0 1 3 0 1 15 0 1 1 0 1 2 0 1 1 0 1 17 0 1 15 0 1 4 0 1 4 0 1 4 0 1",
        "13 0 16 0 1 1 0 1 11 0 1 3 0 1 17 0 1 10 0 1 2 0 1 1 0 1 16 0 1 17 0 1 4 0 1 4 0 1 4 0 1",
        "13 1 10 0 1 10 0 1 9 0 1 3 0 1 16 0 1 3 0 1 11 0 1 1 0 1 10 0 1 16 0 1 4 0 1 4 0 1 4 0 1 6 8 10",
        "13 2 1 0 1 2 0 1 4 0 1 1 0 1 1 0 1 1 0 1 9 0 1 1 0 1 1 0 1 3 0 1 4 0 1 4 0 1 1 0 1 6 6 6 6 7 6",
        "13 2 15 0 1 10 0 1 11 0 1 1 0 1 15 0 1 10 0 1 4 0 1 9 0 1 15 0 1 15 0 1 1 0 1 2 0 1 1 0 1 6 6 6 6 7 2",
        "13 1 17 0 1 3 0 1 9 0 1 1 0 1 17 0 1 2 0 1 11 0 1 10 0 1 17 0 1 17 0 1 12 0 1 9 0 1 1 0 1 6 0 6",
        "13 0 16 0 1 10 0 1 4 0 1 11 0 1 16 0 1 10 0 1 9 0 1 8 0 1 16 0 1 16 0 1 8 0 1 2 0 1 1 0 1",
        "13 0 10 0 1 1 0 1 11 0 1 9 0 1 4 0 1 2 0 1 4 0 1 9 0 1 1 0 1 10 0 1 9 0 1 9 0 1 11 0 1",
        "13 0 1 0 1 10 0 1 9 0 1 3 0 1 15 0 1 10 0 1 9 0 1 1 0 1 15 0 1 3 0 1 3 0 1 10 0 1 9 0 1",
        "13 0 15 0 1 3 0 1 3 0 1 2 0 1 17 0 1 3 0 1 4 0 1 9 0 1 17 0 1 1 0 1 3 0 1 8 0 1 4 0 1",
        "13 2 17 0 1 10 0 1 2 0 1 11 0 1 16 0 1 10 0 1 9 0 1 10 0 1 16 0 1 1 0 1 2 0 1 9 0 1 9 0 1 6 6 9 6 7 4",
        "13 0 16 0 1 2 0 1 11 0 1 9 0 1 10 0 1 4 0 1 10 0 1 8 0 1 1 0 1 1 0 1 9 0 1 3 0 1 3 0 1",
        "13 0 3 0 1 10 0 1 9 0 1 2 0 1 2 0 1 4 0 1 8 0 1 9 0 1 15 0 1 1 0 1 4 0 1 9 0 1 2 0 1",
        "13 0 15 0 1 2 0 1 3 0 1 9 0 1 15 0 1 4 0 1 9 0 1 4 0 1 16 0 1 9 0 1 9 0 1 3 0 1 9 0 1",
        "13 0 17 0 1 10 0 1 11 0 1 4 0 1 17 0 1 4 0 1 2 0 1 2 0 1 4 0 1 4 0 1 1 0 1 3 0 1 4 0 1",
        "13 1 16 0 1 4 0 1 9 0 1 4 0 1 16 0 1 7 3 10 9 0 1 9 0 1 2 0 1 11 0 1 1 0 1 2 0 1 2 0 1 6 3 10",
        "13 0 2 0 1 4 0 1 3 0 1 4 0 1 4 0 1 4 0 1 10 0 1 10 0 1 15 0 1 4 0 1 1 0 1 2 0 1 9 0 1",
        "13 0 15 0 1 2 0 1 9 0 1 4 0 1 15 0 1 2 0 1 8 0 1 8 0 1 17 0 1 11 0 1 9 0 1 9 0 1 2 0 1",
        "13 0 17 0 1 2 0 1 1 0 1 4 0 1 17 0 1 9 0 1 9 0 1 9 0 1 16 0 1 4 0 1 10 0 1 4 0 1 9 0 1",
        "13 1 16 0 1 7 3 14 9 0 1 10 0 1 16 0 1 4 0 1 4 0 1 1 0 1 4 0 1 4 0 1 8 0 1 9 0 1 3 0 1 6 3 14",
        "13 0 10 0 1 5 8 1 0 0 1 1 0 1 0 0 1 9 0 1 9 0 1 9 0 1 9 0 1 2 0 1 9 0 1 0 0 1 9 0 1",
        "1 10 4 0 1 3 0 9 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1",
        "10 5 4 0 1 5 0 4 5 0 5 4 0 1 4 0 1 5 0 5 5 8 2 4 0 1 4 0 1 4 0 1 6 7 10 1 0 1 1 0 1 1 0 1 4 8 1",
        "13 0 2 0 1 4 0 1 15 0 1 2 0 1 2 0 1 15 0 1 3 0 1 4 0 1 3 0 1 4 0 1 3 0 1 3 0 1 4 0 1",
        "13 0 10 0 1 15 0 1 17 0 1 2 0 1 2 0 1 17 0 1 1 0 1 2 0 1 1 0 1 1 0 1 3 0 1 3 0 1 4 0 1",
        "13 0 4 0 1 17 0 1 16 0 1 10 0 1 2 0 1 16 0 1 1 0 1 2 0 1 1 0 1 1 0 1 3 0 1 3 0 1 10 0 1",
        "13 1 10 0 1 16 0 1 1 0 1 3 0 1 2 0 1 1 0 1 1 0 1 2 0 1 1 0 1 9 0 1 1 0 1 1 0 1 3 0 1 6 8 10",
        "13 2 2 0 1 4 0 1 15 0 1 10 0 1 9 0 1 15 0 1 9 0 1 2 0 1 10 0 1 10 0 1 9 0 1 1 0 1 10 0 1 6 6 6 6 7 2",
        "13 1 10 0 1 15 0 1 17 0 1 2 0 1 4 0 1 17 0 1 4 0 1 9 0 1 3 0 1 8 0 1 3 0 1 9 0 1 1 0 1 6 6 6",
        "13 0 3 0 1 17 0 1 16 0 1 10 0 1 9 0 1 16 0 1 9 0 1 10 0 1 16 0 1 9 0 1 9 0 1 4 0 1 10 0 1",
        "13 0 10 0 1 16 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 8 0 1 17 0 1 4 0 1 4 0 1 9 0 1 1 0 1",
        "13 0 2 0 1 4 0 1 15 0 1 1 0 1 10 0 1 15 0 1 11 0 1 9 0 1 10 0 1 2 0 1 1 0 1 1 0 1 1 0 1",
        "13 0 10 0 1 15 0 1 17 0 1 10 0 1 4 0 1 17 0 1 9 0 1 4 0 1 2 0 1 9 0 1 1 0 1 9 0 1 9 0 1",
        "13 0 3 0 1 17 0 1 16 0 1 1 0 1 9 0 1 16 0 1 3 0 1 4 0 1 16 0 1 10 0 1 1 0 1 3 0 1 4 0 1",
        "13 2 1 0 1 16 0 1 4 0 1 7 3 8 4 0 1 10 0 1 3 0 1 9 0 1 17 0 1 8 0 1 1 0 1 9 0 1 1 0 1 6 6 9 6 3 8",
        "13 0 10 0 1 3 0 1 4 0 1 5 8 1 1 0 1 1 0 1 2 0 1 10 0 1 3 0 1 9 0 1 9 0 1 1 0 1 10 0 1",
        "13 0 1 0 1 3 0 1 2 0 1 2 0 1 9 0 1 15 0 1 11 0 1 8 0 1 2 0 1 4 0 1 10 0 1 10 0 1 4 0 1",
        "13 0 10 0 1 3 0 1 15 0 1 2 0 1 4 0 1 17 0 1 9 0 1 9 0 1 16 0 1 1 0 1 8 0 1 3 0 1 10 0 1",
        "13 0 3 0 1 3 0 1 17 0 1 11 0 1 1 0 1 16 0 1 1 0 1 1 0 1 17 0 1 1 0 1 9 0 1 2 0 1 2 0 1",
        "13 2 10 0 1 3 0 1 16 0 1 0 0 1 9 0 1 4 0 1 9 0 1 9 0 1 4 0 1 9 0 1 4 0 1 10 0 1 10 0 1 6 8 14 6 0 24",
        "13 1 7 3 16 15 0 1 4 0 1 0 0 1 0 0 1 2 0 1 3 0 1 1 0 1 4 0 1 1 0 1 4 0 1 2 0 1 4 0 1 6 3 16",
        "13 0 0 0 1 17 0 1 15 0 1 0 0 1 0 0 1 15 0 1 3 0 1 1 0 1 4 0 1 9 0 1 9 0 1 10 0 1 2 0 1",
        "13 1 0 0 1 16 0 1 17 0 1 0 0 1 0 0 1 17 0 1 9 0 1 1 0 1 2 0 1 10 0 1 4 0 1 0 0 1 10 0 1 6 7 6",
        "13 0 0 0 1 10 0 1 16 0 1 0 0 1 0 0 1 16 0 1 2 0 1 9 0 1 2 0 1 8 0 1 4 0 1 0 0 1 2 0 1",
        "13 0 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 9 0 1 0 0 1 11 0 1 9 0 1 9 0 1 0 0 1 10 0 1",
        "1 10 5 0 5 3 0 9 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1",
        "10 5 15 0 1 1 0 1 5 8 4 1 0 1 5 0 5 3 0 1 2 0 1 4 0 1 4 0 1 5 0 5 6 7 4 1 0 1 1 0 1 1 0 1 4 8 4",
        "13 1 4 0 1 1 0 1 11 0 1 5 0 2 1 0 1 3 0 1 9 0 1 2 0 1 4 0 1 15 0 1 3 0 1 4 0 1 4 0 1 6 8 10",
        "13 0 15 0 1 1 0 1 9 0 1 3 0 1 15 0 1 1 0 1 4 0 1 2 0 1 1 0 1 17 0 1 3 0 1 1 0 1 4 0 1",
        "13 0 17 0 1 1 0 1 4 0 1 3 0 1 17 0 1 10 0 1 4 0 1 9 0 1 1 0 1 16 0 1 3 0 1 16 0 1 4 0 1",
        "13 0 16 0 1 10 0 1 11 0 1 15 0 1 16 0 1 3 0 1 9 0 1 2 0 1 1 0 1 10 0 1 1 0 1 17 0 1 4 0 1",
        "13 3 4 0 1 2 0 1 9 0 1 17 0 1 4 0 1 1 0 1 3 0 1 9 0 1 9 0 1 1 0 1 1 0 1 10 0 1 9 0 1 6 3 6 6 6 6 6 7 6",
        "13 3 4 0 1 10 0 1 4 0 1 16 0 1 15 0 1 10 0 1 9 0 1 4 0 1 4 0 1 15 0 1 1 0 1 1 0 1 1 0 1 6 3 6 6 6 6 6 7 2",
        "13 1 15 0 1 3 0 1 11 0 1 4 0 1 17 0 1 2 0 1 2 0 1 4 0 1 4 0 1 17 0 1 1 0 1 10 0 1 12 0 1 6 3 6",
        "13 0 17 0 1 10 0 1 9 0 1 1 0 1 16 0 1 10 0 1 9 0 1 9 0 1 9 0 1 16 0 1 9 0 1 1 0 1 8 0 1",
        "13 0 16 0 1 1 0 1 4 0 1 1 0 1 1 0 1 2 0 1 2 0 1 10 0 1 10 0 1 10 0 1 3 0 1 10 0 1 9 0 1",
        "13 1 3 0 1 10 0 1 11 0 1 15 0 1 15 0 1 10 0 1 9 0 1 8 0 1 8 0 1 1 0 1 1 0 1 4 0 1 1 0 1 6 0 1",
        "13 1 3 0 1 3 0 1 9 0 1 17 0 1 17 0 1 3 0 1 2 0 1 9 0 1 9 0 1 15 0 1 9 0 1 10 0 1 12 0 1 6 8 6",
        "13 2 3 0 1 10 0 1 2 0 1 16 0 1 16 0 1 10 0 1 9 0 1 1 0 1 3 0 1 17 0 1 10 0 1 4 0 1 8 0 1 6 3 18 6 6 9",
        "13 1 3 0 1 2 0 1 9 0 1 3 0 1 4 0 1 4 0 1 10 0 1 9 0 1 12 0 1 16 0 1 8 0 1 4 0 1 9 0 1 6 0 3",
        "13 0 3 0 1 10 0 1 4 0 1 3 0 1 2 0 1 4 0 1 8 0 1 4 0 1 8 0 1 4 0 1 9 0 1 2 0 1 3 0 1",
        "13 0 15 0 1 2 0 1 9 0 1 3 0 1 15 0 1 4 0 1 9 0 1 9 0 1 9 0 1 15 0 1 2 0 1 2 0 1 9 0 1",
        "13 0 17 0 1 10 0 1 10 0 1 9 0 1 17 0 1 4 0 1 3 0 1 10 0 1 3 0 1 17 0 1 9 0 1 10 0 1 1 0 1",
        "13 1 16 0 1 4 0 1 8 0 1 2 0 1 16 0 1 7 3 10 9 0 1 8 0 1 1 0 1 16 0 1 0 0 1 4 0 1 1 0 1 6 3 10",
        "13 0 1 0 1 4 0 1 9 0 1 9 0 1 2 0 1 0 0 1 0 0 1 9 0 1 12 0 1 1 0 1 0 0 1 2 0 1 9 0 1",
        "13 1 15 0 1 2 0 1 2 0 1 0 0 1 15 0 1 0 0 1 0 0 1 2 0 1 8 0 1 15 0 1 0 0 1 9 0 1 3 0 1 6 7 8",
        "13 0 17 0 1 2 0 1 9 0 1 0 0 1 17 0 1 0 0 1 0 0 1 9 0 1 9 0 1 17 0 1 0 0 1 0 0 1 3 0 1",
        "13 1 16 0 1 7 3 14 2 0 1 0 0 1 16 0 1 0 0 1 0 0 1 2 0 1 3 0 1 16 0 1 0 0 1 0 0 1 3 0 1 6 3 14",
        "13 0 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1 0 0 1 0 0 1 9 0 1 9 0 1 10 0 1 0 0 1 0 0 1 9 0 1",
        "1 10 5 0 5 6 7 11 6 8 14 3 0 9 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1",
        "8 6 4 0 1 5 0 5 4 0 1 1 0 1 5 0 5 4 0 1 4 0 1 4 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 4 8 4",
        "13 1 15 0 1 15 0 1 4 0 1 5 8 1 3 0 1 5 0 5 4 0 1 2 0 1 3 0 1 4 0 1 4 0 1 4 0 1 3 0 1 6 8 4",
        "13 0 17 0 1 17 0 1 4 0 1 3 0 1 3 0 1 15 0 1 2 0 1 2 0 1 3 0 1 4 0 1 4 0 1 4 0 1 3 0 1",
        "13 0 16 0 1 16 0 1 10 0 1 1 0 1 15 0 1 17 0 1 2 0 1 2 0 1 1 0 1 4 0 1 4 0 1 1 0 1 3 0 1",
        "13 1 1 0 1 1 0 1 3 0 1 1 0 1 17 0 1 16 0 1 2 0 1 2 0 1 1 0 1 4 0 1 2 0 1 1 0 1 1 0 1 6 8 2",
        "13 1 15 0 1 15 0 1 10 0 1 1 0 1 16 0 1 1 0 1 2 0 1 9 0 1 12 0 1 9 0 1 10 0 1 9 0 1 12 0 1 6 6 6",
        "13 1 17 0 1 17 0 1 3 0 1 1 0 1 10 0 1 15 0 1 9 0 1 10 0 1 8 0 1 10 0 1 4 0 1 3 0 1 8 0 1 6 6 6",
        "13 1 16 0 1 16 0 1 10 0 1 11 0 1 3 0 1 17 0 1 4 0 1 8 0 1 9 0 1 8 0 1 10 0 1 1 0 1 9 0 1 6 6 3",
        "13 0 4 0 1 1 0 1 2 0 1 9 0 1 15 0 1 16 0 1 9 0 1 9 0 1 1 0 1 9 0 1 4 0 1 9 0 1 1 0 1",
        "13 0 15 0 1 15 0 1 10 0 1 2 0 1 17 0 1 1 0 1 10 0 1 1 0 1 12 0 1 1 0 1 9 0 1 3 0 1 12 0 1",
        "13 0 17 0 1 17 0 1 3 0 1 12 0 1 16 0 1 15 0 1 8 0 1 10 0 1 8 0 1 1 0 1 1 0 1 3 0 1 8 0 1",
        "13 0 16 0 1 16 0 1 10 0 1 8 0 1 10 0 1 17 0 1 9 0 1 4 0 1 9 0 1 1 0 1 1 0 1 12 0 1 9 0 1",
        "13 1 2 0 1 10 0 1 2 0 1 9 0 1 3 0 1 16 0 1 4 0 1 10 0 1 3 0 1 1 0 1 9 0 1 8 0 1 1 0 1 6 6 6",
        "13 0 15 0 1 3 0 1 10 0 1 3 0 1 12 0 1 1 0 1 9 0 1 1 0 1 3 0 1 1 0 1 1 0 1 9 0 1 1 0 1",
        "13 0 17 0 1 15 0 1 1 0 1 9 0 1 8 0 1 15 0 1 1 0 1 10 0 1 10 0 1 9 0 1 9 0 1 1 0 1 9 0 1",
        "13 1 16 0 1 17 0 1 1 0 1 3 0 1 9 0 1 17 0 1 9 0 1 4 0 1 2 0 1 3 0 1 3 0 1 9 0 1 4 0 1 6 0 2",
        "13 0 10 0 1 16 0 1 10 0 1 3 0 1 3 0 1 16 0 1 10 0 1 10 0 1 10 0 1 10 0 1 3 0 1 4 0 1 9 0 1",
        "13 1 4 0 1 2 0 1 7 3 14 9 0 1 12 0 1 4 0 1 8 0 1 4 0 1 0 0 1 3 0 1 10 0 1 9 0 1 0 0 1 6 3 14",
        "13 0 15 0 1 15 0 1 0 0 1 10 0 1 8 0 1 2 0 1 9 0 1 9 0 1 0 0 1 2 0 1 4 0 1 10 0 1 0 0 1",
        "13 0 17 0 1 17 0 1 0 0 1 8 0 1 9 0 1 15 0 1 3 0 1 4 0 1 0 0 1 9 0 1 1 0 1 8 0 1 0 0 1",
        "13 0 16 0 1 16 0 1 0 0 1 9 0 1 0 0 1 17 0 1 9 0 1 9 0 1 0 0 1 0 0 1 9 0 1 9 0 1 0 0 1",
        "13 0 1 0 1 10 0 1 0 0 1 4 0 1 0 0 1 16 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 4 0 1 0 0 1",
        "13 0 9 0 1 0 0 1 0 0 1 10 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 9 0 1 0 0 1",
        "1 10 2 0 1 6 6 27 3 0 7 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1",
        "9 5 5 8 6 5 0 5 5 0 5 4 0 1 5 0 5 5 0 2 5 8 3 4 0 1 4 0 1 1 0 1 1 0 1 1 0 1 1 0 1 4 8 4",
        "13 0 9 0 1 15 0 1 15 0 1 3 0 1 4 0 1 3 0 1 2 0 1 4 0 1 1 0 1 4 0 1 4 0 1 4 0 1 4 0 1",
        "13 0 2 0 1 17 0 1 17 0 1 1 0 1 15 0 1 15 0 1 2 0 1 9 0 1 10 0 1 4 0 1 4 0 1 4 0 1 4 0 1",
        "13 0 11 0 1 16 0 1 16 0 1 5 8 2 17 0 1 17 0 1 11 0 1 4 0 1 2 0 1 4 0 1 4 0 1 4 0 1 1 0 1",
        "13 0 9 0 1 10 0 1 10 0 1 1 0 1 16 0 1 16 0 1 9 0 1 9 0 1 10 0 1 4 0 1 4 0 1 4 0 1 1 0 1",
        "13 3 4 0 1 1 0 1 1 0 1 1 0 1 1 0 1 3 0 1 2 0 1 3 0 1 3 0 1 4 0 1 9 0 1 9 0 1 1 0 1 6 3 6 6 7 6 6 8 9",
        "13 2 11 0 1 15 0 1 15 0 1 1 0 1 15 0 1 15 0 1 11 0 1 3 0 1 7 7 8 2 0 1 1 0 1 10 0 1 9 0 1 6 3 6 6 7 4",
        "13 2 9 0 1 17 0 1 17 0 1 1 0 1 17 0 1 17 0 1 9 0 1 3 0 1 1 0 1 2 0 1 1 0 1 8 0 1 10 0 1 6 3 6 6 7 6",
        "13 2 4 0 1 16 0 1 16 0 1 10 0 1 16 0 1 16 0 1 4 0 1 3 0 1 10 0 1 9 0 1 1 0 1 9 0 1 8 0 1 6 3 1 6 7 2",
        "13 1 11 0 1 1 0 1 10 0 1 11 0 1 4 0 1 3 0 1 11 0 1 3 0 1 1 0 1 10 0 1 9 0 1 1 0 1 9 0 1 6 7 18",
        "13 0 9 0 1 15 0 1 1 0 1 3 0 1 15 0 1 1 0 1 9 0 1 3 0 1 10 0 1 8 0 1 10 0 1 1 0 1 4 0 1",
        "13 0 4 0 1 17 0 1 15 0 1 3 0 1 17 0 1 1 0 1 4 0 1 3 0 1 3 0 1 9 0 1 8 0 1 9 0 1 9 0 1",
        "13 1 11 0 1 16 0 1 17 0 1 2 0 1 16 0 1 1 0 1 9 0 1 1 0 1 3 0 1 3 0 1 9 0 1 1 0 1 10 0 1 6 3 14",
        "13 0 9 0 1 1 0 1 16 0 1 10 0 1 2 0 1 12 0 1 4 0 1 1 0 1 10 0 1 3 0 1 1 0 1 9 0 1 8 0 1",
        "13 0 3 0 1 15 0 1 3 0 1 11 0 1 15 0 1 8 0 1 9 0 1 12 0 1 3 0 1 3 0 1 9 0 1 1 0 1 9 0 1",
        "13 0 2 0 1 17 0 1 15 0 1 1 0 1 17 0 1 9 0 1 10 0 1 8 0 1 2 0 1 2 0 1 3 0 1 9 0 1 2 0 1",
        "13 0 11 0 1 16 0 1 17 0 1 10 0 1 16 0 1 3 0 1 8 0 1 9 0 1 9 0 1 2 0 1 1 0 1 10 0 1 9 0 1",
        "13 1 9 0 1 4 0 1 16 0 1 4 0 1 4 0 1 1 0 1 9 0 1 1 0 1 3 0 1 9 0 1 9 0 1 8 0 1 4 0 1 6 0 9",
        "13 0 3 0 1 2 0 1 2 0 1 10 0 1 15 0 1 9 0 1 1 0 1 12 0 1 2 0 1 4 0 1 3 0 1 9 0 1 2 0 1",
        "13 0 11 0 1 15 0 1 15 0 1 4 0 1 17 0 1 4 0 1 9 0 1 8 0 1 9 0 1 9 0 1 9 0 1 3 0 1 9 0 1",
        "13 0 9 0 1 17 0 1 17 0 1 2 0 1 16 0 1 9 0 1 4 0 1 9 0 1 0 0 1 4 0 1 10 0 1 12 0 1 4 0 1",
        "13 0 0 0 1 16 0 1 16 0 1 9 0 1 0 0 1 0 0 1 1 0 1 0 0 1 0 0 1 4 0 1 8 0 1 8 0 1 9 0 1",
        "13 0 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1 9 0 1 9 0 1 9 0 1 0 0 1",
        "1 10 5 0 5 6 7 3 6 8 16 3 0 17 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1",
        "8 6 4 0 1 5 0 5 4 0 1 4 0 1 3 0 1 5 0 2 10 0 1 4 0 1 6 6 6 1 0 1 1 0 1 1 0 1 1 0 1 4 8 2",
        "12 1 15 0 1 4 0 1 4 0 1 2 0 1 5 0 5 3 0 1 7 3 2 4 0 1 3 0 1 1 0 1 4 0 1 4 0 1 6 8 2",
        "12 0 16 0 1 15 0 1 4 0 1 2 0 1 15 0 1 15 0 1 2 0 1 4 0 1 3 0 1 1 0 1 4 0 1 5 8 1",
        "12 1 1 0 1 17 0 1 4 0 1 2 0 1 17 0 1 17 0 1 10 0 1 1 0 1 1 0 1 1 0 1 1 0 1 4 0 1 6 8 1",
        "12 0 15 0 1 16 0 1 9 0 1 2 0 1 16 0 1 16 0 1 4 0 1 1 0 1 1 0 1 1 0 1 1 0 1 10 0 1",
        "12 2 17 0 1 1 0 1 3 0 1 9 0 1 1 0 1 10 0 1 10 0 1 1 0 1 1 0 1 1 0 1 1 0 1 11 0 1 6 3 6 6 6 6",
        "12 2 16 0 1 15 0 1 1 0 1 4 0 1 15 0 1 3 0 1 2 0 1 9 0 1 9 0 1 12 0 1 1 0 1 4 0 1 6 3 3 6 6 3",
        "12 0 4 0 1 17 0 1 1 0 1 4 0 1 17 0 1 15 0 1 10 0 1 10 0 1 3 0 1 8 1 1 9 0 1 10 0 1",
        "12 0 15 0 1 16 0 1 9 0 1 9 0 1 16 0 1 17 0 1 3 0 1 8 0 1 12 0 1 9 0 1 10 0 1 2 0 1",
        "12 0 17 0 1 1 0 1 10 0 1 10 0 1 1 0 1 16 0 1 10 0 1 9 0 1 8 1 1 3 0 1 8 0 1 10 0 1",
        "12 0 16 0 1 15 0 1 8 0 1 8 0 1 15 0 1 3 0 1 2 0 1 4 0 1 9 0 1 12 0 1 9 0 1 2 0 1",
        "12 0 2 0 1 17 0 1 9 0 1 9 0 1 17 0 1 1 0 1 10 0 1 1 0 1 2 0 1 8 1 1 3 0 1 10 0 1",
        "12 1 15 0 1 16 0 1 4 0 1 4 0 1 16 0 1 9 0 1 4 0 1 9 0 1 9 0 1 9 0 1 3 0 1 4 0 1 6 3 14",
        "12 1 17 0 1 1 0 1 1 0 1 9 0 1 10 0 1 3 0 1 10 0 1 10 0 1 3 0 1 3 0 1 9 0 1 9 0 1 6 6 9",
        "12 0 16 0 1 15 0 1 9 0 1 4 0 1 3 0 1 2 0 1 4 0 1 8 0 1 9 0 1 12 0 1 2 0 1 1 0 1",
        "12 1 10 0 1 17 0 1 10 0 1 9 0 1 15 0 1 9 0 1 9 0 1 9 0 1 3 0 1 8 1 1 10 0 1 10 0 1 6 0 7",
        "12 0 4 0 1 16 0 1 8 0 1 10 0 1 17 0 1 4 0 1 3 0 1 3 0 1 1 0 1 9 0 1 2 0 1 4 0 1",
        "12 1 15 0 1 4 0 1 9 0 1 8 1 1 16 0 1 9 0 1 2 0 1 3 0 1 9 0 1 3 0 1 2 0 1 9 0 1 6 0 6",
        "12 0 17 0 1 2 0 1 1 0 1 9 0 1 2 0 1 4 0 1 9 0 1 9 0 1 1 0 1 9 0 1 2 0 1 1 0 1",
        "12 1 16 0 1 15 0 1 9 0 1 1 0 1 15 0 1 1 0 1 0 0 1 3 0 1 9 0 1 10 0 1 7 7 3 1 0 1 6 7 3",
        "12 0 10 0 1 17 0 1 10 0 1 9 0 1 17 0 1 9 0 1 0 0 1 3 0 1 10 0 1 8 0 1 4 0 1 1 0 1",
        "12 0 2 0 1 16 0 1 8 0 1 0 0 1 16 0 1 0 0 1 0 0 1 9 0 1 8 1 1 9 0 1 17 0 1 9 0 1",
        "12 0 10 0 1 10 0 1 9 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1 0 0 1",
        "1 10 5 0 5 6 8 5 3 0 9 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1",
        "9 4 3 0 1 5 0 5 5 8 3 4 0 1 5 0 5 4 0 1 4 0 1 4 0 1 5 0 5 1 0 1 1 0 1 1 0 1 4 8 4",
        "12 1 15 0 1 4 0 1 11 0 1 2 0 1 4 0 1 1 0 1 9 0 1 2 0 1 15 0 1 3 0 1 4 0 1 5 0 2 6 8 4",
        "12 0 17 0 1 4 0 1 9 0 1 9 0 1 4 0 1 1 0 1 2 0 1 2 0 1 17 0 1 1 0 1 1 0 1 3 0 1",
        "12 0 16 0 1 15 0 1 4 0 1 2 0 1 1 0 1 1 0 1 9 0 1 9 0 1 16 0 1 1 0 1 1 0 1 15 0 1",
        "12 1 10 0 1 17 0 1 4 0 1 2 0 1 10 0 1 1 0 1 4 0 1 4 0 1 10 0 1 1 0 1 10 0 1 17 0 1 6 8 2",
        "12 3 1 0 1 16 0 1 11 0 1 9 0 1 3 0 1 9 0 1 9 0 1 9 0 1 1 0 1 1 0 1 17 0 1 16 0 1 6 3 6 6 6 6 6 7 6",
        "12 4 15 0 1 1 0 1 9 0 1 4 0 1 3 0 1 10 0 1 2 0 1 2 0 1 15 0 1 9 0 1 1 0 1 3 0 1 6 3 6 6 6 3 6 7 3 6 8 2",
        "12 2 17 0 1 15 0 1 4 0 1 9 0 1 3 0 1 8 0 1 9 0 1 2 0 1 16 0 1 10 0 1 10 0 1 15 0 1 6 3 6 6 0 6",
        "12 2 16 0 1 17 0 1 11 0 1 4 0 1 3 0 1 9 0 1 4 0 1 9 0 1 1 0 1 8 0 1 4 0 1 17 0 1 6 3 6 6 8 1",
        "12 2 10 0 1 16 0 1 9 0 1 9 0 1 10 0 1 4 0 1 9 0 1 10 0 1 15 0 1 9 0 1 1 0 1 16 0 1 6 7 9 6 8 1",
        "12 1 1 0 1 4 0 1 4 0 1 10 0 1 3 0 1 9 0 1 10 0 1 8 0 1 17 0 1 3 0 1 9 0 1 1 0 1 6 8 2",
        "12 1 15 0 1 15 0 1 1 0 1 8 0 1 2 0 1 4 0 1 8 0 1 9 0 1 16 0 1 3 0 1 3 0 1 1 0 1 6 0 7",
        "12 3 17 0 1 17 0 1 9 0 1 9 0 1 10 0 1 2 0 1 9 0 1 4 0 1 1 0 1 9 0 1 3 0 1 9 0 1 6 3 14 6 6 9 6 8 1",
        "12 0 16 0 1 16 0 1 1 0 1 4 0 1 4 0 1 9 0 1 1 0 1 4 0 1 15 0 1 3 0 1 9 0 1 10 0 1",
        "12 0 3 0 1 2 0 1 9 0 1 9 0 1 4 0 1 4 0 1 9 0 1 9 0 1 17 0 1 9 0 1 1 0 1 8 0 1",
        "12 1 15 0 1 15 0 1 10 0 1 4 0 1 7 7 9 2 0 1 4 0 1 10 0 1 16 0 1 10 0 1 9 0 1 9 0 1 6 7 9",
        "12 0 17 0 1 17 0 1 8 0 1 9 0 1 3 0 1 9 0 1 9 0 1 8 0 1 4 0 1 8 0 1 4 0 1 3 0 1",
        "12 0 16 0 1 16 0 1 9 0 1 10 0 1 3 0 1 1 0 1 10 0 1 9 0 1 2 0 1 9 0 1 4 0 1 9 0 1",
        "12 0 2 0 1 4 0 1 1 0 1 8 0 1 3 0 1 1 0 1 8 0 1 3 0 1 15 0 1 2 0 1 4 0 1 10 0 1",
        "12 0 15 0 1 15 0 1 9 0 1 9 0 1 9 0 1 9 0 1 9 0 1 9 0 1 17 0 1 9 0 1 9 0 1 8 0 1",
        "12 0 17 0 1 17 0 1 0 0 1 1 0 1 3 0 1 4 0 1 1 0 1 3 0 1 16 0 1 2 0 1 4 0 1 9 0 1",
        "12 0 16 0 1 1 0 1 0 0 1 9 0 1 9 0 1 9 0 1 9 0 1 3 0 1 4 0 1 9 0 1 2 0 1 2 0 1",
        "12 0 3 0 1 9 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 9 0 1 9 0 1 0 0 1 9 0 1 9 0 1",
        "1 10 4 0 1 6 6 15 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1",
        "10 5 10 0 1 5 0 4 5 0 6 2 0 1 4 0 1 5 0 7 4 0 1 2 0 1 4 0 1 4 0 1 6 3 10 6 7 3 1 0 1 1 0 1 4 8 2",
        "12 0 2 0 1 5 0 2 15 0 1 4 0 1 4 0 1 4 0 1 3 0 1 4 0 1 2 0 1 1 0 1 1 0 1 3 0 1",
        "12 0 10 0 1 15 0 1 17 0 1 2 0 1 4 0 1 15 0 1 3 0 1 10 0 1 10 0 1 10 0 1 1 0 1 3 0 1",
        "12 0 3 0 1 17 0 1 16 0 1 10 0 1 10 0 1 16 0 1 3 0 1 12 0 1 4 0 1 3 0 1 1 0 1 1 0 1",
        "12 0 10 0 1 16 0 1 1 0 1 12 0 1 12 0 1 4 0 1 3 0 1 8 0 1 2 0 1 3 0 1 10 0 1 9 0 1",
        "12 2 7 3 4 1 0 1 15 0 1 8 0 1 8 0 1 15 0 1 9 0 1 9 0 1 2 0 1 3 0 1 4 0 1 10 0 1 6 3 4 6 8 13",
        "12 0 1 0 1 15 0 1 17 0 1 9 0 1 9 0 1 17 0 1 10 0 1 4 0 1 10 0 1 1 0 1 4 0 1 8 0 1",
        "12 1 7 7 4 17 0 1 16 0 1 3 0 1 4 0 1 16 0 1 8 0 1 10 0 1 12 0 1 10 0 1 4 0 1 9 0 1 6 7 4",
        "12 0 4 0 1 16 0 1 1 0 1 10 0 1 10 0 1 10 0 1 9 0 1 12 0 1 4 0 1 4 0 1 9 0 1 3 0 1",
        "12 0 4 0 1 1 0 1 15 0 1 12 0 1 12 0 1 1 0 1 3 0 1 8 0 1 4 0 1 2 0 1 4 0 1 9 0 1",
        "12 0 4 0 1 15 0 1 17 0 1 8 0 1 8 0 1 15 0 1 9 0 1 9 0 1 9 0 1 2 0 1 9 0 1 10 0 1",
        "12 2 4 0 1 17 0 1 16 0 1 9 0 1 9 0 1 4 0 1 10 0 1 4 0 1 4 0 1 7 7 8 1 0 1 8 0 1 6 7 8 6 0 27",
        "12 0 9 0 1 16 0 1 3 0 1 2 0 1 4 0 1 2 0 1 8 1 1 10 0 1 2 0 1 1 0 1 9 0 1 9 0 1",
        "12 0 3 0 1 1 0 1 15 0 1 10 0 1 9 0 1 15 0 1 9 0 1 12 0 1 10 0 1 1 0 1 1 0 1 4 0 1",
        "12 0 1 0 1 15 0 1 2 0 1 12 0 1 10 0 1 3 0 1 1 0 1 8 0 1 1 0 1 1 0 1 9 0 1 1 0 1",
        "12 0 9 0 1 16 0 1 15 0 1 8 0 1 8 1 1 3 0 1 9 0 1 9 0 1 1 0 1 9 0 1 10 0 1 1 0 1",
        "12 0 4 0 1 4 0 1 16 0 1 9 0 1 9 0 1 3 0 1 1 0 1 3 0 1 9 0 1 10 0 1 3 0 1 9 0 1",
        "12 0 1 0 1 2 0 1 2 0 1 2 0 1 1 0 1 3 0 1 9 0 1 2 0 1 10 0 1 8 0 1 9 0 1 1 0 1",
        "12 0 9 0 1 15 0 1 15 0 1 9 0 1 1 0 1 3 0 1 10 0 1 10 0 1 0 0 1 9 0 1 3 0 1 9 0 1",
        "12 0 1 0 1 2 0 1 17 0 1 10 0 1 1 0 1 3 0 1 4 0 1 12 0 1 0 0 1 3 0 1 9 0 1 3 0 1",
        "12 1 1 0 1 15 0 1 16 0 1 0 0 1 1 0 1 15 0 1 1 0 1 8 1 1 0 0 1 1 0 1 2 0 1 9 0 1 6 6 3",
        "12 0 9 0 1 16 0 1 10 0 1 0 0 1 9 0 1 16 0 1 9 0 1 9 0 1 0 0 1 9 0 1 9 0 1 3 0 1",
        "12 0 10 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 10 0 1 0 0 1 0 0 1 0 0 1 4 0 1 10 0 1",
        "1 10 10 0 1 6 0 25 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1",
        "10 4 7 6 3 3 0 1 4 0 1 4 0 1 4 0 1 4 0 1 12 0 1 1 0 1 4 0 1 4 0 1 6 6 9 1 0 1 1 0 1 4 8 4",
        "12 2 1 0 1 1 0 1 4 0 1 4 0 1 4 0 1 4 0 1 2 0 1 4 0 1 3 0 1 3 0 1 4 0 1 4 0 1 6 1 2 6 8 15",
        "12 0 1 0 1 1 0 1 4 0 1 4 0 1 4 0 1 4 0 1 2 0 1 4 0 1 3 0 1 1 0 1 8 0 1 4 0 1",
        "12 0 10 0 1 1 0 1 4 0 1 4 0 1 10 0 1 1 0 1 2 0 1 1 0 1 3 0 1 1 0 1 9 0 1 2 0 1",
        "12 0 2 0 1 9 0 1 2 0 1 2 0 1 3 0 1 1 0 1 9 0 1 1 0 1 3 0 1 1 0 1 2 0 1 12 0 1",
        "12 2 10 0 1 1 0 1 9 0 1 2 0 1 3 0 1 9 0 1 1 0 1 1 0 1 1 0 1 9 0 1 12 0 1 8 0 1 6 3 6 6 6 3",
        "12 1 3 0 1 9 0 1 1 0 1 9 0 1 1 0 1 10 0 1 9 0 1 9 0 1 1 0 1 3 0 1 8 0 1 9 0 1 6 3 6",
        "12 1 10 0 1 10 0 1 1 0 1 1 0 1 1 0 1 8 0 1 4 0 1 10 0 1 9 0 1 3 0 1 9 0 1 4 0 1 6 3 6",
        "12 1 2 0 1 3 0 1 1 0 1 9 0 1 10 0 1 9 0 1 9 0 1 8 0 1 3 0 1 3 0 1 4 0 1 2 0 1 6 3 4",
        "12 0 10 0 1 10 0 1 9 0 1 1 0 1 3 0 1 4 0 1 4 0 1 9 0 1 9 0 1 3 0 1 9 0 1 2 0 1",
        "12 1 7 6 12 2 0 1 1 0 1 9 0 1 1 0 1 2 0 1 4 0 1 3 0 1 2 0 1 9 0 1 4 0 1 2 0 1 6 6 9",
        "12 1 16 0 1 9 0 1 1 0 1 4 0 1 10 0 1 9 0 1 2 0 1 1 0 1 2 0 1 10 0 1 9 0 1 9 0 1 6 6 3",
        "12 2 1 0 1 10 0 1 9 0 1 1 0 1 2 0 1 10 0 1 9 0 1 9 0 1 9 0 1 4 0 1 1 0 1 3 0 1 6 3 22 6 8 1",
        "12 0 16 0 1 4 0 1 10 0 1 9 0 1 2 0 1 8 0 1 10 0 1 3 0 1 3 0 1 1 0 1 9 0 1 2 0 1",
        "12 1 1 0 1 4 0 1 3 0 1 10 0 1 2 0 1 9 0 1 4 0 1 9 0 1 1 0 1 9 0 1 0 0 1 9 0 1 6 8 1",
        "12 1 16 0 1 2 0 1 9 0 1 3 0 1 7 7 12 1 0 1 9 0 1 4 0 1 9 0 1 10 0 1 0 0 1 4 0 1 6 7 12",
        "12 1 4 0 1 2 0 1 10 0 1 3 0 1 16 0 1 9 0 1 10 0 1 4 0 1 10 0 1 0 0 1 0 0 1 9 0 1 6 8 1",
        "12 1 16 0 1 2 0 1 3 0 1 16 0 1 17 0 1 10 0 1 0 0 1 9 0 1 4 0 1 0 0 1 0 0 1 10 0 1 6 8 1",
        "12 2 1 0 1 7 1 7 9 0 1 3 0 1 1 0 1 4 0 1 0 0 1 10 0 1 9 0 1 0 0 1 0 0 1 4 0 1 6 1 7 6 8 2",
        "12 0 16 0 1 3 0 1 10 0 1 16 0 1 16 0 1 9 0 1 0 0 1 0 0 1 4 0 1 0 0 1 0 0 1 9 0 1",
        "12 1 0 0 1 16 0 1 1 0 1 1 0 1 0 0 1 10 0 1 0 0 1 0 0 1 9 0 1 0 0 1 0 0 1 10 0 1 6 8 1",
        "12 0 0 0 1 1 0 1 9 0 1 16 0 1 0 0 1 0 0 1 0 0 1 0 0 1 2 0 1 0 0 1 0 0 1 0 0 1",
        "12 0 0 0 1 16 0 1 10 0 1 0 0 1 0 0 1 0 0 1 0 0 1 0 0 1 16 0 1 0 0 1 0 0 1 0 0 1",
        "1 10 4 0 1 6 0 75 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1 1 0 1",
        "10 3 4 0 1 4 0 1 4 0 1 4 0 1 3 0 1 4 0 1 3 0 1 4 0 1 4 0 1 4 0 1 1 0 1 1 0 1 4 8 2",
        "12 1 4 0 1 4 0 1 1 0 1 2 0 1 3 0 1 4 0 1 1 0 1 4 0 1 4 0 1 4 0 1 1 0 1 3 0 1 6 8 14",
        "12 0 2 0 1 4 0 1 1 0 1 9 0 1 3 0 1 1 0 1 1 0 1 4 0 1 4 0 1 10 0 1 1 0 1 3 0 1",
        "12 0 9 0 1 4 0 1 1 0 1 10 0 1 3 0 1 10 0 1 1 0 1 4 0 1 9 0 1 3 0 1 1 0 1 1 0 1",
        "12 0 10 0 1 1 0 1 1 0 1 2 0 1 1 0 1 3 0 1 9 0 1 9 0 1 10 0 1 3 0 1 1 0 1 1 0 1",
        "12 0 2 0 1 9 0 1 9 0 1 9 0 1 9 0 1 3 0 1 10 0 1 10 0 1 2 0 1 3 0 1 2 0 1 1 0 1",
        "12 0 9 0 1 10 0 1 10 0 1 10 0 1 10 0 1 3 0 1 3 0 1 3 0 1 9 0 1 1 0 1 2 0 1 9 0 1",
        "12 1 10 0 1 2 0 1 3 0 1 2 0 1 4 0 1 3 0 1 3 0 1 3 0 1 10 0 1 1 0 1 2 0 1 10 0 1 6 1 1",
        "12 0 2 0 1 2 0 1 2 0 1 2 0 1 4 0 1 10 0 1 2 0 1 3 0 1 2 0 1 10 0 1 2 0 1 3 0 1",
        "12 0 9 0 1 2 0 1 9 0 1 9 0 1 4 0 1 3 0 1 2 0 1 3 0 1 2 0 1 3 0 1 4 0 1 9 0 1",
        "12 1 10 0 1 9 0 1 10 0 1 10 0 1 4 0 1 2 0 1 9 0 1 6 0 1 9 0 1 2 0 1 2 0 1 10 0 1 6 6 3",
        "12 1 3 0 1 10 0 1 2 0 1 3 0 1 6 0 1 10 0 1 10 0 1 4 0 1 10 0 1 2 0 1 2 0 1 4 0 1 6 1 4",
        "12 0 3 0 1 3 0 1 2 0 1 1 0 1 1 0 1 4 0 1 2 0 1 4 0 1 3 0 1 10 0 1 2 0 1 2 0 1",
        "12 0 3 0 1 3 0 1 2 0 1 1 0 1 1 0 1 4 0 1 9 0 1 2 0 1 3 0 1 4 0 1 9 0 1 9 0 1",
        "12 2 1 0 1 3 0 1 6 0 1 1 0 1 1 0 1 6 0 1 10 0 1 2 0 1 1 0 1 6 0 1 10 0 1 10 0 1 6 7 3 6 0 5",
        "12 1 1 0 1 3 0 1 4 0 1 1 0 1 1 0 1 4 0 1 4 0 1 9 0 1 1 0 1 16 0 1 2 0 1 4 0 1 6 6 3",
        "12 2 6 0 1 1 0 1 4 0 1 6 0 1 12 0 1 1 0 1 4 0 1 10 0 1 1 0 1 17 0 1 9 0 1 4 0 1 6 0 14 6 8 1",
        "12 1 4 0 1 6 0 1 1 0 1 1 0 1 4 0 1 1 0 1 4 0 1 3 0 1 6 0 1 3 0 1 10 0 1 2 0 1 6 0 13",
        "12 1 9 0 1 9 0 1 16 0 1 16 0 1 4 0 1 16 0 1 6 0 1 3 0 1 1 0 1 16 0 1 1 0 1 6 0 1 6 0 15",
        "12 1 1 0 1 2 0 1 4 0 1 6 0 1 2 0 1 4 0 1 3 0 1 1 0 1 1 0 1 17 0 1 1 0 1 1 0 1 6 8 1",
        "12 0 16 0 1 9 0 1 4 0 1 17 0 1 9 0 1 4 0 1 3 0 1 1 0 1 16 0 1 1 0 1 1 0 1 16 0 1",
        "12 2 0 0 1 0 0 1 9 0 1 0 0 1 3 0 1 9 0 1 16 0 1 6 0 1 17 0 1 16 0 1 6 0 1 17 0 1 6 6 3 6 0 11",
    },
};

%%writefile source/include/policy_plugin_abi.hpp
// Stable C ABI between the native tournament and separately compiled policies.
#pragma once

#include "sim.hpp"

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


%%writefile source/include/pyrandom.hpp
// CPython-compatible Mersenne Twister.
//
// The environment seeds `random.Random((seed * 1_000_003) ^ day)` and calls
// .random() (weed spawns) and .choice() (shop unlocks). To reproduce episodes
// bit-for-bit we must match CPython's _randommodule.c exactly: init_by_array
// seeding from the integer's 32-bit little-endian words, the 53-bit
// random() construction, and getrandbits/_randbelow rejection sampling.
#pragma once
#include <cstdint>
#include <vector>

namespace kag {

class PyRandom {
public:
    explicit PyRandom(uint64_t key) { seed(key); }

    void seed(uint64_t key) {
        // CPython: abs(n) -> array of 32-bit words, little endian. A zero key
        // still yields a one-word array [0].
        uint32_t words[3];
        int n = 0;
        if (key == 0) {
            words[0] = 0;
            n = 1;
        } else {
            while (key) {
                words[n++] = static_cast<uint32_t>(key & 0xffffffffu);
                key >>= 32;
            }
        }
        init_by_array(words, n);
    }

    uint32_t genrand_uint32() {
        uint32_t y;
        if (index_ >= N) {
            for (int k = 0; k < N - M; ++k) {
                y = (mt_[k] & UPPER) | (mt_[k + 1] & LOWER);
                mt_[k] = mt_[k + M] ^ (y >> 1) ^ ((y & 1u) ? MATRIX_A : 0u);
            }
            for (int k = N - M; k < N - 1; ++k) {
                y = (mt_[k] & UPPER) | (mt_[k + 1] & LOWER);
                mt_[k] = mt_[k + (M - N)] ^ (y >> 1) ^ ((y & 1u) ? MATRIX_A : 0u);
            }
            y = (mt_[N - 1] & UPPER) | (mt_[0] & LOWER);
            mt_[N - 1] = mt_[M - 1] ^ (y >> 1) ^ ((y & 1u) ? MATRIX_A : 0u);
            index_ = 0;
        }
        y = mt_[index_++];
        y ^= (y >> 11);
        y ^= (y << 7) & 0x9d2c5680u;
        y ^= (y << 15) & 0xefc60000u;
        y ^= (y >> 18);
        return y;
    }

    // random.random(): 53 bits of precision from two 32-bit draws.
    double random() {
        uint32_t a = genrand_uint32() >> 5;
        uint32_t b = genrand_uint32() >> 6;
        return (a * 67108864.0 + b) * (1.0 / 9007199254740992.0);
    }

    // random.getrandbits(k) for 0 < k <= 32.
    uint32_t getrandbits(int k) { return genrand_uint32() >> (32 - k); }

    // Random._randbelow_with_getrandbits(n), n > 0.
    uint32_t randbelow(uint32_t n) {
        int k = 0;
        for (uint32_t v = n; v; v >>= 1) ++k;   // n.bit_length()
        uint32_t r = getrandbits(k);
        while (r >= n) r = getrandbits(k);
        return r;
    }

    // random.choice(seq) -> index
    uint32_t choice_index(uint32_t len) { return randbelow(len); }

private:
    static constexpr int N = 624;
    static constexpr int M = 397;
    static constexpr uint32_t MATRIX_A = 0x9908b0dfu;
    static constexpr uint32_t UPPER = 0x80000000u;
    static constexpr uint32_t LOWER = 0x7fffffffu;

    uint32_t mt_[N];
    int index_ = N;

    void init_genrand(uint32_t s) {
        mt_[0] = s;
        for (int i = 1; i < N; ++i)
            mt_[i] = 1812433253u * (mt_[i - 1] ^ (mt_[i - 1] >> 30)) + static_cast<uint32_t>(i);
        index_ = N;
    }

    void init_by_array(const uint32_t* key, int keylen) {
        init_genrand(19650218u);
        int i = 1, j = 0;
        int k = (N > keylen) ? N : keylen;
        for (; k; --k) {
            mt_[i] = (mt_[i] ^ ((mt_[i - 1] ^ (mt_[i - 1] >> 30)) * 1664525u)) + key[j] + static_cast<uint32_t>(j);
            ++i; ++j;
            if (i >= N) { mt_[0] = mt_[N - 1]; i = 1; }
            if (j >= keylen) j = 0;
        }
        for (k = N - 1; k; --k) {
            mt_[i] = (mt_[i] ^ ((mt_[i - 1] ^ (mt_[i - 1] >> 30)) * 1566083941u)) - static_cast<uint32_t>(i);
            ++i;
            if (i >= N) { mt_[0] = mt_[N - 1]; i = 1; }
        }
        mt_[0] = 0x80000000u;
        index_ = N;
    }
};

}  // namespace kag


%%writefile source/include/sim.hpp
// Kaggriculture simulator — a C++ port of kaggriculture.py from
// kaggle-environments 1.32.7.
// Official source SHA256:
// bc8a54879ef02c7ea64b8b333d6a976f0ea65c4949149d01f463f23bccee653e
//
// Design goals, in order: (1) bit-identical results to the Python interpreter,
// (2) zero heap allocation per step, (3) trivially copyable state so search can
// snapshot and fork episodes.
#pragma once
#include <cmath>
#include <cstdint>
#include <cstring>
#include <algorithm>
#include <array>
#include "pyrandom.hpp"

namespace kag {

inline constexpr char ENGINE_VERSION[] = "1.32.7";
inline constexpr char ENGINE_SOURCE_SHA256[] =
    "bc8a54879ef02c7ea64b8b333d6a976f0ea65c4949149d01f463f23bccee653e";

// ---------------------------------------------------------------- item space
// PRODUCTS order matches kaggriculture.py exactly. The first five products are
// also the five crops, in CROPS order, so a crop id doubles as a product id.
enum Item : uint8_t {
    WHEAT = 0, CARROT, TOMATO, STRAWBERRY, MELON, EGG, MILK, WOOL, FERTILIZER,
    GOOSE, COW, SHEEP, N_ITEMS
};
constexpr int N_PRODUCTS = 9;
constexpr int N_CROPS = 5;
constexpr int N_ANIMALS = 3;
inline bool is_crop(uint8_t i) { return i < N_CROPS; }
inline bool is_product(uint8_t i) { return i < N_PRODUCTS; }
inline bool is_animal(uint8_t i) { return i >= GOOSE && i < N_ITEMS; }

// ---------------------------------------------------------------- unit ops
enum Op : uint8_t {
    OP_PASS = 0, OP_NORTH, OP_SOUTH, OP_EAST, OP_WEST,
    OP_PICKUP, OP_DROP, OP_PLACE,
    OP_PLANT, OP_WATER, OP_HARVEST, OP_FERTILIZE, OP_DIG,
    OP_BUILD_COOP, OP_BUILD_PASTURE,
    OP_FEED, OP_COLLECT_FERTILIZER, OP_CARE, OP_INVALID
};

enum MOp : uint8_t {
    M_NONE = 0, M_HIRE, M_BUY_LAND, M_BUY_SEED, M_BUY_PRODUCT, M_BUY_ANIMAL, M_SELL
};

// ---------------------------------------------------------------- static data
struct CropDef { int seed, first_yield_day, max_yield_day, interval, max_yield; bool ongoing; };
inline constexpr CropDef CROPS[N_CROPS] = {
    {  10, 2,  4, 0, 6, false },  // WHEAT
    {  20, 2,  3, 0, 4, false },  // CARROT
    {  50, 8,  8, 1, 4, true  },  // TOMATO
    { 100, 10, 10, 2, 4, true },  // STRAWBERRY
    {  80, 10, 12, 0, 6, false }, // MELON
};

enum Structure : uint8_t { ST_COOP = 0, ST_PASTURE = 1 };
struct AnimalDef { int cost; Structure structure; int first_yield_day, interval, max_held; Item product; };
inline constexpr AnimalDef ANIMALS[N_ANIMALS] = {
    { 300, ST_COOP,    4, 1, 4, EGG  },  // GOOSE
    { 400, ST_PASTURE, 8, 2, 6, MILK },  // COW
    { 500, ST_PASTURE, 6, 3, 6, WOOL },  // SHEEP
};

enum Shape : uint8_t { F_LINEAR, F_SQ, F_SQRT, F_LOG, F_LOG10, F_HINGE };
struct MarketDef { double base; int I0; double T; Shape below_f; double below_t; Shape above_f; double above_t; };
inline constexpr MarketDef MARKET[N_PRODUCTS] = {
    {  25, 10000, 400, F_SQRT,   0.80, F_LOG,    0.20 },  // WHEAT
    {  35, 10000, 450, F_HINGE,  1.00, F_SQRT,   0.70 },  // CARROT
    {  60, 10000, 200, F_HINGE,  0.40, F_SQRT,   0.60 },  // TOMATO
    { 120, 10000, 100, F_SQRT,   0.70, F_LINEAR, 1.60 },  // STRAWBERRY
    { 250, 10000, 300, F_LOG,    0.20, F_SQ,     3.60 },  // MELON
    {  50, 10000, 332, F_HINGE,  0.40, F_LOG,    0.20 },  // EGG
    { 160, 10000, 122, F_SQRT,   0.60, F_LINEAR, 1.60 },  // MILK
    { 200, 10000, 105, F_LOG,    0.20, F_SQ,     3.20 },  // WOOL
    { 100, 10000, 200, F_LINEAR, 0.40, F_LINEAR, 0.40 },  // FERTILIZER
};

inline double shape(Shape f, double x, double T = 0.0) {
    if (x < 0.0) x = 0.0;
    switch (f) {
        case F_LINEAR: return x;
        case F_SQ:     return x * x;
        case F_SQRT:   return std::sqrt(x);
        case F_LOG:    return std::log(1.0 + x);
        case F_LOG10:  return std::log10(1.0 + x);
        case F_HINGE: {
            if (T <= 0.0) return x;
            double u = x / T;
            double excess = std::max(0.0, u - 1.0);
            return u + 8.0 * excess * excess;
        }
    }
    return x;
}

// Amplitudes are derived constants; precompute once.
struct MarketAmp { double below, above; };
inline const std::array<MarketAmp, N_PRODUCTS>& market_amps() {
    static const std::array<MarketAmp, N_PRODUCTS> a = [] {
        std::array<MarketAmp, N_PRODUCTS> r{};
        for (int i = 0; i < N_PRODUCTS; ++i) {
            r[i].below = MARKET[i].below_t * MARKET[i].base / shape(MARKET[i].below_f, MARKET[i].T, MARKET[i].T);
            r[i].above = MARKET[i].above_t * MARKET[i].base / shape(MARKET[i].above_f, MARKET[i].T, MARKET[i].T);
        }
        return r;
    }();
    return a;
}

// Python: max(PRICE_FLOOR, int(round(price))). Python's round() on a float is
// round-half-to-even, which is exactly nearbyint's default mode.
inline int market_price(int item, int inv) {
    const MarketDef& p = MARKET[item];
    const MarketAmp& a = market_amps()[item];
    double price;
    if (inv < p.I0) price = p.base + a.below * shape(p.below_f, static_cast<double>(p.I0 - inv), p.T);
    else            price = p.base - a.above * shape(p.above_f, static_cast<double>(inv - p.I0), p.T);
    int v = static_cast<int>(std::nearbyint(price));
    return v < 1 ? 1 : v;
}

// ---------------------------------------------------------------- shops / town
enum ShopId : uint8_t {
    SHOP_BAKERY = 0, SHOP_BRUNCH_SPOT, SHOP_FARMERS_MARKET, SHOP_ICE_CREAM_SHOP,
    SHOP_PET_CAFE, SHOP_PIZZA_SHOP, SHOP_SMOOTHIE_SHOP, SHOP_YARN_STORE, N_SHOPS
};
// NOTE: this array is in sorted(SHOPS) order, because the environment unlocks
// with `rng.choice(sorted(SHOPS))`.
inline constexpr uint16_t SHOP_MASK[N_SHOPS] = {
    (1u << EGG) | (1u << WHEAT),                                        // BAKERY
    (1u << EGG) | (1u << WHEAT) | (1u << STRAWBERRY),                   // BRUNCH_SPOT
    (1u << WHEAT) | (1u << CARROT) | (1u << TOMATO) | (1u << STRAWBERRY),// FARMERS_MARKET
    (1u << STRAWBERRY) | (1u << MILK) | (1u << WHEAT),                  // ICE_CREAM_SHOP
    (1u << CARROT),                                                     // PET_CAFE
    (1u << MILK) | (1u << TOMATO) | (1u << WHEAT),                      // PIZZA_SHOP
    (1u << STRAWBERRY) | (1u << MILK),                                  // SMOOTHIE_SHOP
    (1u << WOOL),                                                       // YARN_STORE
};
inline constexpr int SHOP_MULT[N_SHOPS] = { 1, 1, 1, 1, 2, 1, 1, 2 };  // single-product shops pull 2x
constexpr int MAX_SHOP_INSTANCES = 8;

// ---------------------------------------------------------------- config
struct Config {
    int episode_steps = 720;
    int board_size = 10;
    int starting_money = 3000;
    int max_orders = 10;
    int turns_per_day = 24;
    int shed_capacity = 100;
    double weed_chance = 0.005;
    int shop_unlock_interval = 3;
    int shop_sell_interval = 4;
    int center_sell_interval = 24;
    int hire_mult = 1;
    uint64_t seed = 0;
    // Optional tournament intervention. The official Python runner first runs
    // the ordinary end-of-day transition and then replaces only the unlocked
    // shop identity. Keeping the sampled RNG draw below preserves that order.
    bool pin_shops = false;
    uint8_t pinned_shops[MAX_SHOP_INSTANCES] = {0};
    int n_pinned_shops = 0;
};

// ---------------------------------------------------------------- state
enum TileKind : uint8_t { T_EMPTY = 0, T_LOCKED, T_WEED, T_COOP, T_PASTURE, T_PLANT };

struct Tile {
    TileKind kind = T_EMPTY;
    uint8_t  what = 0;          // crop id (PLANT) or animal id (COOP/PASTURE with animal)
    bool     has_animal = false;
    bool     watered_today = false;
    bool     fed_today = false;
    bool     cared_today = false;
    bool     fertilizer_available = false;
    int8_t   consecutive_dry = 0;    // unwatered (plant) / unfed (animal)
    int8_t   yield_units = 0;
    int8_t   pending_care_bonus = 0;
    int16_t  planted_day = 0;        // or placed_day
    int32_t  max_lifespan_step = -1;
    int16_t  fertilized_until_day = -1;
};

constexpr int MAX_UNITS = 40;   // farmer + hands; hires are Fibonacci-priced so this is ample
constexpr int BOARD = 10;

struct Farm {
    double money = 0;
    Tile tiles[BOARD][BOARD];
    int8_t pos_x[MAX_UNITS], pos_y[MAX_UNITS];
    int n_units = 1;                 // index 0 is the main farmer
    int n_quadrants = 1;             // NW always unlocked
    int hires_today = 0;

    int16_t shed[N_ITEMS] = {0};
    int shed_total = 0;
    int16_t seeds[N_CROPS] = {0};
    int16_t inv[MAX_UNITS][N_ITEMS] = {{0}};
    // Per-unit inventories are Python dicts, and several code paths iterate
    // them in INSERTION order. That order decides which items win the last
    // slots when the 100-item shed cap binds, so it is load-bearing, not
    // cosmetic, and must be modelled explicitly.
    uint8_t inv_keys[MAX_UNITS][N_ITEMS] = {{0}};
    uint8_t inv_nkeys[MAX_UNITS] = {0};

    // Instrumentation only - never read by the interpreter, so behaviour and
    // parity are unaffected. `discarded` is the production the 100-item shed
    // cap silently destroyed, which is otherwise invisible to search.
    int32_t discarded[N_ITEMS] = {0};
    int32_t produced[N_ITEMS] = {0};
    int32_t sold_units[N_ITEMS] = {0};
    double  sell_revenue = 0;   // coins actually received from SELLs
    double  total_spend = 0;    // coins actually paid out

    void inv_add(int u, int item, int n) {
        if (n <= 0) return;
        if (inv[u][item] == 0) inv_keys[u][inv_nkeys[u]++] = (uint8_t)item;
        inv[u][item] += (int16_t)n;
    }
    void inv_erase(int u, int item) {
        inv[u][item] = 0;
        int k = 0;
        while (k < inv_nkeys[u] && inv_keys[u][k] != item) ++k;
        if (k == inv_nkeys[u]) return;
        for (int j = k; j + 1 < inv_nkeys[u]; ++j) inv_keys[u][j] = inv_keys[u][j + 1];
        inv_nkeys[u]--;
    }
    bool inv_take(int u, int item, int n) {
        if (inv[u][item] < n) return false;
        inv[u][item] -= (int16_t)n;
        if (inv[u][item] == 0) inv_erase(u, item);
        return true;
    }
    void inv_clear(int u) { for (int i = 0; i < N_ITEMS; ++i) inv[u][i] = 0; inv_nkeys[u] = 0; }
};

struct Market {
    int32_t inventory[N_PRODUCTS];
    int32_t prices[N_PRODUCTS];
};

struct State {
    Farm farms[2];
    Market market;
    uint8_t shops[MAX_SHOP_INSTANCES];
    int n_shops = 0;
    int step = 0;
    int day = 0;
    int hour = 0;
    bool done = false;
};

// ---------------------------------------------------------------- actions
struct UnitAction { uint8_t op = OP_PASS; uint8_t arg = 0; int16_t n = 1; };
struct Order { uint8_t op = M_NONE; uint8_t item = 0; int32_t n = 0; };

struct Action {
    UnitAction units[MAX_UNITS];     // units[0] = farmer
    int n_units = 1;
    Order orders[16];
    int n_orders = 0;
    void clear() { n_units = 1; units[0] = UnitAction{}; n_orders = 0; }
};

// ---------------------------------------------------------------- helpers
inline int quadrant_of(int x, int y, int bs) {
    // 0=NW 1=NE 2=SW 3=SE
    int half = bs / 2;
    return (y < half ? 0 : 2) + (x < half ? 0 : 1);
}
// Land is unlocked in the order NE, SW, SE.
inline constexpr int LAND_ORDER[3] = { 1, 2, 3 };
inline constexpr int LAND_PRICES[3] = { 1000, 2000, 4000 };

inline void shed_access_tiles(int bs, int out[4][2]) {
    int h = bs / 2;
    out[0][0] = h - 1; out[0][1] = h - 1;
    out[1][0] = h;     out[1][1] = h - 1;
    out[2][0] = h - 1; out[2][1] = h;
    out[3][0] = h;     out[3][1] = h;
}
inline bool is_shed_adjacent(int x, int y, int bs) {
    int h = bs / 2;
    return (x == h - 1 || x == h) && (y == h - 1 || y == h);
}

inline int fib(int n) { int a = 1, b = 1; for (int i = 0; i < n; ++i) { int t = b; b = a + b; a = t; } return a; }

class Sim {
public:
    Config cfg;
    State st;

    explicit Sim(const Config& c = Config{}) : cfg(c) { reset(); }

    void reset() {
        st = State{};
        int h = cfg.board_size / 2;
        for (int p = 0; p < 2; ++p) {
            Farm& f = st.farms[p];
            f.money = cfg.starting_money;
            for (int y = 0; y < cfg.board_size; ++y)
                for (int x = 0; x < cfg.board_size; ++x)
                    f.tiles[y][x].kind = (quadrant_of(x, y, cfg.board_size) == 0) ? T_EMPTY : T_LOCKED;
            f.n_units = 1;
            f.pos_x[0] = static_cast<int8_t>(h - 1);
            f.pos_y[0] = static_cast<int8_t>(h - 1);
        }
        for (int i = 0; i < N_PRODUCTS; ++i) {
            st.market.inventory[i] = MARKET[i].I0;
            st.market.prices[i] = static_cast<int>(MARKET[i].base);
        }
    }

    double reward(int p) const { return st.farms[p].money; }

    // One environment step, given both players' actions.
    void step(const Action& a0, const Action& a1) {
        if (st.done) return;
        const Action* acts[2] = { &a0, &a1 };
        int step_i = st.step;
        int day = step_i / cfg.turns_per_day;

        for (int p = 0; p < 2; ++p) apply_unit_actions(p, *acts[p], day);
        process_market(*acts[0], *acts[1]);
        town_consume(step_i);
        for (int p = 0; p < 2; ++p) decay_plants(st.farms[p], step_i);
        if ((step_i + 1) % cfg.turns_per_day == 0) end_of_day(day);

        st.step = step_i + 1;
        st.day = st.step / cfg.turns_per_day;
        st.hour = st.step % cfg.turns_per_day;
        if (step_i >= cfg.episode_steps - 2) st.done = true;
    }

private:
    // ------------------------------------------------------------ unit actions
    void apply_unit_actions(int p, const Action& a, int day) {
        Farm& f = st.farms[p];
        // Atomic PLANT validation: if requests for a crop exceed seeds held,
        // every PLANT of that crop this turn is dropped.
        // Demand is counted over every submitted unit action, including ones
        // addressed to hands that do not exist (matching the Python, where the
        // blocked set is computed before the position lookup no-ops).
        int demand[N_CROPS] = {0};
        for (int i = 0; i < a.n_units; ++i)
            if (a.units[i].op == OP_PLANT && a.units[i].arg < N_CROPS) demand[a.units[i].arg]++;
        int n = std::min(a.n_units, f.n_units);
        bool blocked[N_CROPS];
        for (int c = 0; c < N_CROPS; ++c) blocked[c] = demand[c] > f.seeds[c];

        for (int i = 0; i < n; ++i) {
            UnitAction u = a.units[i];
            if (u.op == OP_PLANT && u.arg < N_CROPS && blocked[u.arg]) continue;
            apply_unit(f, i, u, day);
        }
    }

    void apply_unit(Farm& f, int idx, const UnitAction& u, int day) {
        const int bs = cfg.board_size;
        int fx = f.pos_x[idx], fy = f.pos_y[idx];
        int16_t* inv = f.inv[idx];

        switch (u.op) {
            case OP_PASS: return;
            case OP_NORTH: case OP_SOUTH: case OP_EAST: case OP_WEST: {
                int nx = fx + (u.op == OP_EAST) - (u.op == OP_WEST);
                int ny = fy + (u.op == OP_SOUTH) - (u.op == OP_NORTH);
                // Movement onto LOCKED tiles is legal (hands can spawn there).
                if (nx < 0 || nx >= bs || ny < 0 || ny >= bs) return;
                f.pos_x[idx] = static_cast<int8_t>(nx);
                f.pos_y[idx] = static_cast<int8_t>(ny);
                return;
            }
            default: break;
        }

        Tile& tile = f.tiles[fy][fx];

        // Shed ops resolve before the LOCKED guard: three of the four
        // shed-access tiles start locked, and the shed itself is always owned.
        if (u.op == OP_DROP) {
            if (!is_shed_adjacent(fx, fy, bs)) return;
            // Insertion order, matching `for item, n in list(inv.items())`.
            uint8_t keys[N_ITEMS];
            int nk = f.inv_nkeys[idx];
            for (int k = 0; k < nk; ++k) keys[k] = f.inv_keys[idx][k];
            for (int k = 0; k < nk; ++k) {
                int it = keys[k];
                if (inv[it] <= 0) { f.inv_erase(idx, it); continue; }
                int room = std::max(0, cfg.shed_capacity - f.shed_total);
                int take = std::min<int>(inv[it], room);
                if (take > 0) { f.shed[it] += take; f.shed_total += take; }
                f.discarded[it] += inv[it] - take;
                f.inv_erase(idx, it);
            }
            return;
        }
        if (u.op == OP_PICKUP) {
            if (!is_shed_adjacent(fx, fy, bs)) return;
            if (u.n <= 0 || u.arg >= N_ITEMS) return;
            int take = std::min<int>(u.n, f.shed[u.arg]);
            if (take <= 0) return;
            f.shed[u.arg] -= take; f.shed_total -= take;
            f.inv_add(idx, u.arg, take);
            return;
        }
        if (u.op == OP_PLACE) {
            if (u.arg >= N_ITEMS) return;
            if (is_animal(u.arg)) {
                const AnimalDef& ad = ANIMALS[u.arg - GOOSE];
                TileKind want = (ad.structure == ST_COOP) ? T_COOP : T_PASTURE;
                if (tile.kind == want && !tile.has_animal) {
                    if (f.inv_take(idx, u.arg, 1)) {
                        Tile t{};
                        t.kind = want; t.what = u.arg; t.has_animal = true;
                        t.planted_day = static_cast<int16_t>(day);
                        tile = t;
                    }
                    return;
                }
            }
            if (is_shed_adjacent(fx, fy, bs)) {
                int n = std::min<int>(u.n, inv[u.arg]);
                if (n <= 0) return;
                n = std::min(n, std::max(0, cfg.shed_capacity - f.shed_total));
                if (n <= 0) return;
                f.inv_take(idx, u.arg, n);
                f.shed[u.arg] += n; f.shed_total += n;
            }
            return;
        }

        if (tile.kind == T_LOCKED) return;

        switch (u.op) {
            case OP_PLANT: {
                if (u.arg >= N_CROPS || tile.kind != T_EMPTY || f.seeds[u.arg] <= 0) return;
                f.seeds[u.arg] -= 1;
                const CropDef& cd = CROPS[u.arg];
                Tile t{};
                t.kind = T_PLANT; t.what = u.arg;
                t.planted_day = static_cast<int16_t>(day);
                t.consecutive_dry = 1;                 // planting day counts as unwatered
                t.yield_units = cd.ongoing ? 0 : 1;
                t.max_lifespan_step = cd.ongoing ? -1
                    : (day + cd.max_yield_day + 1) * cfg.turns_per_day;
                tile = t;
                return;
            }
            case OP_WATER: {
                if (tile.kind != T_PLANT || tile.watered_today) return;
                tile.watered_today = true;
                const CropDef& cd = CROPS[tile.what];
                if (!cd.ongoing) {
                    int age = day - tile.planted_day;
                    int w0 = (cd.max_yield_day + 1) / 2;
                    if (age >= w0 && age <= cd.max_yield_day) {
                        int bonus = (tile.fertilized_until_day >= day) ? 2 : 1;
                        tile.yield_units = static_cast<int8_t>(std::min(cd.max_yield, tile.yield_units + bonus));
                    }
                }
                return;
            }
            case OP_HARVEST: {
                if (tile.kind == T_EMPTY || tile.kind == T_WEED) return;
                if (tile.yield_units <= 0) return;
                if (tile.kind == T_PLANT) {
                    const CropDef& cd = CROPS[tile.what];
                    if (day - tile.planted_day < cd.first_yield_day) return;
                    f.inv_add(idx, tile.what, tile.yield_units);
                    f.produced[tile.what] += tile.yield_units;
                    tile.yield_units = 0;
                    if (!cd.ongoing) { Tile e{}; e.kind = T_EMPTY; tile = e; }
                } else if (tile.has_animal) {
                    f.inv_add(idx, ANIMALS[tile.what - GOOSE].product, tile.yield_units);
                    f.produced[ANIMALS[tile.what - GOOSE].product] += tile.yield_units;
                    tile.yield_units = 0;
                }
                return;
            }
            case OP_FERTILIZE: {
                if (tile.kind != T_PLANT) return;
                if (!f.inv_take(idx, FERTILIZER, 1)) return;
                tile.fertilized_until_day = std::max<int16_t>(tile.fertilized_until_day,
                                                             static_cast<int16_t>(day + 2));
                return;
            }
            case OP_DIG: {
                if (tile.kind == T_EMPTY) return;
                if (tile.has_animal) return;           // animals are not removable
                Tile e{}; e.kind = T_EMPTY; tile = e;
                return;
            }
            case OP_BUILD_COOP:
                if (tile.kind != T_EMPTY) return;
                { Tile t{}; t.kind = T_COOP; tile = t; }
                return;
            case OP_BUILD_PASTURE:
                if (tile.kind != T_EMPTY) return;
                { Tile t{}; t.kind = T_PASTURE; tile = t; }
                return;
            case OP_FEED:
                if (!tile.has_animal || tile.fed_today) return;
                if (!f.inv_take(idx, WHEAT, 1)) return;
                tile.fed_today = true;
                return;
            case OP_COLLECT_FERTILIZER:
                if (!tile.has_animal || !tile.fertilizer_available) return;
                tile.fertilizer_available = false;
                f.inv_add(idx, FERTILIZER, 1);
                f.produced[FERTILIZER] += 1;
                return;
            case OP_CARE:
                if (!tile.has_animal || tile.cared_today) return;
                tile.cared_today = true;
                return;
            default: return;
        }
    }

    // ------------------------------------------------------------ market
    struct OState { uint8_t type; uint8_t item; int32_t remaining; bool live; };

    void process_market(const Action& a0, const Action& a1) {
        const Action* acts[2] = { &a0, &a1 };
        int nq[2];
        for (int p = 0; p < 2; ++p) nq[p] = std::min(acts[p]->n_orders, cfg.max_orders);
        int max_len = std::max(nq[0], nq[1]);

        for (int i = 0; i < max_len; ++i) {
            OState os[2];
            for (int p = 0; p < 2; ++p) {
                os[p].live = false;
                if (i < nq[p]) {
                    const Order& o = acts[p]->orders[i];
                    if (o.op == M_HIRE || o.op == M_BUY_LAND) {
                        os[p].type = o.op; os[p].live = true; os[p].remaining = 1;
                    } else if (o.op != M_NONE && o.n > 0) {
                        os[p].type = o.op; os[p].item = o.item; os[p].remaining = o.n; os[p].live = true;
                    }
                }
            }
            // Atomic orders resolve once, in player order.
            for (int p = 0; p < 2; ++p) {
                if (!os[p].live) continue;
                if (os[p].type == M_HIRE) { do_hire(st.farms[p]); os[p].live = false; }
                else if (os[p].type == M_BUY_LAND) { do_buy_land(st.farms[p]); os[p].live = false; }
            }

            // Per-unit lockstep: both players see the same pre-commit inventory.
            for (;;) {
                struct Q { bool ok = false; uint8_t type = 0; uint8_t item = 0; int price = 0; };
                Q q[2];
                for (int p = 0; p < 2; ++p) {
                    if (!os[p].live || os[p].remaining <= 0) continue;
                    uint8_t t = os[p].type, it = os[p].item;
                    if (t == M_SELL && is_product(it)) {
                        q[p] = { true, t, it, market_price(it, st.market.inventory[it]) };
                    } else if (t == M_BUY_PRODUCT && (it == WHEAT || it == FERTILIZER)) {
                        // Quoted at post-buy inventory so a round trip nets zero.
                        q[p] = { true, t, it, market_price(it, st.market.inventory[it] - 1) };
                    } else if (t == M_BUY_SEED && is_crop(it)) {
                        q[p] = { true, t, it, CROPS[it].seed };
                    } else if (t == M_BUY_ANIMAL && is_animal(it)) {
                        q[p] = { true, t, it, ANIMALS[it - GOOSE].cost };
                    } else {
                        os[p].live = false;
                    }
                }
                if (!q[0].ok && !q[1].ok) break;
                bool committed = false;
                for (int p = 0; p < 2; ++p) {
                    if (!q[p].ok) continue;
                    if (commit_unit(q[p].type, q[p].item, q[p].price, st.farms[p])) {
                        os[p].remaining -= 1; committed = true;
                    } else {
                        os[p].live = false;
                    }
                }
                if (!committed) break;
            }
            refresh_prices();
        }
    }

    bool commit_unit(uint8_t op, uint8_t item, int price, Farm& f) {
        switch (op) {
            case M_SELL:
                if (f.shed[item] <= 0) return false;
                f.shed[item] -= 1; f.shed_total -= 1;
                f.money += price;
                f.sold_units[item] += 1;
                f.sell_revenue += price;
                if (price > 1) st.market.inventory[item] += 1;   // $1 sales don't add supply
                return true;
            case M_BUY_PRODUCT:
                if (f.money < price) return false;
                if (f.shed_total >= cfg.shed_capacity) return false;
                f.money -= price; f.total_spend += price;
                f.shed[item] += 1; f.shed_total += 1;
                st.market.inventory[item] -= 1;
                return true;
            case M_BUY_SEED:
                if (f.money < price) return false;
                f.money -= price; f.total_spend += price; f.seeds[item] += 1;
                return true;
            case M_BUY_ANIMAL:
                if (f.money < price) return false;
                if (f.shed_total >= cfg.shed_capacity) return false;
                f.money -= price; f.total_spend += price;
                f.shed[item] += 1; f.shed_total += 1;
                return true;
        }
        return false;
    }

    void refresh_prices() {
        for (int i = 0; i < N_PRODUCTS; ++i)
            st.market.prices[i] = market_price(i, st.market.inventory[i]);
    }

    void do_hire(Farm& f) {
        int cost = cfg.hire_mult * fib(f.hires_today);
        if (f.money < cost || f.n_units >= MAX_UNITS) return;
        f.money -= cost; f.total_spend += cost;
        f.hires_today += 1;
        // Spawn on the first free shed-access tile (NWSE), ties by occupancy.
        int acc[4][2]; shed_access_tiles(cfg.board_size, acc);
        int occ[4] = {0,0,0,0};
        for (int u = 0; u < f.n_units; ++u)
            for (int k = 0; k < 4; ++k)
                if (f.pos_x[u] == acc[k][0] && f.pos_y[u] == acc[k][1]) occ[k]++;
        int best = 0;
        for (int k = 1; k < 4; ++k) if (occ[k] < occ[best]) best = k;
        int idx = f.n_units++;
        f.pos_x[idx] = static_cast<int8_t>(acc[best][0]);
        f.pos_y[idx] = static_cast<int8_t>(acc[best][1]);
        f.inv_clear(idx);
    }

    void do_buy_land(Farm& f) {
        int extra = f.n_quadrants - 1;
        if (extra >= 3) return;
        int cost = LAND_PRICES[extra];
        if (f.money < cost) return;
        f.money -= cost; f.total_spend += cost;
        int quad = LAND_ORDER[extra];
        f.n_quadrants += 1;
        for (int y = 0; y < cfg.board_size; ++y)
            for (int x = 0; x < cfg.board_size; ++x)
                if (quadrant_of(x, y, cfg.board_size) == quad && f.tiles[y][x].kind == T_LOCKED)
                    f.tiles[y][x].kind = T_EMPTY;
    }

    // ------------------------------------------------------------ town / decay
    void town_consume(int step_i) {
        if (step_i % cfg.shop_sell_interval == 0) {
            for (int s = 0; s < st.n_shops; ++s) {
                uint16_t mask = SHOP_MASK[st.shops[s]];
                int mult = SHOP_MULT[st.shops[s]];
                for (int it = 0; it < N_PRODUCTS; ++it)
                    if (mask & (1u << it)) st.market.inventory[it] -= mult;
            }
        }
        if (step_i % cfg.center_sell_interval == 0) {
            for (int it = 0; it < N_PRODUCTS; ++it)
                if (it != FERTILIZER) st.market.inventory[it] -= 1;
        }
        refresh_prices();
    }

    void decay_plants(Farm& f, int step_i) {
        for (int y = 0; y < cfg.board_size; ++y)
            for (int x = 0; x < cfg.board_size; ++x) {
                Tile& t = f.tiles[y][x];
                if (t.kind != T_PLANT) continue;
                if (t.max_lifespan_step < 0 || step_i < t.max_lifespan_step) continue;
                if ((step_i - t.max_lifespan_step) % 2 != 0) continue;
                t.yield_units -= 1;
                if (t.yield_units <= 0) { Tile w{}; w.kind = T_WEED; t = w; }
            }
    }

    void end_of_day(int day) {
        PyRandom rng((cfg.seed * 1000003ull) ^ static_cast<uint64_t>(day));
        for (int p = 0; p < 2; ++p) {
            Farm& f = st.farms[p];
            daily_refresh_plants(f, day);
            daily_refresh_animals(f, day);
            spawn_weeds(f, rng);
            drop_inventories(f);
            int h = cfg.board_size / 2;
            f.n_units = 1;
            f.pos_x[0] = static_cast<int8_t>(h - 1);
            f.pos_y[0] = static_cast<int8_t>(h - 1);
            f.hires_today = 0;
            for (int u = 0; u < MAX_UNITS; ++u) f.inv_clear(u);
        }
        int next_day = day + 1;
        if (next_day > 0 && next_day % cfg.shop_unlock_interval == 0 && st.n_shops < MAX_SHOP_INSTANCES) {
            uint8_t shop = static_cast<uint8_t>(rng.choice_index(N_SHOPS));
            if (cfg.pin_shops && st.n_shops < cfg.n_pinned_shops)
                shop = cfg.pinned_shops[st.n_shops];
            st.shops[st.n_shops++] = shop;
        }
    }

    void daily_refresh_plants(Farm& f, int day) {
        int next_day = day + 1;
        for (int y = 0; y < cfg.board_size; ++y)
            for (int x = 0; x < cfg.board_size; ++x) {
                Tile& t = f.tiles[y][x];
                if (t.kind != T_PLANT) continue;
                bool was_watered = t.watered_today;
                t.consecutive_dry = was_watered ? 0 : static_cast<int8_t>(t.consecutive_dry + 1);
                t.watered_today = false;
                if (t.consecutive_dry >= 2) { Tile w{}; w.kind = T_WEED; t = w; continue; }
                const CropDef& cd = CROPS[t.what];
                if (!cd.ongoing) continue;
                int since = next_day - t.planted_day - cd.first_yield_day;
                if (since < 0) continue;
                if (since % cd.interval != 0) continue;
                int count = since / cd.interval + 1;
                if (count > cd.max_yield) continue;
                bool fert = was_watered && t.fertilized_until_day >= day;
                t.yield_units = static_cast<int8_t>(std::min(cd.max_yield, t.yield_units + (fert ? 2 : 1)));
                if (count == cd.max_yield) t.max_lifespan_step = (next_day + 1) * cfg.turns_per_day;
            }
    }

    void daily_refresh_animals(Farm& f, int day) {
        int next_day = day + 1;
        for (int y = 0; y < cfg.board_size; ++y)
            for (int x = 0; x < cfg.board_size; ++x) {
                Tile& t = f.tiles[y][x];
                if (!t.has_animal) continue;
                t.consecutive_dry = t.fed_today ? 0 : static_cast<int8_t>(t.consecutive_dry + 1);
                if (t.consecutive_dry >= 2) {           // escapes; structure remains
                    TileKind k = t.kind;
                    Tile s{}; s.kind = k; t = s;
                    continue;
                }
                const AnimalDef& ad = ANIMALS[t.what - GOOSE];
                int since = next_day - t.planted_day - ad.first_yield_day;
                if (since >= 0 && since % ad.interval == 0) {
                    int bonus = t.fed_today ? t.pending_care_bonus : 0;
                    t.yield_units = static_cast<int8_t>(std::min(ad.max_held, t.yield_units + 1 + bonus));
                    t.pending_care_bonus = 0;
                }
                if (t.cared_today && t.fed_today) t.pending_care_bonus += 1;
                t.fertilizer_available = true;
                t.fed_today = false;
                t.cared_today = false;
            }
    }

    void spawn_weeds(Farm& f, PyRandom& rng) {
        for (int y = 0; y < cfg.board_size; ++y)
            for (int x = 0; x < cfg.board_size; ++x)
                if (f.tiles[y][x].kind == T_EMPTY && rng.random() < cfg.weed_chance)
                    f.tiles[y][x].kind = T_WEED;
    }

    void drop_inventories(Farm& f) {
        // Insertion order again: with the shed near capacity this decides which
        // goods survive the day and which are discarded.
        for (int u = 0; u < f.n_units; ++u) {
            uint8_t keys[N_ITEMS];
            int nk = f.inv_nkeys[u];
            for (int k = 0; k < nk; ++k) keys[k] = f.inv_keys[u][k];
            for (int k = 0; k < nk; ++k) {
                int it = keys[k];
                if (f.inv[u][it] <= 0) { f.inv_erase(u, it); continue; }
                int room = std::max(0, cfg.shed_capacity - f.shed_total);
                int take = std::min<int>(f.inv[u][it], room);
                if (take > 0) { f.shed[it] += take; f.shed_total += take; }
                f.discarded[it] += f.inv[u][it] - take;
                f.inv_erase(u, it);
            }
        }
    }
};

}  // namespace kag


%%writefile submission_bridge.cpp
// SPDX-License-Identifier: Apache-2.0
// Packed Python-observation bridge linked directly with ShopForge SixDay Guard R1.
#include "policy_plugin_abi.hpp"
#include "sim.hpp"

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
    std::uint8_t what = 0;
    std::uint8_t flags = 0;
    std::int8_t consecutive_dry = 0;
    std::int8_t yield_units = 0;
    std::int8_t pending_care_bonus = 0;
    std::int16_t planted_day = 0;
    std::int32_t max_lifespan_step = -1;
    std::int16_t fertilized_until_day = -1;
};

struct PackedFarm {
    double money = 0;
    PackedTile tiles[kag::BOARD][kag::BOARD]{};
    std::int8_t pos_x[kag::MAX_UNITS]{};
    std::int8_t pos_y[kag::MAX_UNITS]{};
    std::int32_t n_units = 1;
    std::int32_t n_quadrants = 1;
    std::int32_t hires_today = 0;
    std::int16_t shed[kag::N_ITEMS]{};
    std::int16_t seeds[kag::N_CROPS]{};
    std::int16_t inv[kag::MAX_UNITS][kag::N_ITEMS]{};
};

struct PackedObservation {
    std::int32_t step = 0;
    std::int32_t day = 0;
    std::int32_t hour = 0;
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
    state.day = observation.day;
    state.hour = observation.hour;
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
        for (int unit = 0; unit < farm.n_units; ++unit) {
            farm.pos_x[unit] = source.pos_x[unit];
            farm.pos_y[unit] = source.pos_y[unit];
        }
        for (int y = 0; y < kag::BOARD; ++y) {
            for (int x = 0; x < kag::BOARD; ++x) {
                const PackedTile& packed = source.tiles[y][x];
                kag::Tile& tile = farm.tiles[y][x];
                tile.kind = static_cast<kag::TileKind>(packed.kind);
                tile.what = packed.what;
                tile.has_animal = (packed.flags & 1u) != 0;
                tile.watered_today = (packed.flags & 2u) != 0;
                tile.fed_today = (packed.flags & 4u) != 0;
                tile.cared_today = (packed.flags & 8u) != 0;
                tile.fertilizer_available = (packed.flags & 16u) != 0;
                tile.consecutive_dry = packed.consecutive_dry;
                tile.yield_units = packed.yield_units;
                tile.pending_care_bonus = packed.pending_care_bonus;
                tile.planted_day = packed.planted_day;
                tile.max_lifespan_step = packed.max_lifespan_step;
                tile.fertilized_until_day = packed.fertilized_until_day;
            }
        }
        farm.shed_total = 0;
        for (int item = 0; item < kag::N_ITEMS; ++item) {
            farm.shed[item] = source.shed[item];
            farm.shed_total += source.shed[item];
        }
        for (int crop = 0; crop < kag::N_CROPS; ++crop)
            farm.seeds[crop] = source.seeds[crop];
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
_CROPS = _ITEMS[:5]
_ITEM_ID = {name: index for index, name in enumerate(_ITEMS)}
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
    _fields_ = [
        ("kind", ctypes.c_uint8),
        ("what", ctypes.c_uint8),
        ("flags", ctypes.c_uint8),
        ("consecutive_dry", ctypes.c_int8),
        ("yield_units", ctypes.c_int8),
        ("pending_care_bonus", ctypes.c_int8),
        ("planted_day", ctypes.c_int16),
        ("max_lifespan_step", ctypes.c_int32),
        ("fertilized_until_day", ctypes.c_int16),
    ]


class _PackedFarm(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("money", ctypes.c_double),
        ("tiles", _PackedTile * _BOARD * _BOARD),
        ("pos_x", ctypes.c_int8 * _MAX_UNITS),
        ("pos_y", ctypes.c_int8 * _MAX_UNITS),
        ("n_units", ctypes.c_int32),
        ("n_quadrants", ctypes.c_int32),
        ("hires_today", ctypes.c_int32),
        ("shed", ctypes.c_int16 * len(_ITEMS)),
        ("seeds", ctypes.c_int16 * len(_CROPS)),
        ("inv", ctypes.c_int16 * len(_ITEMS) * _MAX_UNITS),
    ]


class _PackedObservation(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("step", ctypes.c_int32),
        ("day", ctypes.c_int32),
        ("hour", ctypes.c_int32),
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


def _xy(value):
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        return int(value[0]), int(value[1])
    return int(_read(value, "x", 0) or 0), int(_read(value, "y", 0) or 0)


def _fill_counts(target, mapping, names):
    for index, name in enumerate(names):
        target[index] = int(_read(mapping, name, 0) or 0) if mapping else 0


def _fill_tile(dst, tile):
    dst.max_lifespan_step = -1
    dst.fertilized_until_day = -1
    if tile is None:
        return
    if isinstance(tile, str):
        dst.kind = _KIND_ID.get(tile, 0)
        return
    kind = _read(tile, "kind")
    crop = _read(tile, "crop")
    animal = _read(tile, "animal")
    if kind == "PLANT" or crop:
        dst.kind = _KIND_ID["PLANT"]
        if crop:
            dst.what = _ITEM_ID[str(crop)]
        dst.flags = 2 if _read(tile, "watered_today") else 0
        dst.consecutive_dry = int(_read(tile, "consecutive_unwatered", 0) or 0)
        dst.yield_units = int(_read(tile, "yield_units", 0) or 0)
        dst.planted_day = int(_read(tile, "planted_day", 0) or 0)
        lifespan = _read(tile, "max_lifespan_step", -1)
        dst.max_lifespan_step = int(-1 if lifespan is None else lifespan)
        fertilized = _read(tile, "fertilized_until_day", -1)
        dst.fertilized_until_day = int(-1 if fertilized is None else fertilized)
        return
    if animal is not None:
        dst.kind = _KIND_ID.get(kind, _KIND_ID["PASTURE"])
        dst.what = _ITEM_ID[str(animal)]
        flags = 1
        if _read(tile, "fed_today"):
            flags |= 4
        if _read(tile, "cared_today"):
            flags |= 8
        if _read(tile, "fertilizer_available"):
            flags |= 16
        dst.flags = flags
        dst.consecutive_dry = int(_read(tile, "consecutive_unfed", 0) or 0)
        dst.yield_units = int(_read(tile, "yield_units", 0) or 0)
        dst.pending_care_bonus = int(_read(tile, "pending_care_bonus", 0) or 0)
        dst.planted_day = int(_read(tile, "placed_day", 0) or 0)
        return
    dst.kind = _KIND_ID.get(kind, 0)


def _pack_observation(observation, seat):
    packed = _PackedObservation()
    step = int(_read(observation, "step", 0) or 0)
    packed.step = step
    packed.day = int(_read(observation, "day", step // 24) or 0)
    packed.hour = int(_read(observation, "hour", step % 24) or 0)
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
        for unit, position in enumerate(positions[:dest.n_units]):
            x, y = _xy(position)
            dest.pos_x[unit] = x
            dest.pos_y[unit] = y
        dest.n_quadrants = len(list(_read(farm, "unlocked_quadrants", []) or []))
        dest.hires_today = int(_read(farm, "hires_today", 0) or 0)
        tiles = list(_read(farm, "tiles", []) or [])
        for y, row in enumerate(tiles[:_BOARD]):
            for x, tile in enumerate(list(row or [])[:_BOARD]):
                _fill_tile(dest.tiles[y][x], tile)

    private = _read(observation, "private", {}) or {}
    own = packed.farms[seat]
    _fill_counts(own.shed, _read(private, "shed", {}) or {}, _ITEMS)
    _fill_counts(own.seeds, _read(private, "seeds", {}) or {}, _CROPS)
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
    "expected_tape_include_sha256": "abd24b0695c6e2ab4a5551959b453ffdbddfbe757e40d4c5cb83212164215afa",
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

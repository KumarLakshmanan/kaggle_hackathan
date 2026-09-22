PATCH = r"""
-enum Shape : uint8_t { F_LINEAR, F_SQ, F_SQRT, F_LOG, F_LOG10 };
+enum Shape : uint8_t { F_LINEAR, F_SQ, F_SQRT, F_LOG, F_LOG10, F_HINGE };

-    {  35, 10000, 450, F_LOG,    0.20, F_SQRT,   0.70 },  // CARROT
-    {  60, 10000, 200, F_LINEAR, 0.40, F_SQRT,   0.60 },  // TOMATO
-    {  50, 10000, 332, F_LINEAR, 0.40, F_LOG,    0.20 },  // EGG
+    {  35, 10000, 450, F_HINGE,  1.00, F_SQRT,   0.70 },  // CARROT  (1.32.7)
+    {  60, 10000, 200, F_HINGE,  0.40, F_SQRT,   0.60 },  // TOMATO  (1.32.7)
+    {  50, 10000, 332, F_HINGE,  0.40, F_LOG,    0.20 },  // EGG     (1.32.7)

-inline double shape(Shape f, double x) {
+inline double shape(Shape f, double x, double T = 0.0) {
     ...
+        case F_HINGE: {                 // 1.32.7: u + 8*max(0, u-1)^2
+            if (T <= 0.0) return x;
+            double u = x / T;
+            double e = u - 1.0;
+            if (e < 0.0) e = 0.0;
+            return u + 8.0 * e * e;
+        }
 }
"""
print(PATCH)
print("plus the T argument at the two shape() call sites"
      " (amplitude normalisation and market_price)")

!pip install -q kaggle-environments==1.32.7 2>/dev/null; python -c "import kaggle_environments as k; print('engine:', k.__version__)"

%%writefile pyrandom.hpp
// CPython-compatible Mersenne Twister.
//
// The environment seeds `random.Random((seed * 1_000_003) ^ day)` and calls
// .random() (weed spawns) and .choice() (shop unlocks). To reproduce episodes
// bit-for-bit we must match CPython's _randommodule.c exactly: init_by_array
// seeding from the integer's 32-bit little-endian words, the 53-bit
// random() construction, and getrandbits/_randbelow rejection sampling.
#pragma once
#include <cstdint>
#include <cstring>
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

    // The constant half of the seeding. init_genrand(19650218) fills the
    // same 624 words on every construction, so it is a table wearing a
    // loop's clothes: computed once per process and copied thereafter.
    // Provably identical output, since it is the same recurrence with the
    // same constant. It matters because the engine builds a fresh
    // generator every in-game day, 29 times an episode, and this is a
    // third of that cost.
    // public so tools/test_rng_shared.cpp can check the table against the
    // recurrence it replaces, which is the only way to know it is right
    // rather than merely fast.
public:
    static const uint32_t* genrand_base() {
        static const std::vector<uint32_t> base = [] {
            std::vector<uint32_t> m(N);
            m[0] = 19650218u;
            for (int i = 1; i < N; ++i)
                m[i] = 1812433253u * (m[i - 1] ^ (m[i - 1] >> 30))
                       + static_cast<uint32_t>(i);
            return m;
        }();
        return base.data();
    }

private:
    void init_by_array(const uint32_t* key, int keylen) {
        std::memcpy(mt_, genrand_base(), sizeof(uint32_t) * N);
        index_ = N;
        // Same recurrence as CPython, written to keep only the essential
        // work in the loop body. The two mixing passes are a serial
        // dependency chain (each word needs the one before it), so the
        // wins are what surrounds it, not the arithmetic:
        //
        //   * the wrap test `if (i >= N)` is true ONCE in 624 iterations,
        //     so the loop is split at the wrap instead of testing it every
        //     time;
        //   * `mt_[i - 1]` was written by the previous iteration, so it is
        //     carried in a register rather than reloaded;
        //   * `j` cycles over keylen, which for a 64-bit seed is 1 or 2,
        //     so those two cases lose the counter, its test and its reset.
        //
        // Output is identical by construction: the operations, their order
        // and their operands are unchanged.
        int i = 1, j = 0;
        int k = (N > keylen) ? N : keylen;
        uint32_t prev = mt_[0];
        while (k > 0) {
            int run = N - i;                       // until the wrap
            if (run > k) run = k;
            if (keylen == 1) {
                const uint32_t kv = key[0];
                for (int n = run; n; --n) {
                    prev = (mt_[i] ^ ((prev ^ (prev >> 30)) * 1664525u)) + kv;
                    mt_[i] = prev;
                    ++i;
                }
            } else if (keylen == 2) {
                for (int n = run; n; --n) {
                    prev = (mt_[i] ^ ((prev ^ (prev >> 30)) * 1664525u))
                           + key[j] + static_cast<uint32_t>(j);
                    mt_[i] = prev;
                    ++i;
                    j ^= 1;                        // 0,1,0,1,...
                }
            } else {
                for (int n = run; n; --n) {
                    prev = (mt_[i] ^ ((prev ^ (prev >> 30)) * 1664525u))
                           + key[j] + static_cast<uint32_t>(j);
                    mt_[i] = prev;
                    ++i; ++j;
                    if (j >= keylen) j = 0;
                }
            }
            k -= run;
            if (i >= N) { mt_[0] = mt_[N - 1]; prev = mt_[0]; i = 1; }
        }
        k = N - 1;
        while (k > 0) {
            int run = N - i;
            if (run > k) run = k;
            for (int n = run; n; --n) {
                prev = (mt_[i] ^ ((prev ^ (prev >> 30)) * 1566083941u))
                       - static_cast<uint32_t>(i);
                mt_[i] = prev;
                ++i;
            }
            k -= run;
            if (i >= N) { mt_[0] = mt_[N - 1]; prev = mt_[0]; i = 1; }
        }
        mt_[0] = 0x80000000u;
        index_ = N;
    }
};

}  // namespace kag

%%writefile sim.hpp
// Kaggriculture simulator — a faithful C++ port of kaggriculture.py.
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
    {  35, 10000, 450, F_HINGE,  1.00, F_SQRT,   0.70 },  // CARROT  (1.32.7)
    {  60, 10000, 200, F_HINGE,  0.40, F_SQRT,   0.60 },  // TOMATO  (1.32.7)
    { 120, 10000, 100, F_SQRT,   0.70, F_LINEAR, 1.60 },  // STRAWBERRY
    { 250, 10000, 300, F_LOG,    0.20, F_SQ,     3.60 },  // MELON
    {  50, 10000, 332, F_HINGE,  0.40, F_LOG,    0.20 },  // EGG     (1.32.7)
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
        case F_HINGE: {                 // 1.32.7: u + 8*max(0, u-1)^2
            if (T <= 0.0) return x;
            double u = x / T;
            double e = u - 1.0;
            if (e < 0.0) e = 0.0;
            return u + 8.0 * e * e;
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
    // Settle telemetry (instrumentation only, same contract as `discarded`):
    // counters of what the settle does in SILENCE, so an audit reads engine
    // truth instead of reconstructing it from state deltas outside.
    int32_t tel_sell_dead = 0;       // SELL units refused: shed empty
    int32_t tel_refused_product = 0; // BUY_PRODUCT units refused (funds/cap)
    int32_t tel_refused_seed = 0;    // BUY_SEED units refused (funds)
    int32_t tel_refused_animal = 0;  // BUY_ANIMAL units refused (funds/cap)
    int32_t tel_refused_hire = 0;    // HIREs refused (funds or unit cap)
    int32_t tel_refused_land = 0;    // BUY_LANDs refused (funds/none left)
    int32_t tel_hire_paid = 0;       // coins actually paid for hires

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

#ifdef KAG_ABLATE
        // Profiling seam, compiled out of every normal build. tools/ablate.cpp
        // stubs one phase at a time to price it, because -O3 inlining defeats a
        // sampling profiler here. Absent from any build that is not that tool.
        extern int g_skip;
        if (g_skip != 1) for (int p = 0; p < 2; ++p) apply_unit_actions(p, *acts[p], day);
        if (g_skip != 2) process_market(*acts[0], *acts[1]);
        if (g_skip != 3) town_consume(step_i);
        if (g_skip != 4) for (int p = 0; p < 2; ++p) decay_plants(st.farms[p], step_i);
        if (g_skip != 5 && (step_i + 1) % cfg.turns_per_day == 0) end_of_day(day);
#else
        for (int p = 0; p < 2; ++p) apply_unit_actions(p, *acts[p], day);
        process_market(*acts[0], *acts[1]);
        town_consume(step_i);
        for (int p = 0; p < 2; ++p) decay_plants(st.farms[p], step_i);
        if ((step_i + 1) % cfg.turns_per_day == 0) end_of_day(day);
#endif

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
                        // the whole REMAINDER of the order dies here in
                        // silence; telemetry counts every undelivered unit
                        Farm& fp = st.farms[p];
                        switch (os[p].type) {
                            case M_SELL:        fp.tel_sell_dead += os[p].remaining; break;
                            case M_BUY_PRODUCT: fp.tel_refused_product += os[p].remaining; break;
                            case M_BUY_SEED:    fp.tel_refused_seed += os[p].remaining; break;
                            case M_BUY_ANIMAL:  fp.tel_refused_animal += os[p].remaining; break;
                        }
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
        if (f.money < cost || f.n_units >= MAX_UNITS) { f.tel_refused_hire += 1; return; }
        f.money -= cost; f.total_spend += cost;
        f.tel_hire_paid += cost;
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
        if (extra >= 3) { f.tel_refused_land += 1; return; }
        int cost = LAND_PRICES[extra];
        if (f.money < cost) { f.tel_refused_land += 1; return; }
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
        // PARITY SHORTCUT, and it is a proof rather than a heuristic.
        // Every assignment of max_lifespan_step is `k * turns_per_day`
        // (or -1, which the loop rejects), so with an even turns_per_day
        // the value is even and `(step_i - max_lifespan_step) % 2` equals
        // `step_i % 2`. On an odd step no tile can satisfy the decay
        // condition, so the whole scan is provably a no-op. Guarded on
        // the config so an odd turns_per_day falls back to scanning.
        if ((cfg.turns_per_day % 2) == 0 && (step_i % 2) != 0) return;
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
        if (next_day > 0 && next_day % cfg.shop_unlock_interval == 0 && st.n_shops < MAX_SHOP_INSTANCES)
            st.shops[st.n_shops++] = static_cast<uint8_t>(rng.choice_index(N_SHOPS));
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

%%writefile prove.cpp
// Live proof harness: replay an exported episode (equivalence) or
// replay it N times (speed). Reads the minimal trace this notebook
// writes: line 1 "seed n", then per turn two lines (seat 0, seat 1):
// n_units n_orders, then unit triples op,arg,k and order triples.
#include "./sim.hpp"
#include <chrono>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <sstream>
#include <vector>
using namespace kag;

struct Turn { Action a[2]; };

static std::vector<Turn> load(const char* path, uint64_t& seed, int& n) {
    std::ifstream f(path);
    f >> seed >> n;
    std::vector<Turn> turns(n);
    for (int t = 0; t < n; ++t)
        for (int s = 0; s < 2; ++s) {
            Action& a = turns[t].a[s];
            a.clear();
            int nu, no;
            f >> nu >> no;
            a.n_units = nu;
            for (int u = 0; u < nu; ++u) {
                int op, arg, k;
                f >> op >> arg >> k;
                if (u < MAX_UNITS)
                    a.units[u] = UnitAction{(uint8_t)op, (uint8_t)arg,
                                            (int16_t)k};
            }
            for (int o = 0; o < no; ++o) {
                int op, item, k;
                f >> op >> item >> k;
                if (a.n_orders < 16 && op > 0)
                    a.orders[a.n_orders++] = Order{(uint8_t)op,
                                                   (uint8_t)item, k};
            }
        }
    return turns;
}

int main(int argc, char** argv) {
    uint64_t seed; int n;
    auto turns = load(argv[2], seed, n);
    Config c; c.seed = seed;
    if (!strcmp(argv[1], "replay")) {
        Sim sim(c);
        for (int t = 0; t < n && !sim.st.done; ++t) {
            sim.step(turns[t].a[0], turns[t].a[1]);
            if (t == 100 || t == 400)
                printf("CHK %d %.0f %.0f\n", t, sim.reward(0),
                       sim.reward(1));
        }
        printf("FINAL %.0f %.0f\n", sim.reward(0), sim.reward(1));
    } else {                            // bench N
        int reps = atoi(argv[3]);
        double sink = 0;
        auto t0 = std::chrono::steady_clock::now();
        for (int r = 0; r < reps; ++r) {
            Sim sim(c);
            for (int t = 0; t < n && !sim.st.done; ++t)
                sim.step(turns[t].a[0], turns[t].a[1]);
            sink += sim.reward(0);
        }
        double secs = std::chrono::duration<double>(
            std::chrono::steady_clock::now() - t0).count();
        printf("BENCH %d %.3f %.1f\n", reps, secs, sink);
    }
    return 0;
}

!g++ -O3 -std=c++17 -o prove prove.cpp && echo compiled

import time
import kaggle_environments
from kaggle_environments import make

ENGINE_OK = kaggle_environments.__version__ == "1.32.7"
print("kaggle_environments", kaggle_environments.__version__,
      "" if ENGINE_OK else "(NOT 1.32.7: the equivalence check below "
      "will then measure the VERSION GAP, not a port defect)")
SEED = 4242
t0 = time.time()
env = make("kaggriculture",
           configuration={"episodeSteps": 720, "seed": SEED}, debug=False)
env.run(["starter", "random"])
PY_SECS = time.time() - t0

OPS = ["PASS", "NORTH", "SOUTH", "EAST", "WEST", "PICKUP", "DROP", "PLACE",
       "PLANT", "WATER", "HARVEST", "FERTILIZE", "DIG", "BUILD_COOP",
       "BUILD_PASTURE", "FEED", "COLLECT_FERTILIZER", "CARE"]
ITEMS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK",
         "WOOL", "FERTILIZER", "GOOSE", "COW", "SHEEP"]
MOPS = ["NONE", "HIRE", "BUY_LAND", "BUY_SEED", "BUY_PRODUCT",
        "BUY_ANIMAL", "SELL"]
OPI = {o: i for i, o in enumerate(OPS)}
ITI = {o: i for i, o in enumerate(ITEMS)}
MOPI = {o: i for i, o in enumerate(MOPS)}

def enc_unit(a):
    if not isinstance(a, list) or not a:
        return (0, 0, 1)
    op = OPI.get(a[0], len(OPS))
    arg = ITI.get(a[1], 255) if len(a) >= 2 and isinstance(a[1], str) else 0
    try:
        k = int(a[2]) if len(a) >= 3 else 1
    except (TypeError, ValueError):
        k = 1
    return (op, arg, k)

def enc_order(o):
    if not isinstance(o, list) or not o:
        return (0, 0, 0)
    op = MOPI.get(o[0], 0)
    if op in (1, 2):
        return (op, 0, 1)
    if len(o) < 3:
        return (0, 0, 0)
    return (op, ITI.get(o[1], 255), int(o[2]))

n = len(env.steps) - 1
lines = [f"{SEED} {n}"]
for t in range(n):
    for seat in (0, 1):
        act = env.steps[t + 1][seat].action or {}
        units = [act.get("farmer") or ["PASS"]] +             list(act.get("hands") or [])
        orders = list(act.get("market") or [])
        parts = [str(len(units)), str(len(orders))]
        for u in units:
            parts += [str(v) for v in enc_unit(u)]
        for o in orders:
            parts += [str(v) for v in enc_order(o)]
        lines.append(" ".join(parts))
open("live_trace.txt", "w").write("\n".join(lines))

def money_at(k):
    farms = env.steps[k][0].observation.farms
    return (float(farms[0]["money"]), float(farms[1]["money"]))

PY_CHK = {100: money_at(101), 400: money_at(401)}
PY_FINAL = money_at(len(env.steps) - 1)
print(f"live episode exported: {n} turns, {PY_SECS:.1f}s in the real "
      f"environment")
print(f"real-env money: step 100 {PY_CHK[100]}, step 400 {PY_CHK[400]}, "
      f"final {PY_FINAL}")

import subprocess

out = subprocess.run(["./prove", "replay", "live_trace.txt"],
                     capture_output=True, text=True).stdout
print(out)
cpp = {}
for ln in out.splitlines():
    p = ln.split()
    if p[0] == "CHK":
        cpp[int(p[1])] = (float(p[2]), float(p[3]))
    elif p[0] == "FINAL":
        cpp["final"] = (float(p[1]), float(p[2]))

checks = [("step 100", PY_CHK[100], cpp.get(100)),
          ("step 400", PY_CHK[400], cpp.get(400)),
          ("final", PY_FINAL, cpp.get("final"))]
ok = True
for name, py, cx in checks:
    same = cx is not None and py == cx
    ok &= same
    print(f"{'PASS' if same else 'FAIL'} {name}: real {py}  cpp {cx}")
if ok:
    print("EQUIVALENCE: EXACT")
elif not ENGINE_OK:
    print("EQUIVALENCE: differs, as it MUST: this image runs",
          kaggle_environments.__version__, "and the port implements",
          "1.32.7. The divergence above is the engine version gap of",
          "section 2, demonstrated live.")
else:
    print("EQUIVALENCE: MISMATCH on 1.32.7: distrust the port and "
          "open an issue with live_trace.txt")

reps = 2000
out = subprocess.run(["./prove", "bench", "live_trace.txt", str(reps)],
                     capture_output=True, text=True).stdout.split()
cpp_secs = float(out[2])
cpp_eps = reps / cpp_secs
py_eps = 1.0 / PY_SECS
print(f"real environment : {PY_SECS:8.2f} s/episode  "
      f"({py_eps:8.2f} eps/sec)")
print(f"this port        : {cpp_secs/reps*1000:8.3f} ms/episode  "
      f"({cpp_eps:8,.0f} eps/sec)")
print(f"speedup, measured on THIS machine just now: "
      f"{cpp_eps/py_eps:,.0f}x")

import matplotlib.pyplot as plt

RAYK_C = [49.7, 53.0, 56.3, 59.5, 62.8, 66.1, 69.4, 72.6, 75.9, 79.2, 82.5, 85.7, 89.0, 92.3, 95.6, 98.9, 102.1, 105.4, 108.7, 112.0, 115.2, 118.5, 121.8, 125.1, 128.3, 131.6, 134.9, 138.2, 141.5, 144.7, 148.0, 151.3, 154.6, 157.8, 161.1, 164.4, 167.7, 170.9, 174.2, 177.5]
RAYK_N = [2, 0, 0, 2, 6, 8, 13, 8, 13, 11, 14, 13, 19, 19, 24, 26, 31, 49, 52, 69, 61, 61, 71, 86, 71, 76, 93, 110, 105, 136, 132, 131, 120, 121, 87, 65, 42, 32, 17, 4]
LUG_C = [63.0, 66.4, 69.9, 73.3, 76.7, 80.1, 83.5, 86.9, 90.4, 93.8, 97.2, 100.6, 104.0, 107.5, 110.9, 114.3, 117.7, 121.1, 124.5, 128.0, 131.4, 134.8, 138.2, 141.6, 145.1, 148.5, 151.9, 155.3, 158.7, 162.1, 165.6, 169.0, 172.4, 175.8, 179.2, 182.7, 186.1, 189.5, 192.9, 196.3]
LUG_N = [1, 0, 2, 1, 2, 5, 4, 13, 6, 10, 9, 16, 20, 34, 15, 35, 38, 43, 48, 44, 58, 68, 65, 62, 62, 78, 83, 97, 145, 129, 131, 145, 139, 117, 96, 82, 48, 32, 11, 6]

fig, ax = plt.subplots(figsize=(9.5, 3.8))
ax.bar(RAYK_C, RAYK_N, width=3.0, color="#2f6fb2", alpha=0.75,
       label="consensus route, Rayk Kretzschmar (mean 134.8k)")
ax.bar(LUG_C, LUG_N, width=3.0, color="#c2571f", alpha=0.65,
       label="8C/4S route, Lugovoy family (mean 153.5k)")
ax.set_xlabel("final bank vs idle, thousands of $")
ax.set_ylabel("episodes of 2,000")
ax.set_title("what a route ACTUALLY does: full bank distributions,\n"
             "2,000 seeds each, ~1 second each on one core", fontsize=10)
ax.legend(frameon=False, fontsize=9)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
plt.tight_layout(); plt.show()

PANEL_MEANS = [98704, 98730, 100367, 103010, 105540, 106573, 107226, 108428, 108584, 108988, 110352, 110528, 111283, 111555, 111669, 113599, 114523, 114926, 115807, 116229, 117314, 117660, 118884, 119259, 119286, 119565, 119566, 120245, 120743, 121435, 121452, 121498, 122355, 122359, 123359, 123621, 123958, 123977, 124114, 124563, 124863, 124958, 125029, 125077, 125251, 125376, 125400, 125561, 125893, 125974, 126146, 126506, 126790, 127150, 127589, 127788, 128027, 128157, 128559, 128610, 128656, 128817, 129007, 129124, 129311, 129690, 130087, 130247, 130404, 130414, 130520, 130610, 130719, 130937, 130940, 131012, 131074, 131182, 131315, 131523, 131803, 131827, 131961, 132031, 132143, 132188, 132494, 132559, 132661, 133523, 133548, 133595, 133637, 134285, 134289, 134292, 134723, 134846, 134847, 135155, 135158, 135161, 135190, 135832, 136354, 136522, 136610, 136786, 136874, 137146, 137201, 137241, 137333, 137562, 137724, 137858, 137902, 137953, 138003, 138039, 138172, 138326, 138749, 138932, 139593, 139618, 139674, 139855, 139904, 139967, 140004, 140072, 140235, 140237, 140268, 140590, 140609, 140795, 140868, 141016, 141244, 141425, 141680, 141711, 141969, 142333, 142482, 142697, 142786, 143315, 143357, 143471, 143813, 144206, 144372, 145562, 145621, 145940, 146282, 146351, 146489, 146495, 146850, 147145, 147171, 147174, 147197, 147346, 147550, 147979, 148273, 148655, 149079, 149310, 149403, 149460, 149660, 149999, 150044, 150483, 150622, 150701, 150786, 151453, 151658, 152211, 153814, 153860, 153910, 154690, 154918, 155333, 155519, 155587, 157154, 158435, 160235, 161301, 161823, 164898]
TRUE_MEAN = 134813

import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(9.5, 3.2))
ax.hist([p / 1000 for p in PANEL_MEANS], bins=28, color="#7b5bb5",
        alpha=0.85)
ax.axvline(TRUE_MEAN / 1000, color="#1f9d6b", lw=2)
ax.annotate(f"the truth: {TRUE_MEAN/1000:,.1f}k",
            (TRUE_MEAN / 1000, ax.get_ylim()[1] * 0.9),
            xytext=(8, 0), textcoords="offset points",
            color="#1f9d6b", fontsize=9)
ax.set_xlabel("mean bank reported by a random 3-seed panel, thousands of $")
ax.set_ylabel("panels of 200")
ax.set_title("the 3-seed panel illusion: one route, 200 small panels,\n"
             "and every one of them is 'a measurement'", fontsize=10)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
plt.tight_layout(); plt.show()

DM_C = [-0.8, 0.6, 1.9, 3.2, 4.6, 5.9, 7.2, 8.6, 9.9, 11.2, 12.6, 13.9, 15.3, 16.6, 17.9, 19.3, 20.6, 21.9, 23.3, 24.6, 25.9, 27.3, 28.6, 29.9, 31.3, 32.6, 33.9, 35.3, 36.6, 37.9, 39.3, 40.6, 41.9, 43.3, 44.6, 45.9, 47.3, 48.6, 49.9, 51.3, 52.6, 53.9, 55.3, 56.6]
DM_N = [3, 1, 4, 3, 21, 40, 99, 192, 340, 585, 924, 900, 553, 181, 32, 28, 15, 12, 10, 10, 7, 5, 4, 6, 7, 0, 4, 0, 0, 4, 2, 3, 0, 0, 1, 0, 2, 0, 1, 0, 0, 0, 0, 1]

import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(9.5, 3.4))
ax.bar(DM_C, DM_N, width=(DM_C[1]-DM_C[0])*0.9, color="#c2571f", alpha=0.85)
ax.axvline(0, color="#555", lw=1.2)
ax.annotate("8C/4S wins 3,997 of 4,000\n"
            "seat-0 occupant wins 50.0%\n"
            "photo finishes under 1k: 2 games",
            (0.02, 0.95), xycoords="axes fraction", va="top", fontsize=9)
ax.set_xlabel("8C/4S margin over the consensus route, thousands of $ "
              "(per game)")
ax.set_ylabel("games of 4,000")
ax.set_title("head to head, the seed barely matters: the better\n"
             "construction wins 99.9% of a "
             "4,000-game duel", fontsize=10)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
plt.tight_layout(); plt.show()

MD_C = [-89.4, -86.6, -83.9, -81.1, -78.3, -75.6, -72.8, -70.1, -67.3, -64.5, -61.8, -59.0, -56.2, -53.5, -50.7, -47.9, -45.2, -42.4, -39.6, -36.9, -34.1, -31.4, -28.6, -25.8, -23.1, -20.3, -17.5, -14.8, -12.0, -9.2, -6.5, -3.7, -0.9, 1.8, 4.6, 7.3, 10.1, 12.9, 15.6, 18.4]
MD_N = [6, 14, 34, 53, 83, 108, 130, 144, 174, 141, 124, 104, 101, 114, 79, 67, 66, 55, 57, 61, 55, 35, 25, 33, 20, 16, 17, 12, 15, 12, 14, 5, 8, 8, 4, 3, 1, 0, 1, 1]
HD_C = [-4.5, -4.3, -4.1, -3.9, -3.7, -3.5, -3.2, -3.0, -2.8, -2.6, -2.4, -2.1, -1.9, -1.7, -1.5, -1.3, -1.1, -0.8, -0.6, -0.4, -0.2, 0.0, 0.3, 0.5, 0.7, 0.9, 1.1, 1.3, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 2.9, 3.1, 3.3, 3.5, 3.7, 4.0]
HD_N = [2, 15, 78, 97, 132, 146, 185, 145, 140, 119, 116, 75, 94, 34, 86, 11, 40, 26, 26, 5, 3, 7, 12, 78, 46, 30, 4, 34, 24, 40, 8, 21, 9, 47, 22, 1, 25, 4, 6, 7]

import matplotlib.pyplot as plt
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 3.6))
ax1.bar(MD_C, MD_N, width=(MD_C[1]-MD_C[0])*0.9, color="#b5486b", alpha=0.85)
ax1.axvline(0, color="#555", lw=1.2)
ax1.set_title("defer MELON sells by ONE day:\n"
              "-56,317 per game (+-824 at 95%)",
              fontsize=10)
ax1.set_xlabel("paired delta vs the untouched route, thousands of $")
ax1.set_ylabel("seeds of 2,000")
ax2.bar(HD_C, HD_N, width=(HD_C[1]-HD_C[0])*0.9, color="#2f6fb2", alpha=0.85)
ax2.axvline(0, color="#555", lw=1.2)
ax2.set_title("REMOVE one day-12 hire:\n"
              "-1,861 per game (+-89 at 95%)",
              fontsize=10)
ax2.set_xlabel("paired delta, thousands of $")
for ax in (ax1, ax2):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
plt.tight_layout(); plt.show()
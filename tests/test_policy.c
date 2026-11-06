// Synthetic fixtures only; no extracted game tables are used by this test.
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "armor_fusion.h"

enum { CATALOG_SIZE = 48 + 3 * 12 + 3 * 8 };
static unsigned char catalog[CATALOG_SIZE + 1];
static void word(size_t offset, unsigned value, unsigned bytes) {
    while (bytes--) { catalog[offset++] = value & 255; value >>= 8; }
}
static void make_catalog(void) {
    memset(catalog, 0, sizeof catalog);
    memcpy(catalog, "AFUS", 4); word(4, 2, 4); word(8, 3, 4); word(12, 3, 4);
    for (unsigned i = 0; i < 3; ++i) {
        size_t offset = 48 + i * 12;
        word(offset, i ? 149 + i : 100, 2); word(offset + 2, 1, 1);
        word(offset + 3, 255, 1); word(offset + 4, 1, 1); word(offset + 5, 1, 1);
        word(offset + 6, i ? 196 + i : 0, 2); word(offset + 8, i ? 10 : 0, 2);
    }
    const unsigned categories[] = {197, 197, 198}, items[] = {1202, 1203, 1300}, points[] = {2, 3, 5};
    for (unsigned i = 0; i < 3; ++i) {
        size_t offset = 84 + i * 8;
        word(offset, categories[i], 2); word(offset + 2, items[i], 2); word(offset + 4, points[i], 1);
    }
}
static bool catalog_available(void) {
    FusionPiece piece = {1, 100, 1, FUSION_RANK_UNKNOWN, 1};
    return fusion_classify(&piece);
}
static void load_catalog(void) {
    make_catalog();
    assert(fusion_catalog_parse(catalog, CATALOG_SIZE));
    assert(catalog_available());
}
static void check_recipes(void) {
    FusionPiece base = {1, 100, 1, FUSION_RANK_UNKNOWN, 1};
    FusionPiece appearance = {2, 150, 1, FUSION_RANK_UNKNOWN, 1};
    FusionRecipe first, second, repeated;
    assert(fusion_classify(&base) && base.rank == FUSION_LR);
    assert(fusion_recipe(&base, &appearance, &first));
    assert(base.rank == FUSION_LR && appearance.rank == FUSION_LR);
    assert(first.armor_id == 150 && first.category_id == 197 && first.count == 2);
    assert(first.materials[0].item_id == 1202 && first.materials[0].points == 2);
    assert(first.materials[1].item_id == 1203 && first.materials[1].points == 3);
    appearance.armor_id = 151;
    assert(fusion_recipe(&base, &appearance, &second));
    assert(second.armor_id == 151 && second.category_id == 198 && second.count == 1);
    assert(second.materials[0].item_id == 1300 && second.materials[0].points == 5);
    assert(first.materials[0].item_id == 1202 && first.materials[0].points == 2);
    assert(first.materials[1].item_id == 1203 && first.materials[1].points == 3);
    assert(first.materials != second.materials);
    appearance.armor_id = 150;
    assert(fusion_recipe(&base, &appearance, &repeated));
    assert(repeated.materials == first.materials);
    assert(second.materials[0].item_id == 1300 && second.materials[0].points == 5);
    appearance.slot = 2;
    assert(!fusion_recipe(&base, &appearance, &repeated));
    appearance.slot = 1; appearance.level = 0;
    assert(!fusion_recipe(&base, &appearance, &repeated));
    appearance.level = 1; appearance.armor_id = 100;
    assert(!fusion_recipe(&base, &appearance, &repeated)); // Base-only cannot supply appearance.
    appearance.armor_id = 2048;
    assert(!fusion_recipe(&base, &appearance, &repeated));
    appearance.armor_id = 150;
    assert(!fusion_recipe(NULL, &appearance, &repeated));
    assert(!fusion_recipe(&base, NULL, &repeated));
    assert(!fusion_recipe(&base, &appearance, NULL));
    assert(!fusion_classify(NULL));
    appearance.slot = 6;
    assert(!fusion_classify(&appearance));
}

static void check_invalid_catalogs(void) {
    const struct { size_t offset; unsigned value, bytes; } invalid[] = {
        {0, 0, 1}, {4, 1, 4}, {8, 6145, 4}, {12, 32769, 4},
        {48, 0, 2}, {48, 2048, 2}, {50, 0, 1}, {51, 0, 1},
        {52, 0, 1}, {52, 4, 1}, {53, 0, 1}, {53, 32, 1},
        {54, 1024, 2}, {56, 10, 2}, {68, 9, 2}, {70, 1, 2},
        {60, 100, 2}, {72, 150, 2},
        {84, 0, 2}, {84, 1024, 2}, {86, 0, 2}, {86, 4096, 2}, {88, 0, 1},
        {94, 1202, 2}, {100, 196, 2}, {12, 4, 4},
    };
    for (size_t i = 0; i < sizeof invalid / sizeof invalid[0]; ++i) {
        load_catalog();
        word(invalid[i].offset, invalid[i].value, invalid[i].bytes);
        assert(!fusion_catalog_parse(catalog, CATALOG_SIZE) && !catalog_available());
    }
    load_catalog();
    word(72, 150, 2); word(74, 2, 1); // Sorted but overlapping intervals.
    assert(!fusion_catalog_parse(catalog, CATALOG_SIZE) && !catalog_available());
    for (size_t size = 0; size < CATALOG_SIZE; ++size) {
        load_catalog();
        assert(!fusion_catalog_parse(catalog, size) && !catalog_available());
    }
    load_catalog();
    assert(!fusion_catalog_parse(catalog, sizeof catalog) && !catalog_available());
    load_catalog();
    assert(!fusion_catalog_parse(NULL, CATALOG_SIZE) && !catalog_available());
    load_catalog();
    assert(!fusion_catalog_load() && !catalog_available()); // No embed in this host test.
    puts("armor fusion invalid/truncated/reload catalog checks passed");
}
static void check_level_intervals(void) {
    load_catalog();
    word(48, 617, 2); word(50, 1, 1); word(51, 10, 1); word(52, FUSION_HR, 1);
    word(60, 617, 2); word(62, 11, 1); word(63, 15, 1); word(64, FUSION_G, 1);
    word(72, 1108, 2); word(74, 1, 1); word(75, 5, 1); word(76, FUSION_G, 1);
    assert(fusion_catalog_parse(catalog, CATALOG_SIZE));
    FusionPiece piece = {1, 617, 1, FUSION_RANK_UNKNOWN, 1};
    for (unsigned level = 0; level <= 16; ++level) {
        piece.level = level;
        bool valid = level >= 1 && level <= 15;
        assert(fusion_classify(&piece) == valid);
        if (valid) assert(piece.rank == (level <= 10 ? FUSION_HR : FUSION_G));
    }
    piece.armor_id = 1108;
    for (unsigned level = 0; level <= 6; ++level) {
        piece.level = level;
        assert(fusion_classify(&piece) == (level >= 1 && level <= 5));
        if (level >= 1 && level <= 5) assert(piece.rank == FUSION_G);
    }
    puts("armor fusion level interval checks passed");
}
static uint32_t owned(void *context, uint16_t id) {
    return id == 1202 ? *(unsigned *)context : 0;
}

static void check_policy(void) {
    FusionPiece base = {1, 100, 1, FUSION_LR, 1}, appearance = {2, 150, 1, FUSION_LR, 1};
    FusionMaterial material = {1202, 2};
    FusionRecipe recipe = {150, 197, FUSION_LR, &material, 1};
    FusionSelection selection[] = {{1202, 5}, {1202, 1}};
    unsigned inventory = 5;
    FusionPlan plan;
#define PLAN(n) fusion_plan(&base, &appearance, 1, &recipe, selection, n, owned, &inventory, &plan)
    assert(PLAN(1) && plan.points == 10 && plan.count == 1);
    assert(plan.deductions[0].quantity == 5 && inventory == 5); // Preview is read-only.
    inventory = 4; // Inventory changed after preview: confirmation must reject.
    assert(!PLAN(1) && plan.count == 0 && plan.points == 0);
    inventory = 5;
    selection[0].quantity = 4;
    assert(!PLAN(1));
    selection[0].quantity = 5;
    assert(!PLAN(2)); // Duplicate rows cannot double-spend.
    const bool allowed[3][3] = {{true, false, false}, {false, true, false}, {false, false, true}};
    for (unsigned b = 0; b < 3; ++b) for (unsigned a = 0; a < 3; ++a) {
        base.rank = FUSION_LR + b;
        appearance.rank = recipe.rank = FUSION_LR + a;
        assert(PLAN(1) == allowed[b][a]); // All six mixed-tier directions reject.
        if (!allowed[b][a]) assert(plan.count == 0 && plan.points == 0);
        assert(inventory == 5);
    }
    base.rank = recipe.rank = FUSION_LR;
    appearance.rank = FUSION_RANK_UNKNOWN;
    assert(!PLAN(1));
    appearance.rank = FUSION_LR;
    recipe.rank = FUSION_HR;
    assert(!PLAN(1));
    recipe.rank = FUSION_LR;
    recipe.armor_id = 100;
    assert(!PLAN(1));
    recipe.armor_id = 150;
    appearance.slot = 2;
    assert(!PLAN(1));
    appearance.slot = 1;
    assert(!fusion_plan(&base, &appearance, 0x2001, &recipe, selection, 1,
        owned, &inventory, &plan));
    selection[0].item_id = 1203; // Same monster, wrong material rank/category.
    assert(!PLAN(1));
    selection[0].item_id = 1202;
    selection[0].quantity = 6;
    inventory = 6;
    assert(PLAN(1) && plan.points == 12); // Explicit overpayment allowed.
    selection[0].quantity = 65535;
    inventory = 65535;
    assert(!PLAN(1) && !plan.count);
    selection[0].quantity = 6;
    FusionMaterial duplicates[] = {{1202, 2}, {1202, 3}};
    recipe.materials = duplicates;
    recipe.count = 2;
    assert(!PLAN(1));
    puts("armor fusion policy checks passed");
#undef PLAN
}

static uint32_t owned_ten(void *context, uint16_t id) {
    (void)context; (void)id;
    return 10;
}
static void check_selection_bounds(void) {
    FusionPiece base = {1, 100, 1, FUSION_LR, 1}, appearance = {2, 150, 1, FUSION_LR, 1};
    FusionMaterial materials[FUSION_MAX_MATERIALS + 1];
    FusionSelection selection[FUSION_MAX_MATERIALS + 1];
    for (unsigned i = 0; i < FUSION_MAX_MATERIALS + 1; ++i) {
        materials[i] = (FusionMaterial){i + 1, 1};
        selection[i] = (FusionSelection){i + 1, 1};
    }
    FusionRecipe recipe = {150, 197, FUSION_LR, materials, FUSION_MAX_MATERIALS + 1};
    FusionPlan plan;
    const FusionPlan zero = {0};
#define TRY(b, a, r, s, n, o) fusion_plan(b, a, 1, r, s, n, o, NULL, &plan)
#define REJECT(b, a, r, s, n, o) do { \
    memset(&plan, 0xa5, sizeof plan); \
    assert(!TRY(b, a, r, s, n, o)); \
    assert(!memcmp(&plan, &zero, sizeof plan)); \
} while (0)
    assert(TRY(&base, &appearance, &recipe, selection, FUSION_MAX_MATERIALS, owned_ten));
    assert(plan.points == 10 && plan.count == FUSION_MAX_MATERIALS);
    for (size_t i = 0; i < plan.count; ++i)
        assert(plan.deductions[i].item_id == i + 1 && plan.deductions[i].quantity == 1);
    REJECT(&base, &appearance, &recipe, selection, FUSION_MAX_MATERIALS + 1, owned_ten);
    REJECT(&base, &appearance, &recipe, selection, 0, owned_ten);
    REJECT(&base, &appearance, &recipe, NULL, 1, owned_ten);
    REJECT(&base, &appearance, &recipe, selection, 1, NULL);
    REJECT(NULL, &appearance, &recipe, selection, 1, owned_ten);
    REJECT(&base, NULL, &recipe, selection, 1, owned_ten);
    REJECT(&base, &appearance, NULL, selection, 1, owned_ten);
    selection[0].quantity = 0;
    REJECT(&base, &appearance, &recipe, selection, FUSION_MAX_MATERIALS, owned_ten);
    selection[0].quantity = 11;
    REJECT(&base, &appearance, &recipe, selection, FUSION_MAX_MATERIALS, owned_ten);
    selection[0].quantity = 1; selection[0].item_id = 0;
    REJECT(&base, &appearance, &recipe, selection, FUSION_MAX_MATERIALS, owned_ten);
    selection[0].item_id = 1; materials[0].points = 0;
    REJECT(&base, &appearance, &recipe, selection, FUSION_MAX_MATERIALS, owned_ten);
    materials[0].points = 1; materials[0].item_id = 0;
    REJECT(&base, &appearance, &recipe, selection, FUSION_MAX_MATERIALS, owned_ten);
    materials[0].item_id = 1; appearance.box_index = base.box_index;
    REJECT(&base, &appearance, &recipe, selection, FUSION_MAX_MATERIALS, owned_ten);
    appearance.box_index = 2; appearance.armor_id = base.armor_id;
    REJECT(&base, &appearance, &recipe, selection, FUSION_MAX_MATERIALS, owned_ten);
    assert(!fusion_plan(&base, &appearance, 1, &recipe, selection, 1, owned_ten, NULL, NULL));
    puts("armor fusion selection/output clearing checks passed");
#undef REJECT
#undef TRY
}

int main(void) {
    assert(!catalog_available());
    load_catalog();
    check_recipes();
    check_invalid_catalogs();
    check_level_intervals();
    check_policy();
    check_selection_bounds();
    return 0;
}

#include "armor_fusion.h"
#include <string.h>

#ifndef FUSION_CATALOG_NO_EMBED
#include "catalog.inc"
#endif

enum { ARMOR_LIMIT = 2048, ITEM_LIMIT = 4096, CATEGORY_LIMIT = 1024, MEMBER_LIMIT = 32768 };
typedef struct { unsigned char rank, slots, min_level, max_level; uint16_t category; } Entry;
typedef struct { uint16_t offset, count; } Category;
static Entry entries[ARMOR_LIMIT][3];
static FusionMaterial members[MEMBER_LIMIT];
static Category categories[CATEGORY_LIMIT];
static bool catalog_ready;
static unsigned u16(const unsigned char *p) { return p[0] | p[1] << 8; }
static unsigned u32(const unsigned char *p) { return u16(p) | (uint32_t)u16(p + 2) << 16; }

static const Entry *entry_for(const FusionPiece *piece) {
    unsigned level = piece->level;
    for (int i = 0; i < 3; ++i) {
        const Entry *e = &entries[piece->armor_id][i];
        if (e->rank && level >= e->min_level && level <= e->max_level) return e;
    }
    return NULL;
}

bool fusion_classify(FusionPiece *piece) {
    if (!catalog_ready || !piece || piece->armor_id >= ARMOR_LIMIT || piece->slot < 1 || piece->slot > 5) return false;
    const Entry *entry = entry_for(piece);
    if (!entry || !(entry->slots & (1u << (piece->slot - 1)))) return false;
    piece->rank = entry->rank;
    return true;
}

bool fusion_recipe(FusionPiece *base, FusionPiece *appearance, FusionRecipe *recipe) {
    if (!catalog_ready || !base || !appearance || !recipe || base->armor_id >= ARMOR_LIMIT ||
        appearance->armor_id >= ARMOR_LIMIT || base->slot < 1 || base->slot > 5 ||
        appearance->slot < 1 || appearance->slot > 5) return false;
    const Entry *b = entry_for(base), *a = entry_for(appearance);
    if (!b || !a || !(b->slots & (1u << (base->slot - 1))) ||
        !(a->slots & (1u << (appearance->slot - 1))) || !a->category) return false;
    base->rank = b->rank; appearance->rank = a->rank;
    const Category *category = categories + a->category;
    *recipe = (FusionRecipe){appearance->armor_id, a->category, a->rank,
        members + category->offset, category->count};
    return category->count != 0;
}

bool fusion_catalog_parse(const uint8_t *bytes, size_t size) {
    catalog_ready = false;
    memset(entries, 0, sizeof entries);
    memset(members, 0, sizeof members);
    memset(categories, 0, sizeof categories);
    if (!bytes || size < 48 || memcmp(bytes, "AFUS", 4) || u32(bytes + 4) != 2) return false;
    unsigned armor_count = u32(bytes + 8);
    size_t member_count = u32(bytes + 12);
    // Check count limits before multiplication, including on 32-bit ARM.
    if (armor_count > ARMOR_LIMIT * 3 || member_count > MEMBER_LIMIT ||
        size != 48 + (size_t)armor_count * 12 + member_count * 8) return false;
    const uint8_t *row = bytes + 48;
    unsigned previous = 0;
    bool ok = true;
    for (unsigned i = 0; ok && i < armor_count; ++i, row += 12) {
        unsigned id = u16(row), category = u16(row + 6), points = u16(row + 8);
        unsigned key = id * 256u + row[2];
        ok = id && key > previous && id < ARMOR_LIMIT && row[2] && row[3] >= row[2] &&
            row[4] >= 1 && row[4] <= 3 && row[5] && !(row[5] & ~31) && category < CATEGORY_LIMIT &&
            (category ? points == FUSION_POINTS : points == 0) && !u16(row + 10);
        if (ok) {
            Entry *e = entries[id];
            int slot = 0;
            while (slot < 3 && e[slot].rank) ++slot;
            if (slot == 3 || (slot && e[slot - 1].max_level >= row[2])) ok = false;
            else e[slot] = (Entry){row[4], row[5], row[2], row[3], category};
        }
        previous = key;
    }
    previous = 0;
    for (size_t i = 0; ok && i < member_count; ++i, row += 8) {
        unsigned category = u16(row), item = u16(row + 2), key = category << 16 | item;
        ok = category && category < CATEGORY_LIMIT && item && item < ITEM_LIMIT && row[4] && key > previous;
        if (ok) {
            Category *range = categories + category;
            if (!range->count) range->offset = i;
            ++range->count;
            members[i] = (FusionMaterial){item, row[4]};
        }
        previous = key;
    }
    catalog_ready = ok;
    return ok;
}

bool fusion_catalog_load(void) {
#ifndef FUSION_CATALOG_NO_EMBED
    return fusion_catalog_parse(fusion_catalog_bytes, fusion_catalog_size);
#else
    return fusion_catalog_parse(NULL, 0);
#endif
}

static int valid_rank(enum FusionRank rank) { return rank >= FUSION_LR && rank <= FUSION_G; }

bool fusion_plan(const FusionPiece *base, const FusionPiece *appearance,
    uint32_t native_pair_result, const FusionRecipe *recipe,
    const FusionSelection *selection, size_t count,
    FusionOwned owned, void *context, FusionPlan *out) {
    if (!out) return false;
    memset(out, 0, sizeof *out);
    if (!base || !appearance || !base->armor_id || !appearance->armor_id ||
        base->slot < 1 || base->slot > 5 || base->slot != appearance->slot ||
        base->box_index == appearance->box_index || base->armor_id == appearance->armor_id)
        return false;
    if (!valid_rank(base->rank) || !valid_rank(appearance->rank)) return false;
    if (base->rank != appearance->rank) return false;
    // The native validator returns 1 for a compatible pair. Its other bits
    // include equipment/decorations restrictions and must not be discarded.
    if (native_pair_result != 1) return false;
    if (!recipe || recipe->armor_id != appearance->armor_id ||
        !recipe->category_id || !recipe->materials || !recipe->count ||
        recipe->rank != appearance->rank) return false;
    for (size_t i = 0; i < recipe->count; ++i) {
        if (!recipe->materials[i].item_id || !recipe->materials[i].points)
            return false;
        for (size_t j = 0; j < i; ++j)
            if (recipe->materials[j].item_id == recipe->materials[i].item_id)
                return false;
    }
    if (!owned || !selection || !count) return false;
    if (count > FUSION_MAX_MATERIALS) return false;
    FusionPlan plan = {0};
    for (size_t i = 0; i < count; ++i) {
        const FusionSelection s = selection[i];
        if (!s.item_id || !s.quantity || s.quantity > FUSION_POINTS) return false;
        for (size_t j = 0; j < i; ++j)
            if (selection[j].item_id == s.item_id) return false;
        unsigned points = 0;
        for (size_t j = 0; j < recipe->count; ++j)
            if (recipe->materials[j].item_id == s.item_id) points = recipe->materials[j].points;
        if (!points) return false;
        if (owned(context, s.item_id) < s.quantity) return false;
        plan.points += points * s.quantity;
        plan.deductions[plan.count++] = s;
    }
    if (plan.points < FUSION_POINTS) return false;
    *out = plan;
    return true;
}

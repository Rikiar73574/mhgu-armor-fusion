"""Execute the compiled adapter and MHGU 1.4.0 class helpers under Unicorn.
Requires a private local NSO and lz4; no game code or saves are distributed.
Only metadata lookup/vtable answers are synthetic. The three class helper
bodies, their original-call bridge, and the plugin handlers execute as ARM.
"""
import argparse
import struct
from pathlib import Path

import lz4.block
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_PC, UC_ARM_REG_LR
from test_bridge_arm import ArmImage, ROOT, IMPORTS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('nso', type=Path)
    args = parser.parse_args()
    m = ArmImage(ROOT / 'build/armor_fusion.elf')
    m.u.mem_map(0x00200000, 0x02800000)
    raw = args.nso.read_bytes()
    assert raw[:4] == b'NSO0', 'expected MHGU 1.4.0 exefs/main NSO'
    flags = struct.unpack_from('<I', raw, 12)[0]
    for i in range(3):
        off, address, size = struct.unpack_from('<III', raw, 16 + i * 16)
        length = struct.unpack_from('<I', raw, 0x60 + i * 4)[0]
        data = raw[off:off + length]
        if flags & (1 << i):
            data = lz4.block.decompress(data, uncompressed_size=size)
        assert len(data) == size
        m.u.mem_write(0x00200000 + address, data)
    m.call('forge_onInit')
    assert not m.hooks,'native class hooks installed during initialization'
    m.call('forge_onUpdate',0)
    assert not m.hooks,'native class hooks installed during first update'
    m.call('forge_onUpdate',0)
    hooks = dict(m.hooks)
    # Synthetic armor metadata: BM-only, Gunner-only, universal. Native lookup
    # uses +6 (base), while a separate lookup can use +8 (appearance).
    record, objects = 0x02900000, 0x02901000
    for armor_id, allowed in ((1, (1, 0)), (2, (0, 1)), (3, (1, 1))):
        obj = objects + armor_id * 0x200
        vt = obj + 0x20
        m.write32(obj, vt)
        for method, (slot, value) in enumerate(((0x18, 1), (0xf0, allowed[0]), (0xf4, allowed[1]))):
            fn = IMPORTS + 0x400 + armor_id * 0x40 + method * 8
            m.u.mem_write(fn, struct.pack('<II', 0xe3a00000 | value, 0xe12fff1e))
            m.write32(vt + slot, fn)
    native_pair_result = 1

    def external(u, address, size, context):
        if address == 0x33f03c:
            pointer = u.reg_read(UC_ARM_REG_R1)
            armor_id = struct.unpack('<H', u.mem_read(pointer + 6, 2))[0]
        elif address == 0x33c208:
            armor_id = u.reg_read(UC_ARM_REG_R2)
        elif address == 0x340d60:
            u.reg_write(UC_ARM_REG_R0, native_pair_result)
            u.reg_write(UC_ARM_REG_PC, u.reg_read(UC_ARM_REG_LR))
            return
        else:
            return
        u.reg_write(UC_ARM_REG_R0, objects + armor_id * 0x200 if armor_id in (1, 2, 3) else 0)
        u.reg_write(UC_ARM_REG_PC, u.reg_read(UC_ARM_REG_LR))

    m.u.hook_add(UC_HOOK_CODE, external)
    targets = (0x2db0b0, 0x2db160, 0x2db210)
    # Verify the native behavior that motivated the hooks: a universal base
    # with Gunner appearance loses BM eligibility and requests unequipping.
    m.u.mem_write(record, struct.pack('<IHHH', 0, 1, 3, 2) + bytes(34))
    assert tuple(m.call(target, record) for target in targets) == (0, 1, 1)
    for slot in range(1, 6):
        for base, donor, want in ((1, 2, (1, 0, 0)), (2, 1, (0, 1, 0)),
                                  (3, 1, (1, 1, 0)), (3, 2, (1, 1, 0)),
                                  (1, 0, (1, 0, 0)), (2, 0, (0, 1, 0)),
                                  (3, 0, (1, 1, 0)), (0, 2, (0, 0, 0))):
            data = bytearray(range(44))
            struct.pack_into('<HHH', data, 4, slot | (7 << 5), base, donor)
            m.u.mem_write(record, bytes(data))
            got = tuple(m.call(hooks.get(target, target), record) for target in targets)
            assert got == want, f'slot {slot}, base {base}, donor {donor}: {got} != {want}'
            assert bytes(m.u.mem_read(record, 44)) == bytes(data), 'classification mutated equipment record'
            assert m.call(0x2db09c, record) == (donor or base), 'native appearance getter lost donor'
    # Weapons/charms/Palico records retain stock behavior, even with +8 set.
    for slot in (0, 6, 7, 23, 24):
        data = bytearray(44)
        struct.pack_into('<HHH', data, 4, slot, 3, 2)
        m.u.mem_write(record, bytes(data))
        stock = tuple(m.call(target, record) for target in targets)
        got = tuple(m.call(hooks[target], record) for target in targets)
        assert got == stock, f'non-hunter slot {slot} changed'
        assert bytes(m.u.mem_read(record, 44)) == bytes(data)
    print('Native ARM classification: five hunter slots, both cross-class directions, universal bases, unfused and non-hunter records PASS; equipment bytes unchanged')

    # Drive the real pair hook using embedded catalog entries. The native pair
    # result is the external boundary: only its class bit may be relaxed.
    catalog = (ROOT / 'build/armor-fusion.afus').read_bytes()
    count = struct.unpack_from('<I', catalog, 8)[0]
    rows = [struct.unpack_from('<HBBBBHHH', catalog, 48 + i * 12) for i in range(count)]
    rows = [row for row in rows if row[5] and row[4] & 1]
    b = rows[0]
    a = next(row for row in rows if row[0] != b[0] and row[3] == b[3])
    other = next(row for row in rows if row[3] != b[3])
    ui, donor_record = record + 0x100, record + 0x80
    m.write32(m.symbols['active_ui'], ui)
    m.write32(m.symbols['context_ui'], ui)
    m.write32(ui + 0x44, 0)

    def piece(address, row, slot=1):
        m.u.mem_write(address, struct.pack('<IHHH', 0, slot | ((row[1] - 1) << 5), row[0], 0))

    piece(record, b)
    piece(donor_record, a)
    for result in (1, 0x21, 0x61, 0x81, 0x221, 0x421, 0x821, 0x2021, 0x1000):
        native_pair_result = result
        got = m.call(hooks[0x340d60], ui + 0x80, record, donor_record, 1)
        assert got == result & ~0x20, f'pair discarded unrelated restriction: {result:x} -> {got:x}'
    for row, slot in ((other, 1), (a, 2)):
        piece(donor_record, row, slot)
        native_pair_result = 0x21
        assert m.call(hooks[0x340d60], ui + 0x80, record, donor_record, 1) & 0x400, 'rank/slot mismatch accepted'
    piece(donor_record, a)
    m.write32(m.symbols['context_ui'], 0)
    native_pair_result = 0x21
    assert m.call(hooks[0x340d60], ui + 0x80, record, donor_record, 1) == 0x21, 'unowned UI pair relaxed'
    m.write32(m.symbols['context_ui'], ui)
    m.write32(ui + 0x44, 1)
    assert m.call(hooks[0x340d60], ui + 0x80, record, donor_record, 1) == 0x21, 'non-hunter mode pair relaxed'
    print('Compiled ARM pair hook: class bit relaxed only in owned hunter fusion; unrelated restrictions and rank/slot gates preserved PASS')


if __name__ == '__main__':
    main()

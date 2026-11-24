"""Run actual ARM bridge entry/call code. Catches lost LR, shifted stack args,
shadow writes to the native stack, callee-register corruption and lost return.
Requires Unicorn; the ELF reader uses only Python's standard library.
"""
from pathlib import Path
import struct,sys
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm_const import *
ROOT=Path(__file__).resolve().parents[1]
BASE,IMPORTS,STOP,STACK=0x03200000,0x03000000,0x03100000,0x0a000000
class ArmImage:
    def __init__(self,path):
        self.u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
        for addr,size in ((BASE,0x200000),(IMPORTS,0x1000),(STOP,0x1000),(STACK,0x10000)):
            self.u.mem_map(addr,size)
        raw=Path(path).read_bytes(); self.symbols={}; self.imports={}; self.exports=set()
        phoff=struct.unpack_from('<I',raw,28)[0]
        phentsize,phnum=struct.unpack_from('<HH',raw,42)
        for i in range(phnum):
            typ,off,va,_,size,_,_,_=struct.unpack_from('<8I',raw,phoff+i*phentsize)
            if typ==1:self.u.mem_write(BASE+va,raw[off:off+size])
        shoff=struct.unpack_from('<I',raw,32)[0]; shsize,shnum,shstr=struct.unpack_from('<HHH',raw,46)
        sections=[struct.unpack_from('<10I',raw,shoff+i*shsize) for i in range(shnum)]
        def cstr(data,off):return data[off:data.find(b'\0',off)].decode()
        symtabs={}
        for i,s in enumerate(sections):
            if s[1] not in (2,11):continue
            strings=sections[s[6]]; names=raw[strings[4]:strings[4]+strings[5]]; entries=[]
            for off in range(s[4],s[4]+s[5],s[9]):
                name,value,_,info,_,idx=struct.unpack_from('<IIIBBH',raw,off); name=cstr(names,name)
                entries.append(name)
                if not name:continue
                if s[1]==11 and idx:self.exports.add(name)
                if idx:self.symbols[name]=BASE+value
                elif name not in self.symbols:
                    address=IMPORTS+4*len(self.imports);self.imports[address]=name;self.symbols[name]=address
                    self.u.mem_write(address,bytes.fromhex('1eff2fe1'))
            symtabs[i]=entries
        for s in sections:
            if s[1]!=9:continue
            for off in range(s[4],s[4]+s[5],s[9]):
                where,info=struct.unpack_from('<II',raw,off);where+=BASE;typ=info&255
                if typ==23:value=BASE+self.read32(where)
                elif typ in (21,22):value=self.symbols[symtabs[s[6]][info>>8]]
                else:raise AssertionError(f'unsupported ARM relocation {typ}')
                self.write32(where,value)
        self.u.reg_write(UC_ARM_REG_C1_C0_2,0xf00000)
        self.u.reg_write(UC_ARM_REG_FPEXC,0x40000000)
        self.hooks=[];self.originals=[]
        self.u.hook_add(UC_HOOK_CODE,self.imported)
    def read32(self,a):return struct.unpack('<I',self.u.mem_read(a,4))[0]
    def write32(self,a,v):self.u.mem_write(a,struct.pack('<I',v))
    def imported(self,u,a,size,ctx):
        if a==STOP:u.emu_stop();return
        name=self.imports.get(a)
        if name is None:return
        if name=='forge_hook_create':
            out,target,detour,orig=[u.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)]
            previous=self.read32(target+4) if self.read32(target)==0xe51ff004 else target
            self.hooks.append((target,detour));self.originals.append((target,previous));self.write32(orig,previous)
            u.mem_write(out,struct.pack('<6I',target,detour,previous,0,0,0))
        elif name=='forge_log':pass
        elif name=='forge_mem_getMainTextAddr':u.reg_write(UC_ARM_REG_R0,0x00200000)
        else:raise AssertionError(f'unexpected import {name}')
    def call(self,name,*args):
        sp=STACK+0xf000;self.u.reg_write(UC_ARM_REG_SP,sp);self.u.reg_write(UC_ARM_REG_LR,STOP)
        for i,v in enumerate(args[:4]):self.u.reg_write(UC_ARM_REG_R0+i,v)
        self.u.emu_start(self.symbols.get(name,name),STOP+4,count=1000000)
        return self.u.reg_read(UC_ARM_REG_R0)

def main():
    path=ROOT/'build/test_bridge.elf'
    assert path.exists(),'ARM bridge artifact is missing; run make build/test_bridge.elf'
    m=ArmImage(path);m.call('test_bridge_init');assert len(m.hooks)==1
    assert set(m.imports.values())=={'forge_log','forge_hook_create','forge_mem_getMainTextAddr'},'plugin depends on non-Forge host imports'
    for numerator,denominator,want in ((0,1,0),(1,1,1),(9,10,0),(101,10,10),(0xffffffff,1,0xffffffff),(0xffffffff,0x80000000,1),(0xffffffff,3,1431655765)):
        assert m.call('__aeabi_uidiv',numerator,denominator)==want,'freestanding ARM unsigned division failed'
    sp=STACK+0xf000;sentinel=bytes(range(128));m.u.mem_write(sp-64,sentinel)
    for i,v in enumerate((5,6,7,8)):m.write32(sp+4*i,v)
    original=bytes(m.u.mem_read(sp,64))
    for i in range(4,12):m.u.reg_write(UC_ARM_REG_R0+i,0x11110000+i)
    m.symbols['entry']=m.hooks[0][1]
    assert m.call('entry',1,2,3,4)==0x600d0040,'native LR/stack/return bridge contract failed'
    assert m.u.reg_read(UC_ARM_REG_SP)==sp,'native stack was not restored'
    assert bytes(m.u.mem_read(sp,64))==original,'adapter scratch overwrote native stack arguments'
    for i in range(4,12):assert m.u.reg_read(UC_ARM_REG_R0+i)==0x11110000+i,f'r{i} was clobbered'
    print('ARM bridge: incoming LR, eight args, isolated scratch, guest_call4 registers, original call and return PASS')
    # No caller-sensitive conflict may leave even one other fusion hook active.
    # These stock words are independently verified from the MHGU 1.4.0 NSO.
    anchors={
        0x8f1ae8:0xe92d41f0,0x860314:0xe92d4830,0x86549c:0xe3a01001,
        0x75bc7c:0xe590005c,0x340b7c:0xe92d4070,0x340d60:0xe92d4ff0,
        0x341060:0xe92d41f0,0x74ff80:0xe92d4070,0x74fd94:0xe92d4800,
        0x85fcec:0xe92d4010,0x5ea218:0xe92d4010,0x20f248:0xe92d4070,
        0x85fe10:0xe92d4010,0x8f0c70:0xe92d4800,0x8f02fc:0xe92d4830,
        0x8f085c:0xe92d4800,0x75bac0:0xe92d4070,0x75d2b4:0xe0800101,
        0x85e5bc:0xe92d41f0,0x85e794:0xe92d4830,0xa88238:0xe590200c,
        0x2db0b0:0xe92d4070,0x2db160:0xe92d4070,0x2db210:0xe92d4070,
    }
    def boot(patches=None):
        image=ArmImage(ROOT/'build/armor_fusion.elf');image.u.mem_map(0x00200000,0x02800000)
        for addr,word in anchors.items():image.write32(addr,word)
        for addr,words in (patches or {}).items():
            for i,word in enumerate(words):image.write32(addr+4*i,word)
        image.call('forge_onInit')
        assert not image.hooks,'Fusion must not hook during plugin initialization'
        image.call('forge_onUpdate',0)
        assert not image.hooks,'Fusion must allow every peer its first update'
        image.call('forge_onUpdate',0)
        return image
    installed=boot()
    assert {'forge_onInit','forge_onUpdate'}<=installed.exports,'Forge lifecycle callbacks must be dynamic exports'
    assert len(installed.hooks)==16,'stock image did not install all native hooks'
    installed.call('forge_onUpdate',0)
    assert len(installed.hooks)==16,'later updates installed duplicate hooks'
    # A real first-update peer accepts stock code, then installs its literal
    # jump before Fusion's second update. Exercise both callback orders.
    for order in (('fusion','peer'),('peer','fusion')):
        image=ArmImage(ROOT/'build/armor_fusion.elf');image.u.mem_map(0x00200000,0x02800000)
        for addr,word in anchors.items():image.write32(addr,word)
        image.call('forge_onInit')
        assert not image.hooks
        peer=0xf0101000
        for plugin in order:
            if plugin=='fusion':image.call('forge_onUpdate',0)
            else:
                assert image.read32(0x8f1ae8)==anchors[0x8f1ae8],'stock-only peer rejected Fusion-patched entry'
                image.write32(0x8f1ae8,0xe51ff004);image.write32(0x8f1aec,peer)
        assert not image.hooks,'Fusion did not wait for the full first callback round'
        image.call('forge_onUpdate',0)
        assert len(image.hooks)==16,'first-update Windows peer blocked all Fusion hooks'
        assert image.read32(0x8f1aec)==peer,'Fusion preflight altered the peer detour'
        assert image.originals[0]==(0x8f1ae8,peer),'Fusion bridge did not retain the previous detour'
        image.u.mem_map(0xf0100000,0x2000)
        native,ui=0x02910000,0x02900000
        image.u.mem_write(peer,struct.pack('<5I',0xe92d4000,0xe59fc004,0xe12fff3c,0xe8bd8000,native))
        image.u.mem_write(native,struct.pack('<2I',0xe3a0004d,0xe12fff1e))
        calls={peer:0,native:0}
        def counted(u,address,size,context):
            if address in calls:calls[address]+=1
        image.u.hook_add(UC_HOOK_CODE,counted)
        assert image.call(image.hooks[0][1],ui)==77,'Fusion -> Windows peer -> native original lost return'
        assert calls=={peer:1,native:1},'real ARM peer/native chain was not executed once'

    # Failed preflight remains one-shot even if an operator later restores code.
    failed=boot({0x85fcec:(0xe51ff004,0x03201000)})
    failed.write32(0x85fcec,anchors[0x85fcec]);failed.call('forge_onUpdate',0)
    assert not failed.hooks,'failed preflight retried after the initialization boundary'

    for target in (0x74fd94,0x74ff80,0x75bac0):
        assert not boot({target:(0xe51ff004,0x03201000)}).hooks,f'caller-sensitive conflict {target:x} installed partial fusion'
    assert len(boot({0x8f1ae8:(0xe51ff004,0x03201000)}).hooks)==16,'Compendium-first smithy chain was rejected'
    for target in (0x340b7c,0x340d60,0x341060,0x860314,0x86549c,0x75bc7c,0x8f0c70,0x8f02fc,0x8f085c):
        assert len(boot({target:(0xe51ff004,0x03201000)}).hooks)==16,f'safe entry chain {target:x} was rejected'
    for detour in (0xf0100000,0xf80ffffc):
        assert len(boot({0x8f1ae8:(0xe51ff004,detour)}).hooks)==16,'verified Windows spill arena was rejected'
        for target in (0x74fd94,0x74ff80,0x75bac0):
            assert not boot({target:(0xe51ff004,detour)}).hooks,'spill arena bypassed caller-sensitive preflight'
    for words in ((0xe51ff004,0xf00ffffc),(0xe51ff004,0xf8100000),(0xe51ff004,0xf0100001),(0xe51ff004,0x031ffffc),(0xe51ff004,0x03e00000),(0xe51ff004,0x03200001),(0xea000000,0x03201000)):
        assert not boot({0x8f1ae8:words}).hooks,'foreign/unaligned hook bypassed version guard'
    assert not boot({0x85fcec:(0xe51ff004,0x03201000)}).hooks,'native factory conflict installed partial fusion'
    for target in (0x2db0b0,0x2db160,0x2db210):
        assert not boot({target:(0xe51ff004,0x03201000)}).hooks,'classification conflict installed partial fusion'
    print('ARM lifecycle and preflight: no hooks until second update; both first-update peer orders; one-shot failure; old/Windows spill chains; caller-sensitive/classification/foreign conflicts fail closed PASS')
if __name__=='__main__':main()

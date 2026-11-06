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
        raw=Path(path).read_bytes(); self.symbols={}; self.imports={}
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
        self.hooks=[]
        self.u.hook_add(UC_HOOK_CODE,self.imported)
    def read32(self,a):return struct.unpack('<I',self.u.mem_read(a,4))[0]
    def write32(self,a,v):self.u.mem_write(a,struct.pack('<I',v))
    def imported(self,u,a,size,ctx):
        if a==STOP:u.emu_stop();return
        name=self.imports.get(a)
        if name is None:return
        if name=='forge_hook_create':
            out,target,detour,orig=[u.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)]
            self.hooks.append((target,detour));self.write32(orig,target)
            u.mem_write(out,struct.pack('<6I',target,detour,target,0,0,0))
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
    }
    def boot(patches=None):
        image=ArmImage(ROOT/'build/armor_fusion.elf');image.u.mem_map(0x00200000,0x02800000)
        for addr,word in anchors.items():image.write32(addr,word)
        for addr,words in (patches or {}).items():
            for i,word in enumerate(words):image.write32(addr+4*i,word)
        image.call('forge_onInit');return image
    assert len(boot().hooks)==13,'stock image did not install all native hooks'
    for target in (0x74fd94,0x74ff80,0x75bac0):
        assert not boot({target:(0xe51ff004,0x03201000)}).hooks,f'caller-sensitive conflict {target:x} installed partial fusion'
    assert len(boot({0x8f1ae8:(0xe51ff004,0x03201000)}).hooks)==13,'Compendium-first smithy chain was rejected'
    for target in (0x340b7c,0x340d60,0x341060,0x860314,0x86549c,0x75bc7c,0x8f0c70,0x8f02fc,0x8f085c):
        assert len(boot({target:(0xe51ff004,0x03201000)}).hooks)==13,f'safe entry chain {target:x} was rejected'
    for words in ((0xe51ff004,0x031ffffc),(0xe51ff004,0x03e00000),(0xe51ff004,0x03200001),(0xea000000,0x03201000)):
        assert not boot({0x8f1ae8:words}).hooks,'foreign/unaligned hook bypassed version guard'
    assert not boot({0x85fcec:(0xe51ff004,0x03201000)}).hooks,'native factory conflict installed partial fusion'
    print('ARM adapter preflight: stock + ten safe chains PASS; three sensitive conflicts + foreign/factory conflicts fail closed before all hooks PASS')
if __name__=='__main__':main()

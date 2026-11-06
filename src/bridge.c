#include "hle.h"
#include <string.h>

typedef struct {
    void *target,*detour,*original,*context,*context_cell;
    bool has_context;
} ForgeHook;
extern ForgeHook forge_hook_create(void *,void *,void **);
typedef uint32_t (*Native8)(uint32_t,uint32_t,uint32_t,uint32_t,
                            uint32_t,uint32_t,uint32_t,uint32_t);
typedef uint32_t (*Entry)(void);
#define DECL(n) extern uint32_t fusion_entry_##n(void)
DECL(0); DECL(1); DECL(2); DECL(3); DECL(4); DECL(5); DECL(6);
DECL(7); DECL(8); DECL(9); DECL(10); DECL(11); DECL(12);
static const Entry entries[]={fusion_entry_0,fusion_entry_1,fusion_entry_2,
    fusion_entry_3,fusion_entry_4,fusion_entry_5,fusion_entry_6,fusion_entry_7,
    fusion_entry_8,fusion_entry_9,fusion_entry_10,fusion_entry_11,fusion_entry_12};
static struct { HostFn handler; uint32_t target,original; } hooks[13];
static unsigned registered;
static uint8_t strings[128] __attribute__((aligned(8)));
static uint32_t strings_used;

/* Exactly four additional integer words cover every adapted native call.
 * The compiler performs the AAPCS call; the real machine SP is never assigned
 * the virtual SP. Pointer outputs into the private shadow remain valid. */
static uint32_t call_native(Cpu *c,uint32_t target) {
    Native8 fn=(Native8)(uintptr_t)target;
    return fn(c->r[0],c->r[1],c->r[2],c->r[3],LD32(c->r[13]),
              LD32(c->r[13]+4),LD32(c->r[13]+8),LD32(c->r[13]+12));
}
uint32_t guest_call4(Cpu *c,uint32_t target,uint32_t a,uint32_t b,uint32_t d,uint32_t e) {
    uint32_t saved[16]; memcpy(saved,c->r,sizeof saved);
    c->r[0]=a; c->r[1]=b; c->r[2]=d; c->r[3]=e;
    uint32_t result=call_native(c,target);
    memcpy(c->r,saved,sizeof saved);
    return result;
}
void fnhook_call_original(Cpu *c,uint32_t target) {
    for(unsigned i=0;i<registered;i++) if(hooks[i].target==target) {
        if(!hooks[i].original) FATAL("[armor-fusion] missing original %x",target);
        c->r[0]=call_native(c,hooks[i].original); return;
    }
    FATAL("[armor-fusion] unregistered original %x",target);
}
uint32_t fusion_dispatch(unsigned index,const uint32_t *frame) {
    if(index>=registered) FATAL("[armor-fusion] invalid hook index %u",index);
    Cpu c={0};
    /* 64 bytes below the initial virtual SP, 32 above. The reference reserves
     * at most 32 bytes. Never borrow space below the wrapper's native SP. */
    uint32_t shadow[24] __attribute__((aligned(8)))={0};
    memcpy(c.r,frame,4*sizeof(uint32_t));
    memcpy(shadow+16,frame+6,4*sizeof(uint32_t));
    c.r[13]=(uint32_t)(uintptr_t)(shadow+16);
    c.r[14]=frame[5];
    hooks[index].handler(&c);
    return c.r[0];
}
uint32_t hle_alloc(uint32_t size) {
    if(size>sizeof strings-strings_used) FATAL("[armor-fusion] literal arena exhausted");
    uint32_t p=(uint32_t)(uintptr_t)(strings+strings_used); strings_used+=size;
    return p;
}
uint32_t hle_register(const char *name,HostFn fn) {
    (void)name;
    if(registered>=13) FATAL("[armor-fusion] too many native hooks");
    hooks[registered].handler=fn; return ++registered;
}
void fnhook_set(uint32_t target,uint32_t token) {
    if(!token || token>registered) FATAL("[armor-fusion] invalid hook token");
    unsigned index=token-1; void *original=0;
    ForgeHook result=forge_hook_create(G2H(target),(void *)entries[index],&original);
    if(!original || result.original!=original) FATAL("[armor-fusion] installation failed at %x",target);
    hooks[index].target=target; hooks[index].original=(uint32_t)(uintptr_t)original;
}
bool fusion_entry_matches(uint32_t address,uint32_t stock,bool caller_sensitive) {
    uint32_t first=LD32(address);
    if(first==stock) return true;
    if(caller_sensitive || first!=0xe51ff004u) return false;
    uint32_t detour=LD32(address+4);
    return !(detour&3) && detour>=0x03200000u && detour<0x03e00000u;
}

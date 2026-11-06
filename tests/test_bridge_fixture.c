/* ARM-only ABI fixture. The real bridge, wrapper and compiler-generated native
 * calls execute under Unicorn; Forge's installation import alone is replaced. */
#include "hle.h"
#include <string.h>
static uint32_t native_sum(uint32_t a,uint32_t b,uint32_t c,uint32_t d,
                           uint32_t e,uint32_t f,uint32_t g,uint32_t h) {
    return a+b+c+d+e+f+g+h;
}
static void exercise(Cpu *c) {
    uint32_t saved[16], result=0;
    memcpy(saved,c->r,sizeof saved);
    if(c->r[14]!=0x03100000u) return;
    if(LD32(c->r[13])!=5 || LD32(c->r[13]+12)!=8) return;
    c->r[13]-=32;
    ST32(c->r[13],15); ST32(c->r[13]+4,16);
    ST32(c->r[13]+8,17); ST32(c->r[13]+12,18);
    uint32_t scratch_sp=c->r[13];
    result=guest_call4(c,(uint32_t)(uintptr_t)native_sum,11,12,13,14);
    if(result!=116 || c->r[13]!=scratch_sp || c->r[14]!=saved[14] || c->r[0]!=1) return;
    c->r[13]=saved[13];
    if(memcmp(c->r,saved,sizeof saved)) return;
    fnhook_call_original(c,(uint32_t)(uintptr_t)native_sum);
    if(c->r[0]!=36 || c->r[13]!=saved[13] || c->r[14]!=saved[14]) return;
    c->r[0]=0x600d0040;
}
void test_bridge_init(void) {
    fnhook_set((uint32_t)(uintptr_t)native_sum,hle_register("bridge-test",exercise));
}

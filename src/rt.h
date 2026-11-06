#pragma once
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

/* Guest-only compatibility surface for the reference native UI adapter. These
 * pointers are ARM guest pointers: no host runtime or host memory is imported. */
typedef struct Cpu { uint32_t r[16]; } Cpu;
typedef void (*HostFn)(Cpu *);
typedef uint16_t u16u __attribute__((aligned(1),may_alias));
typedef uint32_t u32u __attribute__((aligned(1),may_alias));
#define G2H(a) ((void *)(uintptr_t)(uint32_t)(a))
#define LD8(a) (*(const uint8_t *)G2H(a))
#define LD16(a) (*(const u16u *)G2H(a))
#define LD32(a) (*(const u32u *)G2H(a))
#define ST8(a,v) (*(uint8_t *)G2H(a)=(uint8_t)(v))
#define ST16(a,v) (*(u16u *)G2H(a)=(uint16_t)(v))
#define ST32(a,v) (*(u32u *)G2H(a)=(uint32_t)(v))

extern void forge_log(int level,const char *format,...);
#define LOG(...) forge_log(1,__VA_ARGS__)
#define FATAL(...) do { forge_log(3,__VA_ARGS__); __builtin_trap(); } while(0)
uint32_t guest_call4(Cpu *,uint32_t,uint32_t,uint32_t,uint32_t,uint32_t);
void fnhook_call_original(Cpu *,uint32_t);
uint32_t hle_alloc(uint32_t);
uint32_t hle_register(const char *,HostFn);
void fnhook_set(uint32_t,uint32_t);
bool fusion_entry_matches(uint32_t address,uint32_t stock,bool caller_sensitive);

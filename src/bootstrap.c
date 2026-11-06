#include "hle.h"
#include "armor_fusion.h"
#include <stdarg.h>
#include <string.h>
extern void armorfusion_init(void);
extern void *forge_mem_getMainTextAddr(void);
void *memcpy(void *d,const void *s,size_t n) { uint8_t *p=d;const uint8_t *q=s;while(n--)*p++=*q++;return d; }
void *memset(void *d,int v,size_t n) { uint8_t *p=d;while(n--)*p++=(uint8_t)v;return d; }
int memcmp(const void *a,const void *b,size_t n) { const uint8_t *p=a,*q=b;while(n--){if(*p!=*q)return *p-*q;p++;q++;}return 0; }
void __aeabi_memcpy(void *d,const void *s,size_t n){memcpy(d,s,n);}
void __aeabi_memcpy4(void *d,const void *s,size_t n){memcpy(d,s,n);}
void __aeabi_memcpy8(void *d,const void *s,size_t n){memcpy(d,s,n);}
void __aeabi_memclr(void *d,size_t n){memset(d,0,n);}
void __aeabi_memclr4(void *d,size_t n){memset(d,0,n);}
void __aeabi_memclr8(void *d,size_t n){memset(d,0,n);}
/* ARMv7-A has no mandatory integer divide instruction. Resolve compiler
 * division locally so the NRO imports only the three Forge entry points. */
uint32_t __aeabi_uidiv(uint32_t numerator,uint32_t denominator) {
    if(!denominator) FATAL("[armor-fusion] division by zero");
    uint32_t quotient=0,remainder=0;
    for(unsigned bit=32;bit;bit--) {
        bool carry=(remainder>>31)!=0;
        remainder=(remainder<<1)|((numerator>>(bit-1))&1);
        if(carry || remainder>=denominator) {
            remainder-=denominator; quotient|=1u<<(bit-1);
        }
    }
    return quotient;
}
/* The native adapter uses only one snprintf format, containing one %u. Keep
 * formatting local rather than depending on the host libc or SDK symbols. */
int snprintf(char *out,size_t n,const char *format,...) {
    size_t used=0;va_list ap;va_start(ap,format);
    while(*format) {
        if(format[0]=='%' && format[1]=='u') {
            unsigned value=va_arg(ap,unsigned);char digits[10];unsigned count=0;
            do{digits[count++]=(char)('0'+value%10);value/=10;}while(value);
            while(count){char ch=digits[--count];if(used+1<n)out[used]=ch;used++;}
            format+=2;
        } else {if(used+1<n)out[used]=*format;used++;format++;}
    }
    va_end(ap);if(n)out[used<n?used:n-1]=0;return (int)used;
}
void forge_onLoad(void *params) {
    uint16_t *v=params;v[0]=1;v[1]=5;v[2]=1;
    memcpy((uint8_t *)params+6,"Armor Fusion",sizeof "Armor Fusion");
}
void forge_onInit(void) {
    if((uintptr_t)forge_mem_getMainTextAddr()!=0x00200000u) {
        LOG("[armor-fusion] unsupported executable text base; hooks not installed");return;
    }
    if(!fusion_catalog_load()) {LOG("[armor-fusion] invalid embedded AFUS catalog; hooks not installed");return;}
    armorfusion_init();
}

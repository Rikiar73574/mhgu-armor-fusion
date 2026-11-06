.syntax unified
.arm
.text
/* AAPCS keeps SP 8-byte aligned. Save the four native args, r4 and the exact
 * native LR before any C code. frame+24 is the caller's original SP. */
.macro ENTRY n
.global fusion_entry_\n
.type fusion_entry_\n,%function
fusion_entry_\n:
    push {r0-r4,lr}
    mov r1,sp
    mov r0,#\n
    bl fusion_dispatch
    add sp,sp,#16
    pop {r4,pc}
.size fusion_entry_\n,.-fusion_entry_\n
.endm
ENTRY 0
ENTRY 1
ENTRY 2
ENTRY 3
ENTRY 4
ENTRY 5
ENTRY 6
ENTRY 7
ENTRY 8
ENTRY 9
ENTRY 10
ENTRY 11
ENTRY 12

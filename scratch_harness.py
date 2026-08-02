import sys
from unicorn import *
from unicorn.arm_const import *

FLASH_BASE = 0x08004000
FLASH_SIZE = 0x40000
RAM_BASE = 0x20000000
RAM_SIZE = 0x10000
STACK_TOP = RAM_BASE + RAM_SIZE - 4

def make_uc(bin_path):
    data = open(bin_path, "rb").read()
    uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    flash_map_size = ((len(data) + 0xFFF) // 0x1000) * 0x1000 + 0x1000
    uc.mem_map(FLASH_BASE, flash_map_size)
    uc.mem_write(FLASH_BASE, data)
    uc.mem_map(RAM_BASE, RAM_SIZE)
    uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
    return uc

def call_func(uc, addr, args, ret_addr=0x0FFFFFFE):
    for i, a in enumerate(args):
        uc.reg_write([UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3][i], a)
    uc.reg_write(UC_ARM_REG_LR, ret_addr)
    try:
        uc.emu_start(addr | 1, ret_addr, timeout=0, count=200000)
    except UcError as e:
        print(f"  [stopped: {e}]", file=sys.stderr)
    return uc.reg_read(UC_ARM_REG_R0)

if __name__ == "__main__":
    uc = make_uc("MPK88_v1_01.bin" if __import__("os").path.exists("MPK88_v1_01.bin") else None)

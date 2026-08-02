#!/usr/bin/env python3
"""Find every caller of the menu-switch dispatcher (0x08007fd6, which does
set_param(21, r0)) and try to resolve what screen-id value (r0) each call
site passes, to find what UI action(s) can produce param21==39 -- the
condition that silently swallows every key press in the key-scan handler."""
import json, re
from capstone import *

FLASH_BASE = 0x08004000
data = open("/home/claude/mpk/MPK61_gatebypass_v2.bin", "rb").read()
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
md.detail = True

DISPATCHER = 0x08007fd6

def disasm_window(start, back=40):
    begin = max(FLASH_BASE, start - back)
    out = []
    addr = begin
    while addr <= start:
        off = addr - FLASH_BASE
        got = list(md.disasm(data[off:off+4], addr))
        if not got:
            addr += 2
            continue
        insn = got[0]
        out.append(insn)
        addr += insn.size
    return out

def find_reg_imm(window, call_addr, reg):
    for insn in reversed(window):
        if insn.address >= call_addr:
            continue
        m = re.match(r"movs?(\.w)?$", insn.mnemonic)
        if m and insn.op_str.startswith(reg + ","):
            m2 = re.search(r"#(0[xX][0-9a-fA-F]+|\d+)", insn.op_str)
            if m2:
                return int(m2.group(1), 0)
            return None
        if insn.op_str.startswith(reg + ",") and insn.mnemonic not in ("cmp",):
            return None
    return None

fm = json.load(open("/home/claude/mpk/full_disasm/function_map.json"))

callers = [f for f in fm if hex(DISPATCHER) in f["callees"]]
print(f"functions calling the menu-switch dispatcher (0x{DISPATCHER:08x}): {len(callers)}")
print()

found_39 = []
for f in callers:
    fstart = int(f["start"], 16)
    fend = int(f["end_approx"], 16)
    addr = fstart
    while addr <= fend:
        off = addr - FLASH_BASE
        got = list(md.disasm(data[off:off+4], addr))
        if not got:
            addr += 2
            continue
        insn = got[0]
        if insn.mnemonic in ("bl", "blx") and insn.operands and insn.operands[-1].type == 2:
            tgt = insn.operands[-1].imm
            if tgt == DISPATCHER:
                window = disasm_window(insn.address)
                r0 = find_reg_imm(window, insn.address, "r0")
                print(f"  call at {hex(insn.address)} in {f['label']:35s} -> screen_id={r0}")
                if r0 == 39:
                    found_39.append(hex(insn.address))
        addr += insn.size

print()
print(f"call sites that pass screen_id=39 directly: {found_39}")

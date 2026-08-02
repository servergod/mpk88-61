#!/usr/bin/env python3
"""
Use the complete function map to find EVERY call site to set_param
(0x0801031c) and get_param (0x08007bb4), and for each, try to statically
resolve the immediate param-id (r0) and value (r1) loaded shortly before
the call -- a full enumeration, not a single grep hit.
"""
import json, re
from capstone import *

FLASH_BASE = 0x08004000
data = open("/home/claude/mpk/MPK61_gatebypass_v2.bin", "rb").read()
END = FLASH_BASE + len(data)
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
md.detail = True

SET_PARAM = 0x0801031c
GET_PARAM = 0x08007bb4

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
    """search backward from call_addr for the most recent 'movs reg,#N' or
    'mov.w reg,#N' setting that register, without an intervening redefinition
    by something non-immediate (best-effort, not perfect)."""
    for insn in reversed(window):
        if insn.address >= call_addr:
            continue
        m = re.match(r"movs?(\.w)?$", insn.mnemonic)
        if m and insn.op_str.startswith(reg + ","):
            m2 = re.search(r"#(0[xX][0-9a-fA-F]+|\d+)", insn.op_str)
            if m2:
                return int(m2.group(1), 0)
            return None  # moved from something non-immediate
        # if reg gets redefined by anything else first, stop (best-effort)
        if insn.op_str.startswith(reg + ",") and insn.mnemonic not in ("cmp",):
            return None
    return None

fm = json.load(open("/home/claude/mpk/full_disasm/function_map.json"))

results = {"set_param_calls": [], "get_param_calls": []}
for f in fm:
    fstart = int(f["start"], 16)
    fend = int(f["end_approx"], 16)
    if hex(SET_PARAM) in f["callees"] or hex(GET_PARAM) in f["callees"]:
        # walk this function's instructions to find exact call sites
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
                if tgt in (SET_PARAM, GET_PARAM):
                    window = disasm_window(insn.address)
                    r0 = find_reg_imm(window, insn.address, "r0")
                    entry = {
                        "call_site": hex(insn.address),
                        "in_function": f["label"],
                        "func_start": f["start"],
                        "param_id": r0,
                    }
                    if tgt == SET_PARAM:
                        r1 = find_reg_imm(window, insn.address, "r1")
                        entry["value"] = r1
                        results["set_param_calls"].append(entry)
                    else:
                        results["get_param_calls"].append(entry)
            addr += insn.size

json.dump(results, open("/home/claude/mpk/full_disasm/param_calls.json", "w"), indent=1)

print(f"set_param call sites: {len(results['set_param_calls'])}")
print(f"get_param call sites: {len(results['get_param_calls'])}")
print()
print("=== every set_param call, with resolved (param_id, value) where statically determinable ===")
for e in sorted(results["set_param_calls"], key=lambda x: x["call_site"]):
    print(f"  {e['call_site']} in {e['in_function']:45s} param={e['param_id']} value={e['value']}")
print()
print("=== set_param calls specifically targeting param 21 ===")
for e in results["set_param_calls"]:
    if e["param_id"] == 21:
        print(f"  {e['call_site']} in {e['in_function']} value={e['value']}")

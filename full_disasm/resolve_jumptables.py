#!/usr/bin/env python3
"""
Second pass: resolve every tbb/tbh jump table found in pass 1 into its
actual case targets, by finding the preceding bounds check (cmp rX,#N)
on the same index register, then reading N+1 table entries.

tbb [pc, rN]        -> byte table immediately after the instruction,
                        target = align4(pc_after) + 2*entry
tbh [pc, rN, lsl#1] -> halfword table immediately after,
                        target = align4(pc_after) + 2*entry
"""
import struct, json, re
from capstone import *
from capstone.arm import *

FLASH_BASE = 0x08004000
BIN_PATH = "/home/claude/mpk/MPK61_gatebypass_v2.bin"
data = open(BIN_PATH, "rb").read()
END = FLASH_BASE + len(data)

def in_range(a): return FLASH_BASE <= a < END
def read_u8(a): return data[a - FLASH_BASE]
def read_u16(a): return struct.unpack_from("<H", data, a - FLASH_BASE)[0]

md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
md.detail = True

fm = json.load(open("/home/claude/mpk/full_disasm/function_map.json"))

def disasm_window(start, count_back=8):
    """disassemble backward-ish by scanning forward from a safe earlier point;
       simplest robust approach: linearly disassemble from (start-32) forward
       until we pass `start`, collecting instructions in order."""
    begin = max(FLASH_BASE, start - 32)
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

resolved = {}
for f in fm:
    for b in f["branches"]:
        if "JUMPTABLE" not in b["kind"]:
            continue
        tbb_addr = int(b["at"], 16)
        is_tbh = "tbh" in b["kind"]
        window = disasm_window(tbb_addr)
        # find the tbb/tbh insn itself in window, and the index register
        idx_reg = None
        for insn in window:
            if insn.address == tbb_addr:
                m = re.search(r"\[pc,\s*(r\d+)", insn.op_str)
                if m:
                    idx_reg = m.group(1)
                break
        bound = None
        if idx_reg:
            for insn in reversed(window):
                if insn.address >= tbb_addr:
                    continue
                mm = re.match(rf"cmp(\.w)?$", insn.mnemonic)
                if mm and insn.op_str.startswith(idx_reg + ","):
                    m2 = re.search(r"#(0[xX][0-9a-fA-F]+|\d+)", insn.op_str)
                    if m2:
                        bound = int(m2.group(1), 0)
                        break
        table_start = tbb_addr + 4  # tbb/tbh are 4-byte Thumb-2 instructions
        entries = []
        if bound is not None:
            n = bound + 1
            for i in range(n):
                if is_tbh:
                    val = read_u16(table_start + 2*i)
                else:
                    val = read_u8(table_start + i)
                target = table_start + 2*val
                # align base for tbh table_start read is fine since it's byte-addressed here;
                # actual PC base per ARM ARM is Align(PC,4) at time of tbb/tbh execution.
                entries.append({"case": i, "target": hex(target) if in_range(target) else None})
        resolved[b["at"]] = {
            "kind": b["kind"], "idx_reg": idx_reg, "bound": bound,
            "n_cases": (bound+1) if bound is not None else None,
            "table_start": hex(table_start), "cases": entries,
        }

json.dump(resolved, open("/home/claude/mpk/full_disasm/jumptables_resolved.json", "w"), indent=1)
total_cases = sum(len(v["cases"]) for v in resolved.values())
print(f"resolved {len(resolved)} jump tables, {total_cases} total case targets")
for k, v in resolved.items():
    print(k, v["kind"], "bound=", v["bound"], "n_cases=", v["n_cases"])

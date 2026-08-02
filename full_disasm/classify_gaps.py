#!/usr/bin/env python3
"""
Don't assume the uncovered 41.3% is data -- prove it, byte by byte where
possible. For every gap:
  1. Collect every literal-pool reference (ldr rX,[pc,#imm]) from all
     currently-known instructions and compute the actual literal addresses
     they load from.
  2. For each gap, check how much of it is directly accounted for by real
     literal-pool references (confirmed data, not guessed).
  3. For whatever's left unaccounted for, try linearly disassembling it as
     Thumb code and see if it looks like plausible, well-formed code
     (valid instructions, sensible prologue/epilogue). If so, treat its
     start as a new function seed for another recursive-descent pass.
"""
import json, struct
from capstone import *
from capstone.arm import *

FLASH_BASE = 0x08004000
data = open("/home/claude/mpk/MPK61_gatebypass_v2.bin", "rb").read()
SIZE = len(data)
END = FLASH_BASE + SIZE
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
md.detail = True

fm = json.load(open("/home/claude/mpk/full_disasm/function_map.json"))

# rebuild every actually-visited instruction by re-disassembling each
# function's extent (function_map only stored coarse start/end, so redo
# a light pass over exactly those ranges using the same stepping logic)
visited = set()
literal_refs = set()  # addresses referenced by ldr rX,[pc,#imm]

for f in fm:
    addr = int(f["start"], 16)
    end = int(f["end_approx"], 16)
    while addr <= end:
        off = addr - FLASH_BASE
        got = list(md.disasm(data[off:off+4], addr))
        if not got:
            addr += 2
            continue
        insn = got[0]
        visited.add(addr)
        if insn.mnemonic in ("ldr", "ldr.w", "vldr") and "[pc" in insn.op_str:
            # capstone gives us the resolved absolute address as a comment-less
            # op sometimes; recompute manually: PC = align4(addr+4)
            for op in insn.operands:
                if op.type == 3 and op.mem.base == ARM_REG_PC:  # ARM_OP_MEM
                    pc_val = (addr + 4) & ~3
                    lit_addr = pc_val + op.mem.disp
                    literal_refs.add(lit_addr)
        addr += insn.size

print(f"total instructions re-walked: {len(visited)}")
print(f"literal pool references found: {len(literal_refs)}")

# also mark 4-byte words at each literal ref as "data" (most are 4-byte consts)
literal_bytes = set()
for a in literal_refs:
    for i in range(4):
        literal_bytes.add(a + i)

visited_bytes = set()
for a in visited:
    off = a - FLASH_BASE
    got = list(md.disasm(data[off:off+4], a))
    sz = got[0].size if got else 2
    for i in range(sz):
        visited_bytes.add(a + i)

vector_bytes = set(range(FLASH_BASE, FLASH_BASE + 0x174))  # from earlier gap[0]

accounted = visited_bytes | literal_bytes | vector_bytes
all_bytes = set(range(FLASH_BASE, END))
unaccounted = sorted(all_bytes - accounted)

print(f"code bytes: {len(visited_bytes)}")
print(f"literal-pool bytes (confirmed via real xrefs): {len(literal_bytes)}")
print(f"vector table bytes: {len(vector_bytes)}")
print(f"TOTAL accounted: {len(accounted)} / {SIZE} = {100*len(accounted)/SIZE:.1f}%")
print(f"still unaccounted: {len(unaccounted)} bytes = {100*len(unaccounted)/SIZE:.1f}%")

# group unaccounted into contiguous ranges
ranges = []
if unaccounted:
    s = unaccounted[0]
    prev = unaccounted[0]
    for b in unaccounted[1:]:
        if b != prev + 1:
            ranges.append((s, prev+1))
            s = b
        prev = b
    ranges.append((s, prev+1))

ranges.sort(key=lambda r: -(r[1]-r[0]))
print(f"\n{len(ranges)} unaccounted contiguous ranges, largest first:")
for s, e in ranges[:40]:
    print(f"  {hex(s)}-{hex(e)} ({e-s} bytes)")

json.dump([[hex(s), hex(e)] for s, e in ranges],
          open("/home/claude/mpk/full_disasm/unaccounted_ranges.json", "w"), indent=1)

#!/usr/bin/env python3
"""For every remaining unaccounted gap, decide data vs. possible-code by:
  - content stats (printable ratio, zero ratio, byte entropy-ish)
  - attempting a linear Thumb disasm and checking how much of it decodes
    into a clean, unbroken instruction stream with no invalid encodings
Anything that looks code-like gets its start added to a new seed list for
another recursive-descent pass; the rest gets reported as classified data.
"""
import json, math
from capstone import *

FLASH_BASE = 0x08004000
data = open("/home/claude/mpk/MPK61_gatebypass_v2.bin", "rb").read()
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)

ranges = json.load(open("/home/claude/mpk/full_disasm/unaccounted_ranges.json"))
ranges = [(int(s,16), int(e,16)) for s, e in ranges]

def entropy(b):
    if not b: return 0
    freq = {}
    for x in b: freq[x] = freq.get(x,0)+1
    n = len(b)
    return -sum((c/n)*math.log2(c/n) for c in freq.values())

code_like_seeds = []
data_ranges = []
ambiguous = []

for s, e in ranges:
    off_s, off_e = s - FLASH_BASE, e - FLASH_BASE
    chunk = data[off_s:off_e]
    n = len(chunk)
    printable = sum(1 for b in chunk if 32 <= b < 127) / n
    zeros = chunk.count(0) / n
    ent = entropy(chunk)

    # try linear disasm across the whole gap; measure how much decodes cleanly
    decoded_bytes = 0
    addr = s
    valid_run = True
    insns = 0
    while addr < e:
        off = addr - FLASH_BASE
        got = list(md.disasm(data[off:off+4], addr))
        if not got:
            addr += 2
            continue
        insn = got[0]
        decoded_bytes += insn.size
        insns += 1
        addr += insn.size
    decode_ratio = decoded_bytes / n if n else 0

    # Trust clean linear decode over content stats -- real Thumb code can have
    # high "printable" byte overlap purely by coincidence (opcode bytes landing
    # in the 0x20-0x7e range), so printable/zero ratio is NOT reliable evidence
    # of data on its own. Require a real proof instead: does the whole gap
    # decode as an unbroken, valid instruction stream? If so it's code,
    # regardless of what the first instruction's mnemonic happens to be
    # (dense runs of tiny functions can start with a bare `bx lr`).
    if decode_ratio > 0.98 and n >= 4:
        verdict = "code_candidate"
        code_like_seeds.append(hex(s))
    elif zeros > 0.6 and printable < 0.05:
        verdict = "data"
        data_ranges.append((hex(s), hex(e), n))
    else:
        verdict = "ambiguous"
        ambiguous.append((hex(s), hex(e), n, f"printable={printable:.2f} zeros={zeros:.2f} entropy={ent:.2f} decode_ratio={decode_ratio:.2f}"))

print(f"total gaps: {len(ranges)}")
print(f"classified as data (by content stats): {len(data_ranges)}")
print(f"code candidates (clean decode + real prologue): {len(code_like_seeds)}")
print(f"ambiguous (need manual look): {len(ambiguous)}")
print()
print("=== code candidates ===")
for c in code_like_seeds:
    print(" ", c)
print()
print("=== ambiguous, with stats ===")
for a in ambiguous:
    print(" ", a)

json.dump(code_like_seeds, open("/home/claude/mpk/full_disasm/gap_code_seeds.json","w"))

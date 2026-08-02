#!/usr/bin/env python3
"""Find contiguous byte ranges never visited as code by the recursive
descent walk, to see whether the ~43% uncovered is plausible data
(literal pools, vector table, padding) or real unreached code worth a
further pass."""
import json, struct
from capstone import *

FLASH_BASE = 0x08004000
data = open("/home/claude/mpk/MPK61_gatebypass_v2.bin", "rb").read()
SIZE = len(data)

fm = json.load(open("/home/claude/mpk/full_disasm/function_map.json"))

# rebuild the set of (addr) actually visited: approximate using start..end_approx
# plus proper instruction stepping isn't stored, so instead re-run a quick
# visited-byte estimate via the same instructions dict would be better, but
# function_map only stores extents. Use a coarse per-function byte range as
# "covered" for this gap check (start..end_approx+2).
covered = []
for f in fm:
    s = int(f["start"], 16)
    e = int(f["end_approx"], 16) + 4
    covered.append((s, e))
covered.sort()

merged = []
for s, e in covered:
    if merged and s <= merged[-1][1]:
        merged[-1] = (merged[-1][0], max(merged[-1][1], e))
    else:
        merged.append((s, e))

gaps = []
prev_end = FLASH_BASE
for s, e in merged:
    if s > prev_end:
        gaps.append((prev_end, s))
    prev_end = max(prev_end, e)
if prev_end < FLASH_BASE + SIZE:
    gaps.append((prev_end, FLASH_BASE + SIZE))

gaps = [(s, e) for s, e in gaps if e - s >= 32]
gaps.sort(key=lambda g: g[0])
total_gap_bytes = sum(e - s for s, e in gaps)
print(f"{len(gaps)} gaps >=32 bytes, {total_gap_bytes} total bytes")
for s, e in gaps[:15]:
    print(f"  gap {hex(s)}-{hex(e)} ({e-s} bytes)")

json.dump([(hex(s), hex(e)) for s, e in gaps], open("/home/claude/mpk/full_disasm/gaps.json", "w"), indent=1)

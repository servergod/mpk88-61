#!/usr/bin/env python3
"""Pull all resolved jump-table case targets out into extra_seeds.json
so the next analyze.py pass treats them as function/code entry points."""
import json, os
jt = json.load(open("/home/claude/mpk/full_disasm/jumptables_resolved.json"))
targets = set()
for v in jt.values():
    for c in v["cases"]:
        if c["target"]:
            targets.add(c["target"])

gap_path = "/home/claude/mpk/full_disasm/gap_code_seeds.json"
if os.path.exists(gap_path):
    targets |= set(json.load(open(gap_path)))

existing_path = "/home/claude/mpk/full_disasm/extra_seeds.json"
if os.path.exists(existing_path):
    targets |= set(json.load(open(existing_path)))

json.dump(sorted(targets), open("/home/claude/mpk/full_disasm/extra_seeds.json", "w"))
print(f"wrote {len(targets)} extra seeds (cumulative, merged)")

#!/usr/bin/env python3
"""
Pass 2+: call-graph propagation. Any function whose callees are ALL
already labeled (in the current reference table) with the SAME pool
inherits that pool as an "inferred" label -- real evidence (who it calls),
not a guess. Also: any function called by exactly ONE already-labeled
caller inherits that caller's pool the same way. Iterates until a fixed
point (no new labels in a full pass).
"""
import json, sys

fm = json.load(open("/home/claude/mpk/full_disasm/function_map.json"))
byaddr = {f["start"]: f for f in fm}
ref = json.load(open("/home/claude/mpk/full_disasm/reference_table.json"))
byaddr_ref = {r["addr"]: r for r in ref}

# build caller map
callers_of = {}
for r in ref:
    for c in r["callees"]:
        callers_of.setdefault(c, []).append(r["addr"])

def is_labeled(addr):
    r = byaddr_ref.get(addr)
    return r is not None and r["confidence"] != "unknown"

changed = True
round_num = 0
new_labels_total = 0
while changed:
    round_num += 1
    changed = False
    for r in ref:
        if r["confidence"] != "unknown":
            continue
        addr = r["addr"]
        callees = r["callees"]

        # Rule A: all callees labeled with the same pool -> inherit
        if callees:
            callee_pools = set()
            all_labeled = True
            for c in callees:
                cr = byaddr_ref.get(c)
                if cr is None or cr["confidence"] == "unknown" or cr["pool"] is None:
                    all_labeled = False
                    break
                callee_pools.add(cr["pool"])
            if all_labeled and len(callee_pools) == 1:
                pool = callee_pools.pop()
                r["label"] = f"{pool}_orchestrator"
                r["confidence"] = "inferred"
                r["evidence"] = f"calls only already-labeled '{pool}' functions ({len(callees)} callee(s)) -- propagated from call graph"
                r["pool"] = pool
                changed = True
                new_labels_total += 1
                continue

        # Rule B: exactly one caller, and that caller is labeled -> inherit
        my_callers = callers_of.get(addr, [])
        if len(my_callers) == 1:
            cr = byaddr_ref.get(my_callers[0])
            if cr is not None and cr["confidence"] != "unknown" and cr["pool"] is not None:
                r["label"] = f"{cr['pool']}_helper"
                r["confidence"] = "inferred"
                r["evidence"] = f"sole caller is labeled '{cr['label']}' (pool={cr['pool']}) -- propagated from call graph"
                r["pool"] = cr["pool"]
                changed = True
                new_labels_total += 1

    print(f"round {round_num}: new labels this round = {sum(1 for x in ref if x['confidence']!='unknown')}")

json.dump(ref, open("/home/claude/mpk/full_disasm/reference_table.json", "w"), indent=1)

conf_counts = {}
pool_counts = {}
for r in ref:
    conf_counts[r["confidence"]] = conf_counts.get(r["confidence"], 0) + 1
    if r["pool"]:
        pool_counts[r["pool"]] = pool_counts.get(r["pool"], 0) + 1

print()
print(f"propagation rounds run: {round_num}")
print(f"total newly labeled this pass: {new_labels_total}")
print()
print("=== updated confidence breakdown ===")
for k, v in sorted(conf_counts.items()):
    print(f"  {k}: {v}")
print()
print("=== updated pool breakdown ===")
for k, v in sorted(pool_counts.items(), key=lambda x: -x[1]):
    print(f"  {k}: {v}")

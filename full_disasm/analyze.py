#!/usr/bin/env python3
"""
Full recursive-descent disassembler + function map builder for the MPK61
STM32 firmware blob. Not a targeted trace -- walks the entire reachable
code graph, identifies every function boundary, labels every function,
and records every branch/case target inside each function.

Strategy:
  1. Seed a worklist with the interrupt vector table entries + every
     function address already identified by name in prior sessions.
  2. Recursive-descent walk: disassemble linearly from each seed, follow
     conditional/unconditional branches inline (same function), and queue
     bl/blx targets as new function starts. Stop a linear run at a real
     terminator (bx lr, pop {...,pc}, unconditional b, udf) so we don't
     walk into inline literal-pool data.
  3. After the walk, function boundaries = sorted set of (vector table
     entries UNION all bl/blx targets). Each function's extent runs from
     its start to the last instruction actually visited before the next
     function start (via the recursive walk), not a blind linear slice.
  4. For each function: record its callees (bl targets), its internal
     branch structure (conditional chains, tbb/tbh jump tables), and
     labels it with a known name if we already identified one, else
     FUN_<addr>.
"""
import struct
import json
from capstone import *
from capstone.arm import *

FLASH_BASE = 0x08004000
BIN_PATH = "/home/claude/mpk/MPK61_gatebypass_v2.bin"

data = open(BIN_PATH, "rb").read()
SIZE = len(data)
END = FLASH_BASE + SIZE

def in_range(addr):
    return FLASH_BASE <= addr < END

def read_u32(addr):
    off = addr - FLASH_BASE
    return struct.unpack_from("<I", data, off)[0]

md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
md.detail = True

# ---- known names from prior sessions (ground truth, disassembly-confirmed) ----
KNOWN = {
    0x080107e0: "note_mapping_fn",
    0x08010266: "get_param_wrapper",  # dispatch site used as hook point; real get_param below
    0x0800ff70: "gpio_bit_read_debounce_primitive",
    0x08010800: "note_mapping_fn_base_add (adds r0,#36 patch site)",
    0x08010806: "note_on_path_entry",
    0x0801060e: "gate2_check (get_param 17/232/233, arp/note-repeat?)",
    0x08010714: "gate1_check (calls get_param21_cmp39)",
    0x0800e10:  "matrix_drive_line_select",
    0x08010e10: "matrix_drive_line_select",
    0x08010e9e: "matrix_row_change_handler",
    0x08010f0a: "matrix_read_8_gpio_bits",
    0x08010f58: "matrix_per_row_scan",
    0x08011052: "matrix_scan_orchestrator",
    0x08014716: "event_dispatcher",
    0x080147c0: "enqueue_event_primitive",
    0x0801483c: "note_on_builder (cmp r4,#88 boundary)",
    0x08014854: "note_off_builder (cmp r4,#88 boundary)",
    0x08016b22: "key_scan_handler (2 gate checks)",
    0x08016b46: "key_scan_handler_cont",
    0x08016b62: "key_scan_handler_note_off_path",
    0x08017d0d: "usart1_isr",
    0x0801744c: "uart_rx_ringbuf_push",
    0x0801833c: "uart_rx_byte_consumer (7bit mask+flag split)",
    0x080112b0: "passthrough_noop (bx lr)",
    0x08007bb4: "get_param",
    0x0801031c: "set_param",
    0x08007fd6: "menu_switch_dispatcher (writes param21)",
    0x08007fe0: "menu_switch_write_param21_site",
    0x08006e30: "cc_knob_handler_a",
    0x08006b84: "cc_knob_handler_b",
    0x08006bbe: "switch_style_handler",
}

# ---- 1. vector table ----
vector_table = []
for i in range(16 + 60):  # core exceptions + peripheral IRQs, generous upper bound
    addr = FLASH_BASE + i * 4
    if addr + 4 > END:
        break
    val = read_u32(addr)
    if val & 1 and in_range(val & ~1):
        vector_table.append(val & ~1)

seeds = set(vector_table) | set(KNOWN.keys())

# extra seeds discovered by the jump-table resolver in a prior pass (if present)
import os
extra_path = "/home/claude/mpk/full_disasm/extra_seeds.json"
if os.path.exists(extra_path):
    extra = json.load(open(extra_path))
    seeds |= set(int(a, 16) for a in extra)
    print(f"loaded {len(extra)} extra seeds from jump-table resolution")

TERMINATORS_MNEM = {"bx", "pop", "b", "udf", "trap"}

def is_terminator(insn):
    if insn.mnemonic == "bx":
        return True
    if insn.mnemonic.startswith("pop") and "pc" in insn.op_str:
        return True
    if insn.mnemonic == "b" and insn.cc == ARM_CC_AL:  # unconditional plain b
        return True
    if insn.mnemonic in ("udf",):
        return True
    return False

visited_addrs = set()          # all instruction start addresses actually disassembled
instructions = {}              # addr -> capstone insn
call_targets = set()           # bl/blx destinations -> new function starts
branch_edges = {}              # addr -> list of (target, kind) for internal branches
func_callees = {}              # func_start -> set(callee addrs)

worklist = list(seeds)
work_seen = set(worklist)

MAX_STEPS = 400000
steps = 0

while worklist and steps < MAX_STEPS:
    addr = worklist.pop()
    cur = addr
    # linear run until terminator or already-visited/out-of-range
    while in_range(cur) and cur not in visited_addrs and steps < MAX_STEPS:
        steps += 1
        off = cur - FLASH_BASE
        chunk = data[off:off+4]
        got = list(md.disasm(chunk, cur))
        if not got:
            break
        insn = got[0]
        visited_addrs.add(cur)
        instructions[cur] = insn

        mnem = insn.mnemonic
        ops = insn.op_str

        # branch/call target extraction
        target = None
        if insn.operands:
            last_op = insn.operands[-1]
            if last_op.type == ARM_OP_IMM:
                target = last_op.imm

        if mnem in ("bl", "blx") and target is not None and in_range(target):
            call_targets.add(target)
            if target not in work_seen:
                worklist.append(target); work_seen.add(target)

        elif mnem.startswith("b") and mnem not in ("bl", "blx", "bic", "bkpt") and target is not None and in_range(target):
            # conditional or unconditional branch, or cbz/cbnz (2-operand, target is last)
            branch_edges.setdefault(cur, []).append((target, mnem))
            if target not in work_seen:
                worklist.append(target); work_seen.add(target)

        elif mnem in ("cbz", "cbnz") and target is not None and in_range(target):
            branch_edges.setdefault(cur, []).append((target, mnem))
            if target not in work_seen:
                worklist.append(target); work_seen.add(target)

        elif mnem in ("tbb", "tbh"):
            # jump table immediately following; can't easily bound without more context,
            # flag it for manual/second-pass review rather than guess wrong
            branch_edges.setdefault(cur, []).append((None, mnem + "_JUMPTABLE_UNRESOLVED"))

        if is_terminator(insn):
            break

        cur += insn.size

print(f"steps={steps} visited_instrs={len(visited_addrs)} call_targets={len(call_targets)} vector_table_entries={len(vector_table)}")

# ---- function boundaries ----
func_starts = sorted(set(vector_table) | call_targets | set(KNOWN.keys()))
func_starts = [a for a in func_starts if a in visited_addrs or a in seeds]

all_visited_sorted = sorted(visited_addrs)

def func_extent(start, next_start):
    """addresses in [start, next_start) that were actually visited (code)"""
    return [a for a in all_visited_sorted if start <= a < (next_start or END)]

results = []
for i, start in enumerate(func_starts):
    nxt = func_starts[i+1] if i+1 < len(func_starts) else None
    extent = func_extent(start, nxt)
    if not extent:
        continue
    callees = set()
    cases = []
    for a in extent:
        insn = instructions[a]
        if insn.mnemonic in ("bl", "blx"):
            if insn.operands and insn.operands[-1].type == ARM_OP_IMM:
                t = insn.operands[-1].imm
                if in_range(t):
                    callees.add(t)
        if a in branch_edges:
            for tgt, kind in branch_edges[a]:
                cases.append({"at": hex(a), "kind": kind, "target": hex(tgt) if tgt else None})
    label = KNOWN.get(start, f"FUN_{start:08x}")
    results.append({
        "start": hex(start),
        "label": label,
        "end_approx": hex(extent[-1]),
        "n_instructions": len(extent),
        "callees": sorted(hex(c) for c in callees),
        "branches": cases,
        "in_vector_table": start in vector_table,
    })

with open("/home/claude/mpk/full_disasm/function_map.json", "w") as f:
    json.dump(results, f, indent=1)

print(f"functions identified: {len(results)}")
print(f"total code bytes covered: {len(visited_addrs)*2} approx / {SIZE} total blob bytes")

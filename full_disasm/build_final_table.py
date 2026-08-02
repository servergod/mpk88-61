#!/usr/bin/env python3
"""Merge everything into one consolidated reference table: original
hand-named functions, pass-1 evidence-based labels, and explicit manual
overrides for functions already deeply understood by direct hand analysis
earlier in the project (which deserve their specific name, not a generic
cluster label)."""
import json

fm = json.load(open("/home/claude/mpk/full_disasm/function_map.json"))
p1 = json.load(open("/home/claude/mpk/full_disasm/labels_pass1.json"))

MANUAL_OVERRIDES = {
    "0x8011222": ("key_velocity_event_assembler", "confirmed",
        "hand-disassembled in full tonight: reads 2 raw UART bytes via uart_rx_byte_consumer, "
        "masks key to 7 bits (no-op transform), runs velocity through the 5-curve lookup table "
        "(0x080112b2), drops event entirely if key>=126, else dispatches to note_on/note_off_builder "
        "based on bit7 of the first byte", "keybed_matrix"),
    "0x80112b2": ("velocity_curve_lookup", "confirmed",
        "hand-disassembled: if get_param(218) set, always returns fixed velocity 127; else reads "
        "get_param(63) as a curve index 0-4 and looks up curve_table[curve][raw_velocity_byte] from "
        "a 5x256-byte table at 0x8011334", "velocity"),
    "0x80112b0": ("key_value_passthrough_noop", "confirmed",
        "hand-disassembled: bare `bx lr`, confirmed no-op -- raw masked byte is used directly as key index",
        "keybed_matrix"),
}

# proper sub-pools for the original 30 hand-named functions -- these were
# ALL being lumped into "core_pipeline" regardless of actual role, which
# then over-propagated that label to unrelated menu/CC-handling neighbors.
NAMED_POOL_OVERRIDES = {
    "menu_switch_dispatcher": "ui_menu",
    "menu_switch_write_param21_site": "ui_menu",
    "cc_knob_handler_a": "cc_control_handling",
    "cc_knob_handler_b": "cc_control_handling",
    "switch_style_handler": "cc_control_handling",
    "get_param": "param_storage",
    "set_param": "param_storage",
    "get_param_wrapper": "param_storage",
    "matrix_drive_line_select": "keybed_matrix",
    "matrix_row_change_handler": "keybed_matrix",
    "matrix_read_8_gpio_bits": "keybed_matrix",
    "matrix_per_row_scan": "keybed_matrix",
    "matrix_scan_orchestrator": "keybed_matrix",
    "gpio_bit_read_debounce_primitive": "keybed_matrix",
}

import os
manual_rounds = {}
for fname in ["manual_overrides_round1.json", "manual_overrides_round2.json",
              "manual_overrides_round3.json", "manual_overrides_round4.json"]:
    p = f"/home/claude/mpk/full_disasm/{fname}"
    if os.path.exists(p):
        manual_rounds.update(json.load(open(p)))

rows = []
for f in fm:
    addr = f["start"]
    if addr in MANUAL_OVERRIDES:
        label, conf, ev, pool = MANUAL_OVERRIDES[addr]
    elif addr in manual_rounds:
        m = manual_rounds[addr]
        label, conf, ev, pool = m["new_label"], m["confidence"], m["evidence"], m["pool"]
    elif not f["label"].startswith("FUN_"):
        label = f["label"]
        pool = NAMED_POOL_OVERRIDES.get(label, "core_pipeline")
        conf, ev = "confirmed", "hand-traced earlier in the project (real disassembly + Unicorn verification)"
    elif addr in p1:
        label, conf, ev, pool = p1[addr]["new_label"], p1[addr]["confidence"], p1[addr]["evidence"], p1[addr]["pool"]
    else:
        label, conf, ev, pool = None, "unknown", "no direct peripheral/param evidence found yet", None
    rows.append({"addr": addr, "label": label or f["label"], "confidence": conf, "evidence": ev, "pool": pool,
                 "n_instr": f["n_instructions"], "callees": f["callees"]})

json.dump(rows, open("/home/claude/mpk/full_disasm/reference_table.json", "w"), indent=1)

conf_counts = {}
for r in rows:
    conf_counts[r["confidence"]] = conf_counts.get(r["confidence"], 0) + 1
print("=== label confidence breakdown ===")
for k, v in sorted(conf_counts.items()):
    print(f"  {k}: {v}")
print(f"total functions: {len(rows)}")

pool_counts = {}
for r in rows:
    if r["pool"]:
        pool_counts[r["pool"]] = pool_counts.get(r["pool"], 0) + 1
print()
print("=== by pool (labeled only) ===")
for k, v in sorted(pool_counts.items(), key=lambda x: -x[1]):
    print(f"  {k}: {v}")

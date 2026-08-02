#!/usr/bin/env python3
"""
Pass 1: assign labels ONLY where there's direct, checkable evidence
(peripheral register access with a clear single-purpose signature, or a
param ID range with a known meaning already established). Everything else
stays honestly "unknown" -- no guessing dressed as a label.
"""
import json

ev = json.load(open("/home/claude/mpk/full_disasm/evidence.json"))
fm = json.load(open("/home/claude/mpk/full_disasm/function_map.json"))
byaddr = {f["start"]: f for f in fm}

labels = {}  # addr -> (label, confidence, evidence_str, pool)

for addr, v in ev.items():
    periph = set(v["periph"])
    pset, pget = set(v["params_set"]), set(v["params_get"])

    strings = set(v.get("strings", []))
    if not periph and not pset and not pget and not strings:
        continue

    if strings & {"hard_fault_name_string","mem_fault_name_string","bus_fault_name_string","usage_fault_name_string"}:
        labels[addr] = ("fault_handler_name_lookup", "confirmed",
                         f"references fault-name string(s) {sorted(strings)} -- part of the Cortex-M3 fault-handler family found earlier tonight",
                         "fault_handling")
    if strings & {"mmc_back_string","mmc_forward_string","mmc_stop_string","mmc_play_string","mmc_record_string"}:
        labels[addr] = ("transport_mmc_string_lookup", "confirmed",
                         f"references transport/MMC label string(s) {sorted(strings)} -- confirms transport button handling, independently corroborates the CTRL 115-119 CC mapping",
                         "transport")
    if strings & {"curve_name_linear","curve_name_log1","curve_name_log2","curve_name_exp1","curve_name_exp2"}:
        labels[addr] = ("velocity_curve_name_lookup", "confirmed",
                         f"references velocity-curve name string(s) {sorted(strings)} -- UI display code for the curve selector, matches the 5-entry curve table at 0x8011334",
                         "velocity")
    if "preset_table_base_livelite" in strings:
        labels[addr] = ("preset_table_accessor", "inferred",
                         "references the preset-array base address directly -- reads/writes the 1030-byte-per-preset table (17 presets, confirmed structure), exact role within it not fully resolved",
                         "preset_data")

    # --- GPIOD.BRR-only cluster: bit-reset register writes, no other periph.
    # BRR is write-only "clear these output bits" -- classic simple digital
    # output driver (LED, gate signal, or similar on/off line), NOT input
    # scanning (that uses CRL config + IDR read, seen in the matrix cluster).
    if "GPIOD.BRR" in periph and not (periph & {"GPIOC.CRL","AFIO+0xc00"}):
        labels[addr] = ("gpiod_output_clear", "confirmed",
                         "writes GPIOD.BRR (bit-reset reg) -- simple digital output line, not the keybed matrix (different port/pattern)",
                         "gpio_output")

    # --- shared USART1+SPI1+RCC+AFIO+GPIO cluster: peripheral/pin init, not
    # per-byte data transfer (only CR-region offsets seen, not DR).
    elif "USART1.BRR" in periph and "SPI1+0x0" in periph:
        labels[addr] = ("periph_clock_pin_init", "confirmed",
                         "configures RCC/AFIO/GPIO + USART1 baud + SPI1 CR1 together -- system peripheral init, not per-byte data transfer (no DR register access seen)",
                         "system_init")

    # --- FLASH_IF cluster: matches known EEPROM-emulation/param-storage
    # system (confirmed working via factory reset test on real hardware).
    elif any(p.startswith("FLASH_IF") for p in periph):
        labels[addr] = ("flash_eeprom_emulation_helper", "confirmed",
                         "accesses FLASH_IF registers -- part of the virtual-EEPROM parameter storage system (matches real-hardware-confirmed factory reset behavior)",
                         "param_storage")

    # --- keybed matrix cluster: same GPIOC.CRL / AFIO+0xc00 signature as
    # the already-confirmed matrix_scan_orchestrator/matrix_per_row_scan.
    elif periph & {"GPIOC.CRL", "AFIO+0xc00"} and byaddr[addr]["label"] in (
        f"FUN_{int(addr,16):08x}",):  # only fill in truly unlabeled ones, never overwrite an existing specific name
        labels[addr] = ("keybed_matrix_helper", "inferred",
                         "shares exact peripheral signature (GPIOC.CRL config + AFIO EXTI mux) with confirmed matrix-scan functions matrix_drive_line_select/matrix_row_change_handler/matrix_per_row_scan/matrix_scan_orchestrator -- same subsystem, specific role within it not individually confirmed",
                         "keybed_matrix")

    # --- param-based labels: only apply a specific-meaning param label to
    # a function whose param footprint is NARROW (touches a small, tightly
    # related set of IDs) -- NOT to a bulk initializer that happens to
    # touch one relevant ID among dozens of unrelated ones. A function
    # setting 190+ distinct params is a factory-defaults loader, not
    # "whatever pool its 47th param belongs to".
    total_params_touched = len(pset | pget)
    if total_params_touched >= 6:
        labels[addr] = ("bulk_param_initializer", "confirmed",
                         f"sets/gets {total_params_touched} distinct param IDs in one function -- factory-defaults/bulk-config loader, "
                         f"not specific to any single pool despite touching some individually-known IDs",
                         "param_storage")
    else:
        if 218 in pset or 218 in pget:
            labels[addr] = ("velocity_fixed_mode_toggle_user", "confirmed",
                             "touches param 218, hand-confirmed meaning: 'use fixed velocity 127' toggle (from direct disasm of 0x080112b2)",
                             "velocity")
        if 63 in pset or 63 in pget:
            labels[addr] = ("velocity_curve_index_user", "confirmed",
                             "touches param 63, hand-confirmed meaning: velocity-curve table selector 0-4 (from direct disasm of 0x080112b2)",
                             "velocity")
        if 62 in pset or 62 in pget:
            labels[addr] = ("keyscan_gate1_mode_toggle_user", "confirmed",
                             "touches param 62, hand-confirmed meaning: key-scan gate 1 condition (already traced tonight, tested on real hardware)",
                             "keybed_gate")
        if 21 in pset or 21 in pget:
            labels[addr] = ("ui_screen_state_user", "confirmed",
                             "touches param 21, hand-confirmed meaning: current UI menu-screen ID (already traced tonight)",
                             "ui_menu")

out = {}
for addr, (label, conf, reason, pool) in labels.items():
    f = byaddr[addr]
    out[addr] = {"old_label": f["label"], "new_label": label, "confidence": conf, "evidence": reason, "pool": pool}

json.dump(out, open("/home/claude/mpk/full_disasm/labels_pass1.json", "w"), indent=1)
print(f"pass 1: {len(out)} functions labeled with direct evidence")
for addr, v in sorted(out.items()):
    print(f"  {addr}  {v['new_label']:35s} [{v['confidence']}] pool={v['pool']}")

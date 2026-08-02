#!/usr/bin/env python3
"""Generate the full-system control test-recording template as CSV.
One row per physical control per bank, with the expected value from
tonight's confirmed sources, and blank columns for actual recorded
results across the three staged builds."""
import csv

rows = []

def add(control, bank, control_type, expected, source):
    rows.append({
        "Control": control, "Bank": bank, "Type": control_type,
        "Expected": expected, "Expected_Source": source,
        "01_baseline_id77_Value": "", "01_baseline_id77_Behavior": "",
        "02_gatebypass_test_Value": "", "02_gatebypass_test_Behavior": "",
        "03_gatebypass_v2_Value": "", "03_gatebypass_v2_Behavior": "",
        "Date_Tested": "", "Notes": "",
    })

# Keybed -- sample points, not all 61 (main symptom already Note:000/Data:000 on all)
add("Lowest key (far left)", "-", "Note", "36 (C2)", "note_mapping_fn, hand-verified tonight")
add("Middle key (approx)", "-", "Note", "~66", "computed from BASE=36 + offset")
add("Highest key (far right)", "-", "Note", "96 (C7)", "note_mapping_fn, hand-verified tonight")

# Knobs K1-8, Banks A/B/C
for bank, base in [("A", 12), ("B", 20), ("C", 28)]:
    for i in range(1, 9):
        add(f"K{i}", bank, "Knob CC", f"CC {base + i - 1}", "user LCD-confirmed direct observation")

# Faders F1-8, Banks A/B/C
for bank, base in [("A", 42), ("B", 50), ("C", 58)]:
    for i in range(1, 9):
        add(f"F{i}", bank, "Fader CC", f"CC {base + i - 1}", "pasted table, LCD-confirmed by user")

# Switches S1-8, Banks A/B/C
for bank, base in [("A", 72), ("B", 80), ("C", 88)]:
    for i in range(1, 9):
        add(f"S{i}", bank, "Switch CC", f"CC {base + i - 1}", "pasted table, LCD-confirmed by user")

# Pads 1-16, Banks A/B/C/D -- from Reason Lua codec (Bank D confirmed) + pasted table (A/B/C, unconfirmed vs LCD)
pad_hex = {
    1:(0x25,0x35,0x45,0x55),2:(0x26,0x36,0x46,0x56),3:(0x2A,0x3A,0x4A,0x5A),4:(0x2E,0x3E,0x4E,0x5E),
    5:(0x28,0x38,0x48,0x58),6:(0x2D,0x3D,0x4D,0x5D),7:(0x2F,0x3F,0x4F,0x5F),8:(0x30,0x40,0x50,0x60),
    9:(0x21,0x31,0x41,0x51),10:(0x24,0x34,0x44,0x54),11:(0x22,0x32,0x42,0x52),12:(0x27,0x37,0x47,0x57),
    13:(0x2B,0x3B,0x4B,0x5B),14:(0x29,0x39,0x49,0x59),15:(0x2C,0x4C,0x4C,0x5C),16:(0x31,0x41,0x51,0x61),
}
for pad, (a,b,c,d) in pad_hex.items():
    add(f"Pad {pad}", "A", "Pad Note", f"Note {a} ({int(a)})", "pasted table -- NOT independently confirmed")
    add(f"Pad {pad}", "B", "Pad Note", f"Note {b} ({int(b)})", "pasted table -- NOT independently confirmed")
    add(f"Pad {pad}", "C", "Pad Note", f"Note {c} ({int(c)})", "pasted table -- NOT independently confirmed")
    add(f"Pad {pad}", "D", "Pad Note", f"Note {d} ({int(d)})", "Reason Lua codec, ch16 -- more confirmed than A/B/C")

# Transport / MMC
add("Rewind <<", "-", "Transport CC", "CC 115", "Reason codec + independently confirmed via embedded UI string CTRL 115 tonight")
add("Fast Forward >>", "-", "Transport CC", "CC 116", "same, CTRL 116")
add("Stop", "-", "Transport CC", "CC 117", "same, CTRL 117")
add("Play", "-", "Transport CC", "CC 118", "same, CTRL 118")
add("Record", "-", "Transport CC", "CC 119", "same, CTRL 119")

# Wheels / aftertouch / pedals
add("Mod Wheel", "-", "CC", "CC 1", "standard MIDI convention, Reason codec confirms")
add("Pitch Bend", "-", "Pitch Bend", "14-bit pitch bend (e0-ef status)", "standard MIDI")
add("Aftertouch (channel pressure)", "-", "Channel Pressure", "status D0", "Reason codec")
add("Expression Pedal", "-", "CC", "CC 11", "Reason codec")
add("Damper/Sustain Pedal", "-", "CC", "CC 64", "Reason codec, standard MIDI")

# Performance controls
add("Octave Up", "-", "Function", "shifts note base +12 per press", "manual + note_mapping_fn formula")
add("Octave Down", "-", "Function", "shifts note base -12 per press", "manual + note_mapping_fn formula")
add("SPLIT", "-", "Function/Mode", "toggles two-zone keyboard split, LED lights when active", "Quickstart Guide manual, hand confirmed tonight -- exact firmware handler NOT yet located")
add("Full Level", "-", "Function/Mode", "forces max velocity on pads", "Quickstart Guide manual")
add("1/2 Level", "-", "Function/Mode", "reduces pad velocity range", "Quickstart Guide manual")
add("Arpeggiator", "-", "Function/Mode", "toggles arp on/off", "LCD string ARP ON/OFF found tonight")
add("Latch", "-", "Function/Mode", "latches arp notes", "LCD string ARP LATCH found tonight")
add("Tap Tempo", "-", "Function", "sets tempo by tap interval", "manual")
add("Pad Bank A/B/C/D select", "-", "Function", "switches active pad bank", "manual + firmware pad bank structure")

with open("/home/claude/mpk/test_records/FULL_CONTROL_TEST_TEMPLATE.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

print(f"wrote {len(rows)} test rows to test_records/FULL_CONTROL_TEST_TEMPLATE.csv")

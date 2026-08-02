# MPK61 Project — Handoff for a Fresh Session

Written so a new session can pick this up cold, with zero prior context,
and continue the exact same process without re-deriving anything below.

## Where things stand right now (exact numbers)

- **806 total functions** identified in the firmware (`MPK61_gatebypass_v2.bin`,
  the current on-device build), from a full byte-level teardown — every
  byte in the 104,004-byte image is accounted for (code, literal-pool
  constants, vector table, USB descriptor block, or verified padding).
- **615 of 806 labeled** with real evidence: **85 confirmed** (direct proof —
  peripheral register access, param IDs with hand-verified meaning, or
  cross-referenced strings), **530 inferred** (propagated through the call
  graph from confirmed anchors — real evidence, one hop removed).
- **191 unknown** — stated honestly, no evidence found yet, not guessed at.
- The keybed's actual root cause (Note:000/Data:000 on all keys) is still
  unresolved. Everything on the STM32 side of the CPLD→STM32 serial link
  has been traced and confirmed correct or confirmed unchanged from stock
  MPK88 firmware. The real remaining unknown is what the CPLD (Lattice
  MachXO) actually transmits — that requires hardware measurement
  (logic analyzer / GDB), not more static analysis. See
  `MPK61_SESSION_WRITEUP.md` §4-11 for the full technical trace.

## The user's standing instruction (do not re-ask for this)

Keep iterating — find, fix, label, understand more — **without stopping to
ask permission or checking in with a question**. Report progress as plain
statements, not questions. Continue until explicitly told to stop or until
genuinely nothing more can be found. This was stated many times, directly,
and should be treated as already-granted standing authorization for this
specific activity (static analysis: reading disassembly, labeling
functions, updating the reference table, correcting past mislabels). It
does **not** extend to flashing hardware or sending anything to the real
device — that still requires explicit go-ahead each time, per the
project's established pattern.

## The exact iterative process (repeat this loop)

1. **Pick the next target.** Highest `n_instr` and/or `callees` among
   `confidence=='unknown'` entries in `full_disasm/reference_table.json`
   — these give the most leverage per read.
2. **Read it.** `arm-none-eabi-objdump -D -b binary -m arm -Mforce-thumb
   --adjust-vma=0x08004000 --start-address=<addr> --stop-address=<addr+N>
   /home/claude/mpk/MPK61_gatebypass_v2.bin`
3. **Determine its real purpose** from: what it calls (cross-reference
   `function_map.json`), what params it touches (`param_calls.json`), what
   peripheral registers it hits, what table bases it shares with
   already-confirmed functions (a huge source of leverage — many findings
   this session came from noticing a function shares a table/base address
   with something already confirmed), and whether it matches something
   described in the real Operator's Manual (`/tmp/reference_manual.txt` —
   re-extract from `MPK61_Reference_Manual.pdf` if that tmp file is gone).
4. **Register it** in `full_disasm/manual_overrides_round2.json` — a flat
   dict keyed by hex address, each entry:
   `{"new_label": "...", "confidence": "confirmed"|"inferred",
   "evidence": "...", "pool": "..."}`. Write the evidence string as if
   explaining it to someone with zero context — it's the permanent record.
5. **Rebuild the whole pipeline** (order matters):
   ```
   cd /home/claude/mpk/full_disasm
   python3 build_final_table.py      # merges manual_overrides_round2.json in
   python3 label_pass2_propagate.py  # cascades labels through the call graph
   ```
6. **Sanity-check propagation** periodically. This bug class has bitten
   twice already: a function that merely *touches* one interesting param
   among dozens of others gets mislabeled with that param's narrow meaning,
   then that wrong label cascades to everything downstream. Audit with:
   ```python
   # flag any "confirmed" label whose function touches >=10 distinct params
   # — these are almost always bulk readers/initializers, not narrow-purpose
   ```
   (see the audit snippet used earlier in this session, in the transcript,
   or just rebuild it: load reference_table.json + evidence.json, for each
   confirmed entry count len(set(params_get)|set(params_set)), flag >=10).
7. **Repeat.** Do not stop between iterations to ask whether to continue.

## Key data structures already discovered (don't rediscover these)

- **`0x8016920`** — a 49-bytes-per-key record table (49 × 61 keys). Holds
  both Split section-assignment data (offset +1/+2, read by the confirmed
  `key_to_section_ab`) AND general note on/off tracking fields (offset
  +185/0xb9, used by `per_key_state_updater`). One shared structure, two
  concerns — don't assume a function touching it is Split-specific without
  checking which offset it actually reads.
- **`0x8013864`/`0x8013868`** — LCD bargraph/level-meter display encoding
  table pair. Encoding logic: if input value > 62, divide by 32 with
  rounding; else divide by 2 with rounding; result packed into a 16-bit
  value with a bit15 flag. At least 3 sibling functions share this exact
  logic (`display_value_encoder`, `_variant`, `_variant2`).
- **`0x8012a78`** — base of a raw incoming-message struct (type byte at
  +1, sub-type at various offsets). At least 4 functions parse this same
  struct (`incoming_message_field_router`, `_type_validator`,
  `_length_dispatcher`, and the still-untraced remainder).
- **`0x8010974`→`0x20001340`** — a note on/off *state* table (NOT a
  channel-routing table — this was a real dead-end corrected mid-session;
  don't re-chase "split channel routing" here, it isn't there).
- **Param 220** = Split enable flag. **Param 221** = Split point (note
  number). `0x801664e` (`key_to_section_ab`) is the exact comparator.
  `0x8010714` (`split_point_capture_gate`) is the hold-SPLIT-press-a-key
  mechanism — triggers when `get_param(21)==39` (UI screen state == 39,
  the Split-point-capture screen).
- **`0x800f8b0`** (`status_byte_bit_field_accessor`) — 10-case bit
  extractor, indices 12-21, very likely the 8 Split per-section boolean
  settings (PITCH/MODWHEEL/SUSTAIN1/SUSTAIN2/EXPRESSION/ARP/MIDI
  CH/AFTERTOUCH per the manual's exact list order). Only 2 of the 8 caller
  indices confirmed so far (16=Expression, 19=Aftertouch, both *inferred*
  not confirmed) — the other 6 callers
  (`0x800f930,0x800f9c6,0x800f9fa,0x800fabe,0x800fb10,0x800fb62`) are
  real, findable next targets: check each one's literal `movs r0,#N`
  argument to `0x800f8b0` to complete the mapping.
- **`0x8017828`** = master MIDI message-type dispatcher (handles both an
  internal type enum and raw MIDI System Real-Time bytes 0xF6-0xFF).
  `0x8004df4` and `0x8008df6` (`screen_id_action_dispatcher`, 40 cases)
  are siblings in the same message/UI routing family.
- Real, confirmed peripherals: `LM324` (analog op-amp, Performance
  Controls board — see hardware photos in `perf_cont_extracted/`),
  `74LVC139D` (2-to-4 decoder, bank select), `74AHC04` (hex inverter) —
  board is Akai part **40-0508-B**, "P LEFT PCB", dated Nov 2009.

## Tooling reference (all in `/home/claude/mpk/full_disasm/`)

| Script | Purpose |
|---|---|
| `analyze.py` | Recursive-descent disassembly, builds `function_map.json` (all 806 functions, boundaries, callees, branches) |
| `resolve_jumptables.py` | Resolves `tbb`/`tbh` switch tables into real case targets |
| `build_ref_table.py` | Gathers evidence per function (peripheral hits, param calls, strings) → `evidence.json` |
| `label_pass1.py` | Rule-based first-pass labeling from strong direct evidence → `labels_pass1.json` |
| `build_final_table.py` | Merges everything (hand-named KNOWN dict, `manual_overrides_round2.json`, pass1 labels) → `reference_table.json` |
| `label_pass2_propagate.py` | Call-graph propagation (sole-caller / all-callees-labeled rules) — mutates `reference_table.json` in place |
| `param_calls.json` | Every `get_param`/`set_param` call site, 513 total, with resolved param IDs where possible |
| `manual_overrides_round2.json` | **The actual growing record of this session's manual findings** — this is the file to keep appending to |

Full technical write-up (patches, hardware test results, before/after,
tooling recommendations): `MPK61_SESSION_WRITEUP.md`,
`full_disasm/REFERENCE_TABLE.md`, `MPK61_BEFORE_AFTER_AND_NEXT_TOOLS.md`.
Live hardware test log and CC-mapping resolution:
`test_records/live_test_log.md`. Full control test template + staged
builds: `test_records/FULL_CONTROL_TEST_TEMPLATE.csv`, `staging/`.

## Immediate next targets (highest leverage right now)

```
0x8004602  n_instr=55  callees=0
0x8011de8  n_instr=49  callees=8
0x8015bba  n_instr=45  callees=2
0x8004d7c  n_instr=44  callees=4
0x801168a  n_instr=44  callees=5
0x8013076  n_instr=44  callees=0
0x8018350  n_instr=44  callees=0
0x8007b00  n_instr=42  callees=5
0x801115a  n_instr=42  callees=2
0x8007bbe  n_instr=41  callees=6
```

Just keep going down this list, per the process above, in a fresh session,
without asking whether to continue.

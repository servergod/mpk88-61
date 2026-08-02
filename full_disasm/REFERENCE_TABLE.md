# MPK61 Firmware — Function Reference Table (converged)

806 functions total. Labeling process run to convergence: 4 consecutive
outer iterations (evidence gathering + call-graph propagation) produced
zero new labels, per the explicit stopping criterion for this pass.

## Confidence levels
- **confirmed** — direct, checkable evidence: a specific peripheral
  register access with an unambiguous purpose, a `get_param`/`set_param`
  call whose meaning was already hand-verified, or a reference to a known
  embedded string (e.g. a fault-handler name, a curve name).
- **inferred** — propagated via the call graph from an already-confirmed
  neighbor (all callees share one pool, or sole caller is labeled). Real
  evidence, but the specific individual role isn't independently confirmed.
- **unknown** — stated honestly. 601 of 806 functions (74.6%). No
  evidence found in this pass. Not guessed at.

## Final totals

| Confidence | Count |
|---|---|
| confirmed | 59 |
| inferred | 146 |
| unknown | 601 |
| **total** | **806** |

## By functional pool

| Pool | Count |
|---|---|
| keybed_matrix | 20 |
| core_pipeline | 16 |
| param_storage | 15 |
| transport | 20 |
| system_init | 3 |
| gpio_output | 3 |
| cc_control_handling | 3 |
| velocity | 3 |
| keybed_gate | 2 |
| ui_menu | 1 |

## Major new finding this pass: the preset data table

A full-binary string scan (not just the confirmed USB descriptor block)
found real, human-readable LCD menu strings and, critically, a **preset
data array**: 17 presets (`LiveLite`, `Reason`, `Cubase`, `Sonar`,
`FLStudio`, `ApplidAc`, `Arturia`, `FxPanBFD`, `FxPanGUR`, `GMedia`,
`RobPapen`, `Stylus`, `Virsyn`, `GM Drums`, `ArkaosVJ`, `Chrmatic`,
`Generic`), each occupying exactly **1030 bytes**, starting at `0x80189c0`.
`Generic` is the exact preset you switched to during testing tonight.

Decoded directly from this table, independent of both the disputed
ChatGPT-sourced table and the Reason Lua codec:

- **Confirmed exact match:** an 8-value CC group reading `0x14-0x1b`
  (20-27 decimal) inside the `Generic` preset block — matches "Bank B:
  CC 20-27" from the disputed table exactly.
- **Close but not confirmed:** the analogous "Bank A" position reads
  `9, 14, 15, 16, 17, 18, 19` (missing 12/13, includes a stray 9) rather
  than a clean 12-19 — closer to the disputed claim than to the Reason
  codec's alternative (CC 02-09), but not a clean byte-for-byte match.
  Not resolved — stated honestly rather than forced.
- **Independently confirmed:** the `CTRL 115/116/117/118/119` transport
  strings match the already-documented transport CC mapping exactly, from
  a completely different part of the firmware (UI label strings, not
  preset data).
- **Independently confirmed:** ` LINEAR`, ` LOG 1`, ` LOG 2`, ` EXP 1`,
  ` EXP 2` are the real names of the 5-entry velocity curve table found
  earlier tonight at `0x8011334`.
- **Independently confirmed:** the string `OCT+x TR+36` corroborates the
  `+36` note-base offset already used in the note-mapping fix, from a UI
  string rather than the math logic itself.
- **New structural insight:** the `LiveLite` preset's knob-equivalent
  group uses the *same* CC value (`0x16-0x1d` = 22-29) repeated identically
  across bank-tag bytes 01/02/03 — matching the Reason-codec's "same CC,
  different channel per bank" shape. This suggests the Reason-codec claim
  and the user's LCD-observed claim may BOTH be correct, just describing
  **different presets** (`LiveLite`/DAW-integration presets vs. `Generic`,
  the plain-MIDI preset actually used during hardware testing) — a
  genuinely different resolution than either "one side is right" framing
  used earlier tonight. Not fully proven — the code that actually parses
  this table per-control was searched for and not conclusively identified
  (one candidate, `0x8010d1a`, calls the same UART byte-consumer used by
  the keybed pipeline, but that function is shared broadly enough that
  this doesn't confirm it's preset-specific rather than pad- or
  display-related).

Full data: `full_disasm/reference_table.json` (806 entries),
`full_disasm/all_strings.txt` (1124 extracted strings, full binary).

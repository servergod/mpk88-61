# MPK61 Verified MIDI Mapping Table

Built only from sources with real, checkable byte-level or disassembly-level
evidence. No numbers here came from an AI's unverified claim. Each section
states its actual source. Where something is unconfirmed, it says so.

## Keybed (from our own STM32 disassembly, Unicorn-verified)

- Function: `0x080107E0`
- Formula: `note = key_index + BASE + transpose_offset + 12*octave_offset`
- `BASE` was hardcoded `21` (A0, 88-key default) in the original MPK88 image.
  Patched to `36` (C2) for the 61-key refactor. This is the actual bug this
  whole project has been fixing — see `MPK61_firmware_notes.md` sections 12.1-12.6.
- Key 0 (lowest, far left) = note 36 = C2. Key 60 (highest, far right) = note
  96 = C7. Middle C (note 60/C4) is not physically on this keybed at all —
  the range is C2 to C7, middle C would be one octave above the actual
  keybed's own MIDI-note midpoint.
- Base note 36 is **not hardware-confirmed** — see section 12.6 of the notes
  file for the reasoning (5-octave phrasing in the official manual) and its
  confidence level.

## Knobs, Faders, Switches (from the real Akai-published Reason Lua codec,
`Preset Support Files/Reason/Codecs/Lua Codecs/AkaiMPK61_1.00.lua` —
byte-level `pattern="..."` entries, not abstraction, not guessed)

Bank is selected by **MIDI channel**, not by CC range. Same CC numbers
repeat on channels 1/2/3 for banks A/B/C. This is confirmed independently by
the Cubase remote XML (`MPK88_61_Cubase.xml`), which uses the same
channel-per-bank shape via its `<chan>` field.

| Control | Bank A (ch 1, `b0`) | Bank B (ch 2, `b1`) | Bank C (ch 3, `b2`) |
|---|---|---|---|
| Knob 1-8 | CC `02`-`09` (2-9) | CC `02`-`09` | CC `02`-`09` |
| Switch 1-8 | CC `15`-`1C` (21-28) | CC `15`-`1C` | CC `15`-`1C` |
| Fader 9-16 (Bank B, confirmed) | — | CC `0F`-`13` (15-19)* | — |
| Fader 17-24 (Bank C, confirmed) | — | — | CC `0C`-`13` (12-19) |

*Fader Bank A (Fader 1-8) pattern lines were above where this file's excerpt
started — not yet re-confirmed by re-reading the full file top-to-bottom.
Flagging as unconfirmed rather than guessing the values by extrapolation.

**Explicitly contradicted by this real source:** the earlier claim
("Knobs Bank A: CC 12-19, Bank B: CC 20-27, Bank C: CC 28-35") from an
unverified AI conversation. That pattern does not match — real data shows
the same CC numbers across banks, differentiated by channel, not
sequential CC ranges per bank.

## Pads (same Reason Lua codec)

- Pad Bank D (only bank confirmed in the excerpt read): Note On, channel 16
  (`9F`), notes `00`-`0F` (0-15 decimal) for Pad D1-D16.
- Banks A/B/C for pads not yet confirmed from this source — the codec file
  has more content below what's been read so far.

## Other confirmed controls (same source)

- Mod Wheel: CC 1 (standard MIDI convention)
- Expression: CC 11 (standard)
- Damper Pedal: CC 64 (standard)
- Channel Pressure: status `D0` (Channel Pressure, channel 1)
- Pitch Bend: standard 14-bit pitch bend (`e?` status)

## Transport Controls (from the official Akai PDF,
`MPK61_transport_controls_midi_details.pdf`, read earlier tonight)

- Rewind (`<<`): CC 115
- Fast Forward (`>>`): CC 116
- Stop: CC 117
- Play: CC 118
- Record: CC 119
- Also transmit MMC (`F0 7F 7F 06 [cmd] F7`) depending on mode.

## What's still unconfirmed / not yet checked

- Full Fader Bank A (1-8) CC numbers — need to re-read the Lua codec from
  the top rather than the excerpt already seen.
- Pad Banks A/B/C note numbers.
- Whether the real hardware's actual firmware (not the Vyzex software side)
  uses these exact same CC assignments — everything above describes what
  *Vyzex/DAW-integration tooling expects to receive*, which should match
  the firmware's real output for a factory-default preset, but this has
  not been independently confirmed via live MIDI monitoring against the
  actual connected device tonight.
- 3 more PDFs exist in the Vyzex package that haven't been opened yet:
  `Vyzex MPK88-61 User's Guide Manual.pdf`, `Vyzex MPK88-61 Preferences.pdf`,
  `Vyzex MPK88-61 Quick-Start Manual.pdf` — likely overlapping with what's
  already covered (the standalone Quickstart/Reference PDFs already read),
  not yet verified as redundant.

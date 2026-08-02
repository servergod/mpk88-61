# Live Hardware Test Log

## Build 01 (baseline_id77.syx) — first real test

- **Keybed:** Note:000/Data:000 confirmed present, same as always. Confirms
  symptom predates all of tonight's patches — not introduced by the
  gate-check bypass or the note-boundary fix.
- **K1, Banks A/B/C: all read CC 22.** Directly matches the LiveLite preset's
  raw data decoded from the binary tonight (bank-tagged 01/02/03, same CC
  0x16=22 repeated across all three banks). Real hardware confirmation of
  the "same CC across banks, differentiated by channel" structure for this
  specific preset.
- **Prediction to verify next:** K2=23, K3=24, K4=25, K5=26, K6=27, K7=28,
  K8=29, all identical across banks A/B/C, per the same decoded table.

## CC-Mapping dispute — RESOLVED (complete hardware confirmation)

Real LCD readings, LiveLite preset, all three banks:

| Control | CC (all banks, channel = bank #) |
|---|---|
| Knobs K1-K8 | CC 22-29 |
| Faders F1-F8 | CC 12-19 |
| Switches S1-S8 | CC 32-39 |

Every value matches the LiveLite preset block decoded from the firmware
binary tonight, byte-for-byte. Bank differentiates by MIDI channel
(A=ch1, B=ch2, C=ch3), same CC number across all three banks.

**Neither prior source was fully correct:**
- Reason Lua codec claimed Knobs = CC 02-09 -- wrong.
- The disputed pasted ChatGPT table claimed Knobs = CC 12-19 -- wrong for
  knobs, but that's exactly the real **Fader** CC range. Likely an
  upstream mislabeling (faders described as knobs) in whatever generated
  that table, not a fabrication of the number itself.

This is now closed with direct, complete, real-hardware evidence -- not
inference, not a disputed secondary source.

## CORRECTION — important, not a simple resolution

User confirmed: actually on preset #17 (Generic) during the above test,
NOT preset #1 (LiveLite) as I assumed. Re-checked Generic's own raw data
block at the same structural offset -- it does NOT match (Generic has a
different, non-bank-tagged, messier sequence: 9,14-19,34-3c,53x5,55-5b,
14-1b -- not the clean CC22-29/12-19/32-39 pattern).

**Real finding: the hardware is transmitting LiveLite's stored CC values
while the display shows Generic (#17).** Either Generic doesn't define its
own knob/fader/switch mapping and falls through to a previously-loaded
preset's data, or there's a real bug where preset selection updates
display/pad state but doesn't correctly reload continuous-controller
config into whatever live state drives actual MIDI transmission.

This directly parallels the keybed symptom shape (display state and actual
transmitted/computed state disagreeing) -- worth keeping in mind as a
possible systemic pattern, not just a keybed-specific issue. NOT yet
root-caused. Flagging plainly rather than treating the earlier CC-mapping
match as a closed, clean resolution.

## CORRECTION #2 — original match stands

User clarified: after reboot the device defaults to preset #1 (LiveLite),
not #17 (Generic) as stated in the prior message -- that was a mistake on
the user's end, not a real preset-switching bug. The original CC-mapping
match (K1-8=22-29, F1-8=12-19, S1-8=32-39, all matching LiveLite's decoded
binary data exactly) is confirmed correct and stands as the valid result.
The "display vs. transmitted state mismatch" finding logged above was
based on this mistaken premise and should NOT be treated as a real
firmware finding -- no evidence of that bug exists. Leaving both log
entries in place chronologically rather than deleting, for an honest
record of the back-and-forth.

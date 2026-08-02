# Full System Control Test — How To Use This

## Staged builds (in `/home/claude/mpk/staging/`, load in this order)

1. `01_baseline_id77.syx` — the pre-tonight baseline (table refactor + note-base
   fix only, header ID 77). This is your reference point.
2. `02_gatebypass_test.syx` — baseline + both key-scan gate checks removed.
3. `03_gatebypass_v2.syx` — baseline + gate checks removed + note-boundary
   fix (`<88`→`<61`). This is the most recent build, already on the device
   from tonight.

Flash each one in order (hold `<<`+`STOP`+`REC` while reconnecting USB →
ERASE OK → ENTER → SEND SYSEX), test the full control list, record results,
then move to the next build. Same procedure each time, so results are
directly comparable across builds.

## Recording sheet

`FULL_CONTROL_TEST_TEMPLATE.csv` — 158 rows, one per physical control per
bank/mode. Columns:

- **Control / Bank / Type** — what you're testing
- **Expected** — the value tonight's work says it *should* be, with
  **Expected_Source** stating exactly where that number came from and how
  confident it is (hand-confirmed vs. pasted-table-unconfirmed — some pad
  bank A/B/C values are flagged as NOT independently confirmed, so a
  mismatch there isn't necessarily a bug)
- **0X_..._Value / 0X_..._Behavior** — fill in what you actually see on the
  LCD/MIDI monitor for each of the 3 builds
- **Date_Tested** — so results stay dated as you go
- **Notes** — anything odd, physical issues, uncertainty

Fill in only what's practical — the keybed rows are just 3 sample points
since the main symptom (Note:000/Data:000) is already known to be identical
across all 61 keys; no need to test all of them individually unless you
want to confirm that's still uniformly true.

## What this settles

Comparing the same control across all 3 builds tells you definitively
whether any of tonight's patches changed *anything* system-wide, not just
the keybed — the original ask ("full testing behavior of everything to see
if any of your changes had ANY effect"). If a control's value/behavior is
identical across all 3 builds, that patch didn't touch it. If a value is
missing/wrong from the very first baseline build too, that's a pre-existing
issue, not something tonight's patches caused.

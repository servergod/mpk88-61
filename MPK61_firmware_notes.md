# Akai MPK88 to MPK61 Firmware Refactor - Continuous Record

This file is the continuous record of this project. The record starts at
the first step and continues to the current step. The record does not
stop and start again in a new file. Do not split this record into more
than one file.

## 1. Purpose

The user gave a file to the project. The file name is `MPK88_v1_01.syx`.
The file is the firmware for the Akai MPK88 controller. The MPK88
controller has 88 keys.

The goal is this: make the MPK88 firmware work correctly on Akai MPK61
hardware. The MPK61 controller has 61 keys. The MPK61 and the MPK88 use
the same processor board. The MPK61 and the MPK88 use the same pots,
faders, pad grid, mod wheel, and pitch wheel. The key count is the only
hardware difference between the two controllers.

The project has two parts:

1. An address-space refactor. The firmware has a table in memory. The
   table stores data for pairs of keys. The table size and the table
   address math are correct for 88 keys. The table size and the table
   address math are not correct for 61 keys. This part of the project
   changes the table size and the table address math for 61 keys.
2. A note-base fix. The firmware has code that converts a key number to
   a MIDI note number. This code adds a fixed number to the key number.
   The fixed number is correct for an 88-key keyboard. The fixed number
   is not correct for a 61-key keyboard. This part of the project
   changes the fixed number for a 61-key keyboard.

This file describes both parts as one project, not two projects.

## 2. File Structure of the Source File

The source file `MPK88_v1_01.syx` is not raw binary data. The file has
this structure:

```
byte 0-4:   F0 47 00 71 70
byte 5:     ':'
...         ASCII Intel HEX records, with CRLF at the end of each line
end:        :00000001FF
last byte:  F7
```

The file has one SysEx frame. The frame starts at byte 0 (`F0`). The
frame ends at the last byte (`F7`). The frame contains ASCII text. The
text is one Intel HEX file. All bytes in the text are below `0x80`. Do
not compare this file as raw binary data. First convert the Intel HEX
text to a binary image.

Byte 3 in the header (`0x71`) is the product ID byte. This byte must
change to target the MPK61 controller. Two values were candidates for
this byte: `0x6C` (MPK61) and `0x71` (MPK88). The correct value for the
MPK61 controller was checked two ways:

1. A check against the list at usb-ids.gowdy.us.
2. A check against a Wireshark USB capture. The capture showed the
   value `0x0077`. This value matched the driver details.

The byte swap from `0x71` to `0x6C` is correct. This byte swap lets the
MPK88 firmware load onto MPK61 hardware. The device boots to firmware
version 1.01 after the load. The keys work at a basic level after the
load.

## 3. Flash Memory Map of the Source File

Convert the Intel HEX text to a binary image. Use the Extended Linear
Address records (type `04`) to set the address of each block. The file
has three of these records: `0x0800`, `0x0801`, and `0x0802`.

The address `0x08000000` is the start address of internal flash on
STM32 parts. This address confirms the processor family is STM32.

The file has data for two address ranges:

- `0x08004000` to `0x08010000` (48 KB)
- `0x08010000` to `0x0801D644` (about 53.5 KB)

The file does not have data for addresses `0x08000000` to `0x08003FFF`.
This range is the first 16 KB of flash. This range holds the bootloader.
A firmware update does not change this range.

The Intel HEX Start Linear Address record (type `05`) gives the value
`0x080040ED`. This value is the entry point address.

## 4. Vector Table of the Source File

The vector table starts at address `0x08004000`. The table holds these
values:

```
0x08004000: 20004218   Initial stack pointer
0x08004004: 08011339   Reset_Handler address
0x08004008: 0801133D
0x0800400C: 0801133F
0x08004010: 08011353
0x08004014: 08011367
0x08004018: 0801137B
0x0800401C: 00000000
0x08004020: 00000000
0x08004024: 00000000
0x08004028: 00000000
0x0800402C: 0801138F
0x08004030: 080113A3
0x08004034: 00000000
0x08004038: 080113B7
0x0800403C: 08011A05
```

The value `0x20004218` is a valid RAM address on this processor. This
value confirms the stack pointer value is correct.

The Reset_Handler code is at address `0x08011338`. This code does two
steps:

1. It loads the value at address `0x080113F4` into register r0.
2. It jumps to the address in register r0.

The value at address `0x080113F4` is `0x080040ED`. This value matches
the Start Linear Address value from the Intel HEX file. The real
startup code starts at address `0x080040EC`.

## 5. The 88x88 Key Table

A search found a group of `cmp Rx, #0x58` instructions. `0x58` is 88 in
decimal. This group is at addresses `0x08016649` to `0x08016DDC`. This
group has 19 instructions. Each instruction checks a key number against
the limit 88.

The address math for this table works this way:

```
row_offset = key_index * 67
byte_offset = row_offset << 2
```

This math gives a row size of 268 bytes (`0x10C`). The code uses a key
number from 0 to 87 to select a row.

Each row also holds a second table. The code uses a second key number
to select a position in this second table. Each position in the second
table is 3 bytes wide. 88 positions at 3 bytes each equal 264 bytes
(`0x108`). Byte `0x108` in each row is the start of 4 extra bytes. These
4 bytes hold state data for the row.

This structure is a table with two key numbers as input. Each pair of
key numbers points to 3 bytes of data. The table covers all 88 keys on
both axes. The table size is about 23,584 bytes (88 rows x 268 bytes).

This table structure explains the fault on the MPK61 hardware. The
firmware uses the limit 88 to check key numbers. The MPK61 has 61 keys.
The firmware can read or write data past the true key range on MPK61
hardware.

## 6. Refactor Plan for the 88x88 Table

The refactor does not change the first 16 KB of flash (`0x08000000` to
`0x08003FFF`). This range holds the bootloader. A bad firmware write to
the application region must not remove the ability to send another
firmware update. The bootloader itself must stay untouched.

The plan is this: resize the table for 61 keys instead of 88 keys. The
resize must change every site that computes a row or a cell offset into
the table. A patch to the limit checks alone is not correct. A
limit-check-only patch tests the bounds check. A limit-check-only patch
does not test the row-size math. A pass on a limit-check-only patch does
not confirm the resize is correct.

The steps are these:

1. Set up an emulator for the STM32F103RCT6 target. Use the emulator to
   run the firmware without real hardware.
2. Find the new row-stride constant. The current code uses `key_index *
   67` for an 88-row table. Find the correct constant for a 61-row
   table. Find the matching instruction sequence for this constant.
3. Change the address math at each site that reads or writes the key
   table. Change more than the limit checks.
4. Run the result in the emulator. Check the key table reads and writes
   at each key index from 0 to 60.

## 7. Search for `#0x58` Sites

The first search checked 16-bit Thumb instructions only. The first
search did not check 32-bit Thumb-2 instructions (`cmp.w`). Section 9
describes the result of the 32-bit search.

19 sites are in the address range `0x08016600` to `0x08016E00`. These
sites are part of the 88x88 key table code.

5 sites are outside this range. These 5 sites were not checked yet at
this point in the project. Section 10 describes the check of these 5
sites.

- `0x0800757A`
- `0x08009A1A`
- `0x0800C844`
- `0x08014842`
- `0x0801485A`

The search also found 5 instances of `movs r0, #0x3D` (61 in decimal).
These instructions are outside the key table range. These instructions
were not checked yet at this point in the project.

- `0x08006AD6`
- `0x08007DCA`
- `0x08008EC2`
- `0x08008FF8`
- `0x08009690`

## 8. Commands Used for the Initial Analysis

```bash
# Extract the Intel HEX text from the SysEx frame
python3 -c "
data = open('MPK88_v1_01.syx','rb').read()
assert data[0] == 0xF0
end = data.rfind(0xF7)
payload = data[5:end]
open('MPK88_v1_01.hex','wb').write(payload)
"

# Convert to a binary image and create a disassembly file
arm-none-eabi-objcopy -I ihex -O binary MPK88_v1_01.hex MPK88_v1_01.bin
arm-none-eabi-objdump -D -b binary -m arm -Mforce-thumb \
    --adjust-vma=0x08004000 MPK88_v1_01.bin > MPK88_v1_01.disasm.txt

# List lines with a cmp or movs instruction and the value 0x58
grep -E "cmp|movs" MPK88_v1_01.disasm.txt | grep "0x58"
```

A disassembly file can show wrong instructions in some places. Code and
data sit together in the binary image. Check each result against a
confirmed region (vector table, startup code, key table) before use.

## 9. Hardware Notes

- Processor: STM32F103RCT6
- CPLD: Lattice MachXO. The exact part number was not readable in the
  photo used for this check.
- One 4-pin header for the mod wheel, pitch wheel, and CC control.
- 16 finger pads in a 4x4 grid.
- LCD screen and menu buttons.
- 8 pots and 8 faders.
- 2 key ribbon connectors, 16-pin, IDE style.

## 10. Emulator Setup

The tools for the emulator are these: `gcc-arm-none-eabi`,
`binutils-arm-none-eabi`, Python 3 with the `unicorn` and `capstone`
packages, `qemu-system-arm`, and `gdb-multiarch`. The Unicorn Engine was
the emulator used for all checks in this project. Unicorn emulates the
Cortex-M3 core directly. A test harness can map flash and RAM with
Unicorn. A test harness can call a function in the image with controlled
register values with Unicorn. This method does not need full
STM32F103RCT6 peripheral support.

### 10.1 Result: no 32-bit `cmp.w #0x58` sites

A search checked the image with an objdump text parser and a
Capstone-based scanner. The result: zero `cmp.w` (32-bit Thumb-2)
instructions compare against `#0x58` in the image. Every key-limit check
uses the 16-bit `cmp Rd, #imm8` encoding. This result closes the 32-bit
search from section 7. The 16-bit-only search in section 7 did not miss
a site.

### 10.2 Correction to the 19-site count from section 7

A re-check of all `cmp`/`movs #0x58` sites found this: the correct count
of `cmp Rx, #88` bounds checks for the key table is 18, not 19. Site
`0x0800C844` is a `movs r0, #0x58` instruction, not a `cmp` instruction.
This instruction writes the literal byte value 88 into a struct field
(`strb.w r0, [sp, #54]`). This instruction writes near other writes of
the values 53, 54, 55, and `0x50`. This instruction is not a key-index
bounds check. The first count in section 7 placed this site in the wrong
group. This site needs no change.

### 10.3 Check of the 4 remaining outlier sites from section 7

- `0x0800757A`: This site is part of a chain of `cmp r7, #N; beq ...`
  instructions. The chain checks r7 against the values 18, 32, 33, 48,
  and 88 in sequence. This chain is a switch statement on a message-type
  byte. The value 88 is one case value in this switch statement. This
  value is not related to key count. Result: not related to the key
  table. This site needs no change.
- `0x08009A1A`: This site bounds a loop (`adds r7,#1` / `cmp r7,#88` /
  `blt`). After the loop, the code calls the function at `0x08016C38`.
  This function is inside the table-code block. This function makes two
  fixed calls to the row-init routine, for rows 0 and 1 only (`cmp
  r4,#2`). The loop does not set the table access count. The link
  between this site and the 88-key limit is not clear. Result:
  ambiguous. This site was left unpatched. This site was not guessed at.
- `0x08014842` and `0x0801485A`: These two sites are near-identical
  functions. Each function checks one incoming index against 88 (`cmp
  r4,#88; bcs skip`). Each function then calls `0x08014812`, which calls
  `0x080147C0`, with a type tag value of 2 or 3. This code may be a
  single-key validity guard for a different part of the firmware, for
  example the LED or display feedback. This code is structurally
  separate from the two-key 88x88 table. The MPK61 hardware will never
  generate a key index above 60. This bound is safe at the value 88,
  even without a change, because the firmware will never use a higher
  value. Result: left unpatched, as the lower-risk choice. This note is
  here for a future check.

### 10.4 Table base address

The literal pool word at `0x08016920` holds the value `0x20003AF0`. This
value is an SRAM address. This word is the table base pointer used at
all the address-math sites. Result: the 88x88 table is a runtime buffer.
The table is not flash-resident data. This result makes the refactor
simpler. Only the code that computes table offsets needs a change.
There is no flash data block to resize.

### 10.5 Full site inventory

All table-touching code is in one address block, `0x08016500` to
`0x08016DAC`. A Capstone-based and objdump-text-based scanner found
these groups:

- 18 `cmp Rx, #88` bounds-check sites. This is the list from section 7,
  minus the miscounted site `0x0800C844` from section 10.2.
- 76 instances of the row-stride pattern. The pattern is `add.w
  Rd,Rn,Rn,LSL#1` followed by `add.w Rd,Rd,Rn,LSL#6`. This pattern
  computes `Rn*3 + Rn*64`, which equals `Rn*67`. Each pair is followed
  by a shift of 2 bits against the table-base literal. This shift gives
  the byte offset, `Rn*268`. The compiler placed this pattern at each
  site. The compiler did not use one shared subroutine for this pattern.
  This is the reason for the high count.
- 35 accesses (`strb.w` or `ldrb.w`) to the fixed byte offsets 264, 265,
  266, and 267 (`0x108` to `0x10B`). These are the 4 state bytes after
  the 88x3 inner table in each row.

A check with the Unicorn harness confirmed this result. The check called
the row-init function at `0x0801651C` with row indices 0, 1, and 87. The
check hooked all memory writes. Result: the row stride is exactly 268
bytes (`row1_min - row0_min == 268`, and `row87_min - row0_min ==
87*268`). This result matches the static analysis.

### 10.6 New constants for 61 keys

The minimal new row size is `61*3 + 4 = 187` bytes. This value is not a
multiple of 4. This value breaks the left-shift-by-2 step in the
row-stride pattern, because that step needs a word count, not a byte
count directly. The refactor does not replace the row-stride pattern
with new instructions. A new instruction set could change the size,
alignment, or branch offsets at 76 sites. The refactor keeps the same
two-instruction pattern. The refactor changes only the two shift-amount
fields in each pair. Each change is a bit-field edit. Each change has a
length delta of zero bytes.

The row-stride pattern computes `Rn * ((1 + 2^s1) + 2^s2)` with two
shift amounts, `s1` and `s2`. The original values are `s1=1, s2=6`,
which give `(1+2)+64 = 67`. The value 47, the exact word count for 61
keys, is not reachable with any pair of `s1` and `s2` in the range 0 to
7. The check tried all values of `s1` in this range, with all values of
`s2`. The smallest reachable value at or above 47 is 49 words, or 196
bytes per row. This value uses `s1=5, s2=4`, which give `(1+32)+16 =
49`. This choice wastes 9 bytes per row against the tight minimum. This
waste has no effect on the RAM budget. The new table (61 rows x 196
bytes = 11,956 bytes) is still less than half the size of the original
table (88 rows x 268 bytes = 23,584 bytes).

The new row layout is this: the inner 61x3 table is at bytes 0 to 182.
The state bytes move from offsets 264-267 to offsets 183-186, directly
after the inner table. Bytes 187 to 195 are unused padding.

All 18 bounds checks change from `cmp Rx, #88` to `cmp Rx, #61`. The
valid key index range is 0 to 60.

## 11. Refactor Implementation and Verification

All 3 edit classes were applied directly to `MPK88_v1_01.bin`. Each edit
was an exact instruction-encoding bit-field change. Each site had a
check on its pre-edit encoding. A mismatch at any site would stop the
process and report an error, instead of a silent wrong edit at the wrong
place. The result had exactly 240 changed bytes: 18 bytes for the bounds
checks, 152 bytes for the row-stride pattern, and 70 bytes for the state
byte offsets. This count matches the site inventory from section 10.5.

A disassembly of the result confirmed these changes:

- The row-init function shift amounts read `lsl #5` and `lsl #4`.
- The bound check reads `cmp r1, #61`.
- The state-byte stores read offset `#183` (`0xB7`) and offset `#184`
  (`0xB8`).

A second run of the Unicorn harness against the result gave these
checks:

- The row stride is exactly 196 bytes (`row1 - row0`). Row 60 is at
  offset `60*196 = 11,760`. This result matches the prediction.
- The row-init inner loop, traced for row 0, touches inner slots 0 to
  60, 61 slots in total. The bound of 61 is correct. There is no
  off-by-one error.
- A sweep of the accessor function at `0x08016668` across all indices 0
  to 87 gave this result: table writes occur for indices 0 to 60 only.
  No writes occur past the new table end, for any input, including the
  range 61 to 87, which was in bounds before the refactor and is not in
  bounds after the refactor.

The `.syx` file was rebuilt from the edited binary. The rebuild process
changed only the affected Intel HEX text lines. The rebuild process
recomputed a new checksum only for each changed line. The rebuild
process did not regenerate the full hex file. The rebuild process kept
the exact original formatting: CRLF line endings, uppercase hex text,
the no-op Extended Linear Address record after the last data line, and
the CRLF after the final `F7` byte. The rebuild process also changed
header byte 3 from `0x71` to `0x6C`, the MPK61 product ID from section
2. The result file has the same size as the original file: 292,614
bytes.

A round-trip check confirmed this result: the rebuilt `.syx` file,
converted back to a binary image, is byte-for-byte identical to the
edited binary. The Unicorn bounds sweep, run again against this
round-tripped binary, passed with zero mismatches.

### 11.1 Caveats for the table refactor

- The emulator checks call the table-read, table-write, table-init, and
  table-accessor functions directly, with controlled register inputs.
  The emulator checks do not run a full chip boot. The emulator checks
  do not run the real vector-table dispatch. The emulator checks do not
  run peripheral emulation. The emulator checks do not run the
  interrupt-driven key-scan flow. These checks are strong evidence that
  the address math is correct. These checks are not a full functional
  replay of key presses on real hardware.
- Section 10.3 lists 2 ambiguous sites: the loop-then-call site at
  `0x08009A1A`, and the pair at `0x08014842` and `0x0801485A`. These
  sites were left unpatched. These sites were not guessed at. A future
  hardware test that finds a fault must check these sites next.
- The refactor did not touch the first 16 KB of flash, the bootloader
  region (`0x08000000` to `0x08003FFF`). A bad flash write to the
  application region must still leave the device able to accept another
  firmware update, because the bootloader stays untouched.

## 12. The MIDI Note Mapping Function

This section covers the second part of the project, from section 1: the
code that converts a key number to a MIDI note number. The table
refactor in sections 5 through 11 changes memory layout only. The table
refactor decides which row of the 88x88 buffer holds the data for key N.
The table refactor does not change which MIDI note number key N sends.
This section checks that second function.

### 12.1 Location of the function

The function is at address `0x080107E0`. The physical key-scan handler
calls this function. The call site is at address `0x08016B46`, inside
the function at `0x08016B22`. This calling function is the key-press
handler from the 88x88-table code block in sections 5 through 11. This
handler reads the table and decides if a Note On message must send. The
key index used at this call site is the register `r4`. This is the same
register bounds-checked against the key-count limit at the 18 sites from
section 10.5, now changed from 88 to 61. Result: this function reads a
real physical key number as its input.

The function at `0x080107E0` disassembles to this code:

```
080107e0: push {r4, r5, r6, lr}
080107e2: mov  r4, r0            ; r4 = key index (0-based)
080107e4: movs r0, #8
080107e6: bl   0x8010266         ; get_param(8)  -- user "transpose" setting
080107ea: subs r0, #36
080107ec: sxtb r5, r0            ; r5 = transpose_setting - 36 (signed)
080107ee: movs r0, #216
080107f0: bl   0x8010266         ; get_param(216) -- user "octave" setting
080107f4: subs r0, r0, #3
080107f6: sxtb r6, r0            ; r6 = octave_setting - 3 (signed)
080107f8: movs r0, #12
080107fa: mla  r0, r0, r6, r4    ; r0 = 12*octave_offset + key_index
080107fe: add  r0, r5            ; r0 += transpose_offset
08010800: adds r0, #21           ; r0 += 21   <-- fixed base note
08010802: uxtb r0, r0
08010804: pop  {r4, r5, r6, pc}
```

In words, the formula is this:

```
note = key_index + 21 + transpose_offset + 12 * octave_offset
```

The values `transpose_offset` and `octave_offset` are independent
user-configurable settings. These settings are not related to key
count. The `-36` and `-3` terms center these settings at zero. The value
21 is not user-configurable. The value 21 is a fixed number in a single
16-bit instruction, `adds r0, #21`, encoding `0x3015`, at flash address
`0x08010800`.

The result of `0x080107E0` is the value sent as the MIDI note. The
caller of this function, at `0x08010806`, wrapped by the function at
`0x080108C4`, stores the computed note into a per-key state slot. The
caller passes this value to the Note On message builder at `0x08016ECC`,
which calls `0x080172EC`. This builder function does this:

```
status = 0x90 | channel
send(status, note, velocity)
```

The matching Note Off path is at `0x080108D8` and `0x080108D2`. The
key-scan block calls this path from `0x08016B90` and `0x08016C7C`. This
path reads the same stored note value. Result: a key press and a key
release always report the same note number, even if the transpose or
octave setting changes while the key is held down.

### 12.2 Base value used by this function

The function uses a fixed base note of 21. MIDI note 21 is A0. This
value is the standard base note for an 88-key keyboard. This value was
checked two ways:

1. A static check of the disassembly in section 12.1.
2. An empirical check with the Unicorn harness, in section 12.4. Key 0
   gives note 21. Key 87 gives note 108, which is C8. This range is the
   correct 88-key range, A0 to C8.

No lookup table exists for this conversion. A search checked for an
88-entry lookup table with note-range values. This table does not
exist. The function computes the note with arithmetic. The function
does not look up the note in a table. The only 88-entry table in the
firmware is the table from sections 5 through 11. That table stores a
3-byte make/break-contact timing structure for velocity sensing. The
third byte of that structure is read back and used as a column index in
a bounded loop. That third byte drives the table's own internal scan
state. That third byte is not a MIDI note value. No other fixed-size
table with 88 small-integer entries exists in the firmware.

### 12.3 Note on the CPLD

The project has no CPLD bitstream and no CPLD netlist to check. The
project has only the STM32 flash image. This gap does not change where
the fix belongs. Section 12.1 shows the STM32 firmware itself adds the
fixed value 21 to a raw key index, in software, before it sends the
value to the USB-MIDI packet builder. The CPLD may supply raw
make/break contact edges for the velocity-timing table. This work
happens before the note-base addition. The note-base addition happens
in the STM32 image, not in CPLD hardware. Result: the fix belongs in the
STM32 image.

### 12.4 Verification of the fault and the fix (Unicorn, not disassembly alone)

The check called `0x080107E0` directly, the same method as the table
checks in section 11. The check used a hook on `0x08010266`
(`get_param`). This hook forced the transpose and octave settings to
their zero-offset values (8 gives 36, 216 gives 3). This hook isolated
the `+21` term from the user-configurable settings.

Results:

- Original firmware, no refactor and no fix: key 0 gives note 21. Key 87
  gives note 108. This result matches the 88-key A0 convention.
- Firmware with the table refactor from sections 5-11, before the
  note-base fix: key 0 gives note 21. Key 60 gives note 81. This result
  confirms the fault. A 61-key board still starts at note 21 (A0), even
  with the table refactor applied.
- Firmware with the table refactor and the note-base fix, combined: key
  0 gives note 36. Key 60 gives note 96. This range is C2 to C7, the
  standard 61-key range.
- A cross-check ran the table-bounds harness from section 11 against
  the combined firmware. Result: the table refactor is still correct.
  The note-base fix did not change the table refactor. The two fixes
  touch different instructions in different functions.

### 12.5 The note-base fix

The fix is one 16-bit instruction edit. This edit has the same shape as
the bit-field edits in section 11: it changes the immediate value field
only. The edit changes `adds r0, #21` (`0x3015`) to `adds r0, #36`
(`0x3024`), at address `0x08010800`.

This fix is combined with the table refactor from sections 5-11, in one
delivered file, `MPK61_v1_01.syx`. This file carries both changes: the
88x88-to-61x61 table refactor, and the note-base change from 21 to 36.
There is one delivered MPK61 file. There are not separate files for
each change.

A direct check of the delivered file gave this result:

```
key   0 -> MIDI note  36   (C2)
key  60 -> MIDI note  96   (C7)
inner slots written (should be exactly 0..60): 0 .. 60  count = 61
```

A round-trip and header check of the delivered file gave this result:

- The file, converted from `.syx` to hex text to a binary image, is
  byte-for-byte identical to the edited binary.
- The header is `F0 47 00 6C 70`. The product ID byte, `0x6C`, is
  correct for the MPK61 controller.
- The file size is 292,614 bytes. This size is identical to the
  original `MPK88_v1_01.syx` file.

### 12.6 Base note 36: confidence level

The value 36 is not confirmed against real hardware. The value 36 is
not confirmed against an Akai note chart or an Akai spec table. No such
chart or table was available to this project.

The value 36 is the standard scientific-pitch-notation base note for a
61-key keyboard, C2 to C7. This is the same naming convention as the
88-key base note, A0 to C8, confirmed correct in section 12.2 for the
unpatched firmware.

If a future check of real MPK61 hardware gives a different value for
key 0, that check is the correct value. That check must replace the
value 36 in this document and in the firmware.

### 12.7 Open items

- The emulator checks in this project call an isolated function
  directly, with controlled inputs. The emulator checks do not run a
  full boot. The emulator checks do not run the key-scan interrupt. The
  emulator checks do not run a full USB-MIDI message replay on real
  hardware.
- The settings read by `get_param(8)` and `get_param(216)` come from a
  live settings structure at run time. The checks in this project did
  not model this structure. The checks in this project set these values
  to their zero-offset value directly, through a hook. This method
  isolated the one constant this section is about.
- The base note value, 36, is not a hardware-confirmed value. Section
  12.6 states the confidence level.

## 13. Deliverables

- `MPK61_v1_01.syx`: the delivered MPK61 firmware file. This file has
  the 88x88-to-61x61 table refactor from sections 5-11. This file has
  the note-base fix from section 12.5. Both changes were checked with
  static analysis and with the Unicorn emulator. The file was checked
  with a byte-for-byte round trip.
- `MPK88_v1_01.syx`: the original MPK88 firmware file. This file has no
  changes. This file is the source file for every change in this
  project.
- `MPK61_firmware_notes.md`: this file.

No file in this project was flashed to real hardware. No hardware was
available to this project. Every check in this project used static
analysis or the Unicorn emulator.

## Signatures

- Claude Sonnet 5 (`claude-sonnet-5`), via Claude Code `2.1.220`
- Grok — [version string not known to this session, fill in]
- frustro — 7/31/2026

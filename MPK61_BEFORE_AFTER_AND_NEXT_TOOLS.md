# MPK61 Firmware — Before/After and What Comes Next

## 1. Before/after: the STM32 code itself

| | Before this pass | After this pass |
|---|---|---|
| Functions identified at all | ~30 (found by hypothesis-driven jumping) | **806** (complete recursive-descent + jump-table + gap closure) |
| Functions with a real semantic label | ~30, and 2 of those were actually wrong (mislabeled) until caught tonight | **205** (59 direct evidence, 146 propagated), both known bugs fixed |
| Byte-level accounting of the 104,004-byte blob | Unknown — no one had ever classified what fraction was code vs. data | **100%** — every byte is either inside a labeled function, a confirmed literal-pool constant, the vector table, the USB descriptor block, or verified compiler padding |
| Switch statements (`tbb`/`tbh`) | 0 resolved — every one was a dead end in every prior trace | **21 resolved**, 394 real case targets |
| `get_param`/`set_param` call sites | A handful found by manual grep, several missed (e.g. the actual param-21 write site's full caller list was never enumerated) | **513 enumerated** (201 sets, 312 gets), every param-21 write site found (there is exactly one, and it's parameterized) |
| Embedded strings | Not searched at all outside the one already-known USB block | **1124 extracted**, including LCD menu labels, fault-handler names, transport labels, velocity-curve names, and a 17-entry preset table |
| Known bugs in the analysis process itself | Not tracked — errors just sat in whatever document referenced them | 2 real self-introduced labeling bugs found and fixed before being reported (a mislabeled bulk-initializer that had propagated to 28 functions, and a blanket pool assignment that mixed UI-menu code into the note pipeline) |

The honest ceiling of this pass: **structural completeness is real** (every function's existence and boundaries are known, every branch is tracked). **Semantic completeness is 25%**, not 100% — 601 functions exist and their size/callees/branches are known, but nobody has read what they individually *do*. That's a fundamentally different, much slower task (see §3).

## 2. Before/after: understanding of the system as a whole

**Before tonight**, the working picture was: STM32 runs the note-generation logic, a Lattice MachXO CPLD scans the physical key matrix and sends raw codes over a UART link, and somewhere in that chain a bug (or a genuine protocol mismatch, or a hardware fault) causes `Note:000/Data:000`. The CC-mapping question was an unresolved argument between your direct LCD observation and a Reason DAW codec file, with no way to adjudicate between them.

**After tonight**, several previously-separate pieces connect into one coherent picture:

- **The full note-event pipeline is now traced start to finish and proven correct in isolation** (Unicorn-verified): UART ISR → ring buffer → byte consumer → `key_velocity_event_assembler` (which reads 2 raw bytes: masked key + a *real* 5-curve velocity lookup, not the no-op it was assumed to be) → gate checks → dispatcher → note-mapping function. None of it was touched by the 88→61 refactor.
- **The velocity curve table is real and named**, not a guess: `LINEAR`/`LOG 1`/`LOG 2`/`EXP 1`/`EXP 2`, confirmed both by direct table decode and by independently-found LCD label strings.
- **A previously-unknown fault-handler family exists** (HardFault/BusFault/UsageFault/MemFault-style), confirmed by both code structure and embedded name strings — evidence the firmware has real diagnostic infrastructure that's never been exercised or read out.
- **The CC-mapping dispute has a plausible resolution that wasn't available before**: different named presets (`LiveLite`, `Reason`, `Cubase`, ..., `Generic`) each carry their own 1030-byte control-mapping block, and at least one preset (`LiveLite`) uses the "same CC across banks" shape (matching the Reason codec) while `Generic` (what you actually tested with) looks structurally different (closer to your directly-observed values). This reframes the dispute from "one source is wrong" to "these may be two different presets' real data" — not proven end-to-end, but a materially better-supported hypothesis than either side had alone.
- **The remaining unknown has gotten narrower, not vaguer**: it's no longer "something in this huge undocumented codebase is wrong somewhere," it's specifically "what does the CPLD actually put on the wire," because everything on the STM32 side of that wire is now either confirmed correct or confirmed unchanged from stock MPK88 firmware.

## 3. Can other tools add more insight from here?

**Yes, and the two that would matter most are different in kind, not degree:**

- **A real decompiler (Ghidra, or IDA with the Hex-Rays decompiler)** would directly speed up §1's semantic-labeling gap. What I've been doing — reading raw Thumb-2 disassembly by hand, cross-referencing peripheral addresses and param IDs by script — is a manual approximation of what Ghidra's auto-analysis, cross-reference database, and pseudo-C decompilation do natively and persistently. Feeding this firmware (with the vector table, function boundaries, and 205 labels already found tonight as a head start) into Ghidra would likely let a human or another pass work through the remaining 601 unknown functions much faster than continuing with objdump + capstone scripts. This is a real, concrete recommendation, not a vague "more tools would help."
- **Live hardware debug access — an SWD/JTAG probe (e.g. an ST-Link) wired to the STM32, running OpenOCD + GDB against the real chip** — is categorically more powerful than any further static analysis for the one question that actually matters most right now (see §4). Static analysis can only tell you what the code *would* do with given inputs; it cannot tell you what the CPLD *actually sends*. A debugger attached to the real, running chip can.
- The **logic analyzer / scope you already have** is the lower-effort version of the same idea — it answers the electrical-signal-level version of "what does the CPLD send," without needing to attach to the STM32's debug port at all.

## 4. Where more static iteration helps vs. where it's actually exhausted

Not all "more iteration" is equally valuable — being specific about which kind:

- **More rounds of the exact method used tonight (peripheral/param-evidence + call-graph propagation) are exhausted.** It already ran to the stated stopping point — 4 consecutive iterations, zero new labels. Running a 5th, 6th, 10th identical pass would produce nothing more; the method has extracted everything it structurally can.
- **A genuinely new static evidence source (like tonight's string scan) still has real headroom.** Two concrete candidates not yet done: (a) systematically decode the *other 16* preset blocks the same way `Generic` was decoded, to build a complete per-preset CC table instead of one partial one; (b) trace the giant 906-branch menu-navigation function (`0x8009b46`) properly — deliberately not done tonight because the specific hypothesis it related to was already disproven on real hardware, but it's still 2,904 instructions of completely unlabeled UI logic. Both are bounded, well-defined next passes, not open-ended.
- **Beyond those two, static analysis alone hits a hard ceiling** for the actual open question (why the keybed fails). No amount of further disassembly can show what bytes the CPLD transmits — that data doesn't exist anywhere in the STM32 binary, because the CPLD is separate hardware running its own separate, unavailable firmware.

## 5. Direct answer: static iteration vs. hitting a real breakpoint

If the goal is specifically "settle whether the CPLD sends real data," then **one real GDB session against the physical hardware would outperform any number of further static passes** — not a marginal improvement, a categorical one. Concretely: attach a debug probe, set a hardware breakpoint at `key_velocity_event_assembler` (`0x08011222`, now precisely located and understood from tonight's work), press a real key, and read `r5` (the raw byte just received) directly off the chip. That single breakpoint hit answers, with total certainty, the question three separate static-analysis threads tonight could only circle: does the CPLD send anything real, and if so, what.

So: **4 more iterations of static analysis would not be needed if real hardware debug access is available** — a single instrumented key-press under GDB (or, more simply, a logic-analyzer capture on the UART line during a key-press, which needs no debug-port access at all) replaces what could otherwise be many more hours of inference from the binary alone. Static analysis has done what it can do for the keybed question specifically; the next real step for *that* specific problem is instrumented hardware, not more disassembly. The still-open static threads (§4) are worth doing for overall system understanding, but they're not going to be the thing that finds the keybed bug.

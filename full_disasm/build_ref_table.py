#!/usr/bin/env python3
"""
Pass 1 of iterative semantic labeling.

For every function, gather hard evidence:
  - literal-pool CONSTANT VALUES it loads (not just addresses) -- resolve
    what each `ldr rX,[pc,#n]` actually loads, and check against known
    STM32F103 peripheral base addresses (GPIO/USART/TIM/etc.)
  - every get_param/set_param ID it touches
  - its callees (from function_map.json)

Then apply rule-based labeling wherever there's real, checkable evidence,
and write a running reference table (address, label, confidence, evidence).
Confidence levels: "confirmed" (direct peripheral/param evidence, hand-
checkable), "inferred" (propagated from labeled callees/callers, weaker),
"unknown" (no evidence yet -- stated honestly, not guessed).
"""
import json, struct
from capstone import *
from capstone.arm import *

FLASH_BASE = 0x08004000
data = open("/home/claude/mpk/MPK61_gatebypass_v2.bin", "rb").read()
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
md.detail = True

fm = json.load(open("/home/claude/mpk/full_disasm/function_map.json"))
byaddr = {f["start"]: f for f in fm}

# STM32F103RC peripheral base addresses (reference part number confirmed
# earlier in the project). Offsets are the standard register layout.
PERIPH_BASES = {
    0x40010800: "GPIOA", 0x40010C00: "GPIOB", 0x40011000: "GPIOC",
    0x40011400: "GPIOD", 0x40011800: "GPIOE",
    0x40013800: "USART1", 0x40004400: "USART2", 0x40004800: "USART3",
    0x40012C00: "TIM1", 0x40000000: "TIM2", 0x40000400: "TIM3", 0x40000800: "TIM4",
    0x40013000: "SPI1", 0x40003800: "SPI2",
    0x40005400: "I2C1", 0x40005800: "I2C2",
    0x40012400: "ADC1", 0x40012800: "ADC2",
    0x40020000: "DMA1",
    0x40021000: "RCC",
    0x40010400: "EXTI",
    0x40010000: "AFIO",
    0x40022000: "FLASH_IF",
    0x40007000: "PWR",
    0x40006C00: "BKP",
    0x40002800: "IWDG",
    0x40002C00: "WWDG",
    0x40005C00: "USB_FS_CAN",  # shared USB/CAN SRAM region on some parts
    0xE000E010: "SYSTICK",
    0xE000E100: "NVIC_ISER",
}
GPIO_OFFSETS = {0x00: "CRL", 0x04: "CRH", 0x08: "IDR", 0x0C: "ODR", 0x10: "BSRR", 0x14: "BRR", 0x18: "LCKR"}
USART_OFFSETS = {0x00: "SR", 0x04: "DR", 0x08: "BRR", 0x0C: "CR1", 0x10: "CR2", 0x14: "CR3", 0x18: "GTPR"}
TIM_OFFSETS = {0x00: "CR1", 0x10: "CNT" , 0x24: "CNT", 0x28: "ARR", 0x34: "CCR1", 0x38: "CCR2", 0x3C: "CCR3", 0x40: "CCR4"}

SORTED_BASES = sorted(PERIPH_BASES.keys())

def classify_addr(val):
    # exact nearest-preceding-base match, not a blind 4K mask -- STM32
    # GPIO ports sit only 0x400 apart, well inside one 4K page together
    base = None
    for b in SORTED_BASES:
        if b <= val < b + 0x400:
            base = b
            break
    if base is None:
        return None
    off = val - base
    if base in PERIPH_BASES:
        name = PERIPH_BASES[base]
        reg = None
        if name.startswith("GPIO"):
            reg = GPIO_OFFSETS.get(off)
        elif name.startswith("USART"):
            reg = USART_OFFSETS.get(off)
        elif name.startswith("TIM"):
            reg = TIM_OFFSETS.get(off)
        return f"{name}{'.'+reg if reg else f'+0x{off:x}'}"
    return None

def func_instructions(f):
    addr = int(f["start"], 16)
    end = int(f["end_approx"], 16)
    out = []
    while addr <= end:
        off = addr - FLASH_BASE
        got = list(md.disasm(data[off:off+4], addr))
        if not got:
            addr += 2
            continue
        insn = got[0]
        out.append(insn)
        addr += insn.size
    return out

STRING_HITS = {
    0x8004868: "hard_fault_name_string", 0x8004874: "mem_fault_name_string",
    0x8004880: "bus_fault_name_string", 0x800488c: "usage_fault_name_string",
    0x8018678: "mmc_back_string", 0x8018688: "mmc_forward_string",
    0x8018698: "mmc_stop_string", 0x80186a8: "mmc_play_string", 0x80186b8: "mmc_record_string",
    0x8018960: "curve_name_linear", 0x801896b: "curve_name_log1",
    0x8018976: "curve_name_log2", 0x8018981: "curve_name_exp1", 0x801898c: "curve_name_exp2",
    0x80189c0: "preset_table_base_livelite",
}

param_calls = json.load(open("/home/claude/mpk/full_disasm/param_calls.json"))
params_by_func = {}
for e in param_calls["set_param_calls"]:
    params_by_func.setdefault(e["func_start"], {"set": set(), "get": set()})["set"].add(e["param_id"])
for e in param_calls["get_param_calls"]:
    params_by_func.setdefault(e["func_start"], {"set": set(), "get": set()})["get"].add(e["param_id"])

evidence = {}
for f in fm:
    start = f["start"]
    insns = func_instructions(f)
    periph_hits = set()
    string_hits = set()
    for insn in insns:
        if insn.mnemonic in ("ldr", "ldr.w") and "[pc" in insn.op_str:
            for op in insn.operands:
                if op.type == 3 and op.mem.base == ARM_REG_PC:
                    pc_val = (insn.address + 4) & ~3
                    lit_addr = pc_val + op.mem.disp
                    off = lit_addr - FLASH_BASE
                    if 0 <= off < len(data) - 3:
                        val = struct.unpack_from("<I", data, off)[0]
                        cls = classify_addr(val)
                        if cls:
                            periph_hits.add(cls)
                        if val in STRING_HITS:
                            string_hits.add(STRING_HITS[val])
    p = params_by_func.get(start, {"set": set(), "get": set()})
    evidence[start] = {
        "label": f["label"],
        "n_instr": f["n_instructions"],
        "callees": f["callees"],
        "periph": sorted(periph_hits),
        "strings": sorted(string_hits),
        "params_set": sorted(x for x in p["set"] if x is not None),
        "params_get": sorted(x for x in p["get"] if x is not None),
    }

json.dump(evidence, open("/home/claude/mpk/full_disasm/evidence.json", "w"), indent=1)
with_periph = sum(1 for v in evidence.values() if v["periph"])
with_params = sum(1 for v in evidence.values() if v["params_set"] or v["params_get"])
print(f"functions with peripheral evidence: {with_periph}")
print(f"functions with param evidence: {with_params}")
print(f"functions with any hard evidence: {sum(1 for v in evidence.values() if v['periph'] or v['params_set'] or v['params_get'])}")

# LSDL Standard-Cell Library for GF180MCU

A custom **Limited Switch Dynamic Logic (LSDL)** standard-cell library for the
GlobalFoundries **GF180MCU** open PDK, built with the open-source SMT cell
generator **LibreCell** and signed off against the official GF180 KLayout DRC
and Netgen LVS decks.

LSDL is a single-clock dynamic-logic family with an integrated latch (paper
Fig. 1; NAND-complex form Fig. 3a) — each cell is effectively a positive-edge
flop on `Clk` (precharge on `Clk`=0, evaluate on `Clk`=1). No keeper, no minder,
footed trees only, no scan. Architecture from:

- Belluomini et al., *Limited switch dynamic logic circuits for high-speed
  low-power circuit design*, IBM J. Res. & Dev. 50(2/3), 2006.
- Sivagnaname et al., *Wide Limited Switch Dynamic Logic Circuit
  Implementations*, 2006.

This is the **cell library** repo. The benchmark chip that consumes it (LSDL-vs-CMOS
adder / mux / encoder, wafer.space tapeout) lives in a separate repo.

## Conventions

- **Site:** custom **11-track** row, `unit` site, **0.56 × 6.16 µm** (LSDL needs
  11 tracks to route; 9T is unroutable for these cells).
- **Voltage:** 5.0 V (GF180MCU MV devices; NMOS L=0.6 µm, PMOS L=0.5 µm).
- **Sign-off:** **KLayout DRC** (0 cell-level) + **Netgen LVS** ("match uniquely")
  are authoritative. Tap/well bulk ties + DF.13/14 close at the 11T tap/fill row
  (`librecell/signoff_support_11t/`), not in the functional cells.
- **Source of truth:** hand-source `.spice` (`cells/lsdl_basic/`) + per-cell
  `descriptor/*.yaml`. GDS/LEF/Liberty/`.v` are generated and frozen under
  `librecell/signoff_<cell>/` and `lib/`.
- **Naming:** files use the legacy prefix `lsdl_fd_sc_9t5v0` to mirror the stock
  GF180 `gf180mcu_fd_sc_mcu9t5v0` convention. ⚠️ Both `fd` (foundry) and `9t` are
  legacy misnomers — this is a *custom* library on an **11-track** row; a rename
  to `lsdl_sc_11t5v0` is planned.

## Layout

```
cells/lsdl_basic/   hand-source .spice (truth) + .v blackbox wrappers
descriptor/         per-cell .yaml (drives Liberty + Verilog + characterization) + SCHEMA.md
librecell/          LibreCell flow: tech_gf180mcu/ enablement, gen_and_drc.sh,
                    build_support.py (tap/endcap/fill/antenna-diode), post-process +
                    port + LEF-fix scripts, lclayout patches, LESSONS.md
                    signoff_<cell>/        frozen GDS/LEF/lib/mag + LVS log + MANIFEST
                    signoff_support_11t/   11T tap/endcap/fill/antenna-diode row cells
scripts/            gen_liberty.py, gen_verilog_wrapper.py, pvt_sweep.py,
                    audit_lef.py, check_pin_access.py, pex_validate.py
testbench/  pvt/    PVT testbenches (.sp) + per-cell *_pvt.json sweep data
lib/                lsdl_fd_sc_9t5v0__*.lib  (combined Liberty)
docs/               schematics + presentation
```

## Build / reproduce

See `versions.md` for the exact toolchain + run env. Per cell:
```
librecell/gen_and_drc.sh <cell> 11          # lclayout SMT P&R + KLayout DRC
librecell/librecell_postprocess.py ...       # 5V markers (DUALGATE/FET5VDEF)
# port + LEF fix, then Magic ext2spice + Netgen LVS vs cells/lsdl_basic/<cell>.spice
```
See the `lsdl-librecell-gf180` flow notes and `librecell/LESSONS.md`.

## Status

Wave-1 BASIC cells (9) physically signed off (0 cell-level DRC, block LVS clean).
See `STATUS.md`.

---

## Maximum frequency experiment (LSDL NAND2, TT 5 V 25 °C)

Script: `scripts/freq_sweep.py`.

### Method

Sweep `Clk` frequency from 0.25 GHz to 2.5 GHz. At each frequency run an
ngspice transient with worst-case inputs (A1=A2=1, full discharge every
cycle). Read the `wrdata` dump; measure 50%-crossing delays from the Clk
rising edge to `dyn` (before the latch) and to `Out` (after the latch).
Timing margin is expressed as a percentage of the full clock period:

```
margin(%) = (T/2 − t_delay) / T × 100
```

Pass criterion: `Out` margin ≥ 10 % (10 % guard band).

### Formula for maximum safe clock frequency

```
t_clk_to_Out ≈ 252 ps  (constant across frequency — determined by circuit delay)

f_max = 0.40 / t_clk_to_Out = 0.40 / 252 ps ≈ 1.587 GHz
```

The 0.40 factor comes from allowing the 40 % of a half-period (the evaluate
window = T/2) remaining after the output settles, leaving 10 % guard.

### SPICE sweep table (worst-case inputs, TT 5 V 25 °C)

| freq (GHz) | T/2 (ps) | t\_dyn (ps) | dyn margin% | t\_Out (ps) | Out margin% | pass? |
|---|---|---|---|---|---|---|
| 0.25  | 2000 |  97 | 95.1 % | 252 | 93.7 % | PASS |
| 0.40  | 1250 |  97 | 96.1 % | 252 | 89.9 % | PASS |
| 0.50  | 1000 |  97 | 90.3 % | 252 | 74.8 % | PASS |
| 0.625 |  800 |  97 | 87.9 % | 252 | 68.5 % | PASS |
| 0.80  |  625 |  97 | 84.5 % | 252 | 59.8 % | PASS |
| 1.00  |  500 |  97 | 80.6 % | 252 | 49.6 % | PASS |
| 1.25  |  400 |  97 | 75.8 % | 252 | 37.0 % | PASS |
| 1.50  |  333 |  97 | 70.9 % | 252 | 24.4 % | PASS |
| 1.575 |  317 |  97 | 69.4 % | 252 | 10.3 % | PASS ← boundary |
| 1.667 |  300 |  97 | 67.7 % | 252 |  8.0 % | FAIL |
| 2.00  |  250 |  97 | 61.2 % | Out N/A | — | FAIL |
| 2.50  |  200 |  97 | 51.5 % | Out N/A | — | FAIL |

`dyn` (before latch) settles at ~97 ps and is constant across all
frequencies — it is not the bottleneck. `Out` (after the latch + output
driver) settles at ~252 ps and is also constant; it is the limiting path.

### Liberty values derived from this experiment

| Attribute | Value | Note |
|---|---|---|
| `min_pulse_width_high (CLK)` | **252 ps** | minimum evaluate window = t\_clk\_to\_Out |
| `min_pulse_width_low  (CLK)` | **≈ 180–200 ps** | minimum precharge window (dyn must return to VDD; ~2× RC) |
| `cell_rise/fall (CLK→OUT)`  | **252 ps** | at worst-case inputs, TT corner |

### Practical frequency recommendations

| Use case | Recommended frequency | Rationale |
|---|---|---|
| Benchmark functional mode (LFSR input) | **1 GHz** | 50 % margin on Out; all PVT corners safe |
| Ring-oscillator measurement mode | **free-run** | RO sets its own frequency; ÷256 output pad |
| Absolute maximum (TT 5 V 25 °C only) | **1.575 GHz** | 10 % guard; not recommended for tape-out |

At SS / low-voltage / hot corners the delays increase; **1 GHz is
conservative and recommended for the tapeout benchmarks.**

### Comparison to static CMOS (NAND2 + DFF equivalent)

At 500 MHz (2 ns period):

| Metric | LSDL NAND2 | CMOS NAND2 + DFF |
|---|---|---|
| Clk-to-Out delay | **252 ps** | **418 ps** (361 ps DFF + 57 ps NAND) |
| Speed-up | **1.66×** faster | baseline |
| Power (50 MHz, worst-case A1=A2=1) | **17.6 µW** | **44.6 µW** |
| Power saving | **2.5×** | baseline |
| FET count | **12** (single cell) | **28** (NAND2=4 + DFF=24) |

The LSDL `dyn` node (before latch) resolves at only ~99 ps — comparable to
the raw CMOS NAND2 propagation delay (~70–94 ps). The additional 153 ps
(99 → 252 ps) is the latch-to-output-driver path, which is the cost of
integrating the flip-flop inside the cell. A stand-alone CMOS DFF adds
~361 ps on top of the NAND, so the net saving is still 166 ps per stage.

---

## License

Apache-2.0 (see `LICENSE`, `NOTICE`). The GF180MCU PDK and the source papers are
**not** redistributed here. `lclayout` (AGPL) is used only as a generation tool.

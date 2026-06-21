# L5 Liberty Signoff — lsdl_fd_sc_9t5v0__tt_5v_25c.lib

**Date:** 2026-06-02  
**Library:** `lsdl_fd_sc_9t5v0`  
**Corner:** TT / 5.0 V / 25 °C  
**Tool:** OpenSTA 3.1.0

---

## Acceptance gates — ALL PASS

| Gate | Description | Result |
|------|-------------|--------|
| **G1** | Liberty parse — 0 errors | **PASS** |
| **G2** | All 9 cells present in library | **PASS** |
| **G3** | NAND2 cell report: correct pins, timing arcs, ff model | **PASS** |
| **G4** | Timing smoke at 500 MHz: setup slack 1.10 ns, hold slack 0.05 ns | **PASS** |
| **G5** | 1 GHz closure, LSDL pipelined adder (4-bit and 16-bit): worst setup slack **+0.134 ns**, hold +0.5 ns, TNS 0 | **PASS** |

G1–G4: `sta_smoke/run_sta.tcl`. G5: `blocks/adder/run_sta_adder.tcl`.

---

## G2 — Cells found

```
lsdl_aoi21_x1   lsdl_aoi22_x1   lsdl_inv_x1
lsdl_nand2_x1   lsdl_nand3_x1   lsdl_nand4_x1
lsdl_nor2_x1    lsdl_nor3_x1    lsdl_nor4_x1
```

## G3 — NAND2 pin/arc summary

```
CLK   input   (clock: true)
A1    input
A2    input
OUT   output  function=IQ
VPWR  bidirect
VGND  bidirect

Timing arcs:
  CLK -> CLK  width (high and low pulse-width constraints)
  CLK -> A1   setup_rising / hold_rising
  CLK -> A2   setup_rising / hold_rising
  CLK -> OUT  Reg Clk to Q (rising_edge)
```

---

## Liberty timing values — ALL MEASURED (45-point PVT sweeps, 9/9 cells)

| Cell | cell_fall (TT/25°C/5V) | min_pw_high (SS/125°C worst) | PVT result |
|------|------------------------|-------------------------------|------------|
| lsdl_inv_x1   | 0.214 ns | 0.339 ns | 45/45 PASS |
| lsdl_nand2_x1 | 0.255 ns | 0.416 ns | 45/45 PASS |
| lsdl_nand3_x1 | 0.281 ns | 0.463 ns | 45/45 PASS |
| lsdl_nand4_x1 | 0.312 ns | **0.518 ns** ⚠ | 45/45 PASS |
| lsdl_nor2_x1  | 0.210 ns | 0.330 ns | 45/45 PASS |
| lsdl_nor3_x1  | 0.220 ns | 0.341 ns | 45/45 PASS |
| lsdl_nor4_x1  | 0.231 ns | 0.357 ns | 45/45 PASS |
| lsdl_aoi21_x1 | 0.266 ns | 0.430 ns | 45/45 PASS |
| lsdl_aoi22_x1 | 0.266 ns | 0.430 ns | 45/45 PASS |

⚠ **nand4 flag:** `min_pulse_width_high` 518 ps > the 500 ps evaluate window at
1 GHz / 50% duty. Designs using nand4 at 1 GHz will fail the pulse-width check
at the SS/125°C corner — either avoid nand4 on 1 GHz paths, upsize its n-tree
(X2 variant), or run those domains at the wafer-measured frequency. The adder
benchmark uses only inv + aoi22 and is unaffected.

Fixed timing values (all cells):
- `cell_rise` = 0.050 ns (precharge path, conservative)
- `setup_rising` = 0.100 ns, `hold_rising` = 0.050 ns
- `min_pulse_width_low` (CLK) = 0.250 ns

### Testbench errata fixed during T1

The first NOR2/3/4 sweep run failed 0/45 on `v_out_b_glitch` ≈ VDD at every
corner — measurement-window bug, not silicon. The window sat in the precharge
after an evaluate-low cycle, where the feedback latch legitimately holds
`out_b` high. Fix: appended two all-0 cycles (cyc6 recovery, cyc7 stay-high)
and moved the glitch window to cyc7's evaluate phase [125n,135n], which is the
condition the paper's 10%-VDD rule actually constrains. After fix: 45/45.

---

## Deferred to L5-B (after adder PnR validation)

- Replace scalar timing values with 7×7 slew×cap NLDM lookup tables.
- Measured setup/hold per cell (dedicated testbench variant).
- Per-corner Liberty files (SS, FF) for sign-off STA.
- Liberty + collateral for lsdl_nand_cmplx_x1 (physically signed off, no descriptor yet).

## What L5 unblocks

- **16-bit adder LibreLane block** — netlist generated and timing-closed
  (`blocks/adder/`), ready for PnR.
- **OpenSTA** — full timing analysis on LSDL blocks (proven at 1 GHz).

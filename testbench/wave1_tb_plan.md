# Wave 1 per-cell testbench descriptor plan

What each Wave 1 cell's testbench needs, to fill `TEMPLATE_lsdl_cell.sp`. NOT yet
fully authored — this is the spec; author each tb when its cell reaches the PEX gate.

Shared (all cells): 20 ns clock (precharge low first half), inputs switch mid-precharge,
`Cload Out 0 5f`, probes `dyn`/`out_b`/`Out`, pass gates: glitch on out_b < 0.5 V,
charge-share dyn floor > 3.5 V, eval delay < 2 ns, functional final value correct.

`function` column assumes the **basic LSDL cell is inverting** (Out = !(n-tree
pulldown)), pending the polarity decision (see NOTE). Probe-node list excludes
metal-less diffusion stack-mid nodes (e.g. `nint`) — not layout-probeable; their
parasitic folds into `dyn`.

| Cell | n-tree (pulldown) | function (if inverting) | inputs | worst charge-share vector | probe nodes |
|---|---|---|---|---|---|
| AND2/NAND2 | A1·A2 series | !(A1·A2) | A1,A2 | A1=1,A2=0 after A1A2=11 drove stack-mid low | dyn,out_b |
| AND3 | A1·A2·A3 series | !(A1·A2·A3) | A1..A3 | top on, lower off, after full-eval | dyn,out_b |
| AND4 | A1·A2·A3·A4 series | !(·) | A1..A4 | top on, deepest off, after full-eval | dyn,out_b |
| OR2 | A1+A2 parallel | !(A1+A2) | A1,A2 | single input pulses (no stack node) | dyn,out_b |
| OR3 | A1+A2+A3 parallel | !(·) | A1..A3 | one input on | dyn,out_b |
| OR4 | A1+A2+A3+A4 parallel | !(·) | A1..A4 | one input on | dyn,out_b |
| AOI21 | (A1·A2)+B | !((A1·A2)+B) | A1,A2,B | A1=1,A2=0 share on the A-arm stack node | dyn,out_b |
| AOI22 | (A1·A2)+(B1·B2) | !(·) | A1,A2,B1,B2 | each arm partial-eval (2 stress cycles) | dyn,out_b |
| NAND_CMPLX_X1 | tree1=A, tree2=B (two dyn) | NAND(dyn1,dyn2) | A,B | each tree partial | dyn1,dyn2,out_b |
| NAND_CMPLX_AOI | tree1=A1·A2, tree2=B1·B2 | NAND(dyn1,dyn2) | A1,A2,B1,B2 | each arm/tree partial | dyn1,dyn2,out_b |

## Stimulus authoring rules
- **Series (AND-family):** worst charge-share = top device ON, a lower device OFF,
  in the cycle *after* a full-eval drove the stack-internal node low (the nand2 cyc3
  pattern). Generalize: for an n-stack, stress each "top-k on, k+1 off" boundary;
  one representative (top on, bottom off) is the minimum gate.
- **Parallel (OR-family):** no internal stack node → charge-share is mild; the gate
  is mainly glitch + full-eval delay + each-input-alone discharge.
- **AOI:** treat each series arm like an AND stack; stress arms independently.
- **NAND_CMPLX:** two dynamic nodes; the tb must drive both trees and probe dyn1/dyn2.
  Out = NAND(dyn1,dyn2) — extra recovery cycles to exercise all (dyn1,dyn2) combos.
- `tpd` meas RISE/FALL index depends on the cycle where Out toggles for that vector.

## RESOLVED — inverting family (matches Belluomini LSDL paper)
Decision (2026-05): build the **natural inverting LSDL gates**. The nFET eval tree
is the computation block; predriver + output driver are the latch/drive inverters,
not a positive-logic restorer. So `Out = !(eval-tree conducts)`:

| Physical eval tree | conducts when | LSDL function | cell name |
|---|---|---|---|
| 2-series | A·B | !(A·B) | **NAND2** (= existing Wave-0 lsdl_nand2_x1, physically; not Boolean-AND) |
| 3-series | A·B·C | !(A·B·C) | **NAND3** |
| 4-series | A·B·C·D | !(·) | **NAND4** |
| 2-parallel | A+B | !(A+B) | **NOR2** |
| 3-parallel | A+B+C | !(·) | **NOR3** |
| 4-parallel | A+B+C+D | !(·) | **NOR4** |
| (A·B)+C | — | !((A·B)+C) | **AOI21** |
| (A·B)+(C·D) | — | !(·) | **AOI22** |

No true AND/OR primitives in Wave 1 (would need a static output inverter = +2 FETs,
+area/power). Synthesis uses De Morgan mapping; add static inverters only where
polarity correction is unavoidable. Liberty/Verilog/LVS `function` = NAND/NOR/AOI.
NOR-family note (paper): parallel nFET tree is cheap, but watch the predriver pFET
side; the paper favors NAND complex-output over NOR for critical paths.
Generation order: NAND3→NAND4 (PEX NAND4) → NOR2/3/4 (PEX NOR4) → AOI21/22 (PEX
AOI22) → NAND_CMPLX (PEX immediately). Eval-NMOS width scaled by stack height
(NAND3 1.0 µm, NAND4 1.2 µm) per Task-3 guidance; PEX charge-share gate confirms.

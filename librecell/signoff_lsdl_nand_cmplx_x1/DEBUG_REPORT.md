# DEBUG: lsdl_nand_cmplx_x1 — LibreCell internal LVS FAILS (net shorts)

Status: **FAIL** at TRACKS=11 and TRACKS=13. lclayout routes the cell but its own
LVS rejects it; with `--ignore-lvs` it emits a GDS that has 2 net shorts + 1 M1.2a.

## ROOT CAUSE — the router shorted two net pairs
From lclayout's verbose LVS, the layout-extracted netlist collapses these nets
(KLayout names a merged net `'X,Y'` when X and Y are physically one net):

  - **`B` ≡ `DYN2`**  (input B shorted to dynamic node dyn2)
  - **`CLK` ≡ `OUT`** (clock shorted to the output)

Evidence — extracted subckt port line (shorted nets shown merged):
```
circuit lsdl_nand_cmplx_x1 (VGND,OUT_B,DYN1,'B,DYN2','CLK,OUT',A,VPWR)
```
The reference (input) has all 6 ports distinct:
```
circuit LSDL_NAND_CMPLX_X1 (A,B,CLK,OUT,VPWR,VGND)
```
The final extracted port list collapses to just `(VGND,A,VPWR)` — because the
shorts merge B/DYN2 and CLK/OUT, destroying the pin set. → "Netlists don't match".

## Why DRC looked clean but the cell is wrong
A net short is a **connectivity** error, not a geometry rule. KLayout DRC on the
`--ignore-lvs` GDS reports only **1 × M1.2a** (metal1 spacing) + the chip-level
DF.13/14_LV taps — it does NOT flag the shorts. So "DRC 0" in the signoff run was
doubly misleading: (a) it ran on a stale/missing GDS (lclayout writes no GDS on LVS
fail), and (b) DRC can't see shorts anyway. **LVS is the gate that caught it.**

## Why this cell and not the others
This is the only cell with **16 FETs + TWO dynamic nodes (dyn1,dyn2) + a NAND-form
predriver** (parallel pullup PMOS + series pulldown NMOS). It is far denser than the
basic cells (≤12 FETs, single dyn), and lclayout's pathfinder router merges adjacent
nets under that congestion. TRACKS=13 (taller row, more channels) did NOT help —
same two shorts — so it is a router-quality limit on this topology, not just room.

Geometric hint: `B` gates N2 whose drain is `DYN2` (they are physically adjacent —
gate poly beside its own drain diffusion); `CLK` drives a long horizontal spine that
crosses the `OUT` column. The render (cmplx_shorted.png) shows the long DYN1/CLK
horizontal M1 runs that collide.

## Functional note (important for scoping)
`lsdl_nand_cmplx_x1` computes **Out = !(A+B) = NOR2** — which we ALREADY have as the
DRC/LVS-clean `lsdl_nor2_x1` (single tree). Likewise `lsdl_nand_cmplx_aoi` would be
**!((A·B)+(C·D)) = AOI22**, already built as the clean `lsdl_aoi22_x1`. The complex
(two-tree) form is the paper's *timing* optimization (two short trees vs one combined
tree), not a new function. So if the router can't be coaxed, the basic-cell
equivalents cover the tapeout's functional needs; the complex cells are optional.

## Files (for debugging)
- input netlist (lclayout):   `lsdl_lib/librecell/lsdl_nand_cmplx_x1.sp`
- hand-source SPICE (LVS ref):`lsdl_lib/cells/lsdl_basic/lsdl_nand_cmplx_x1.spice`
- functional proof (correct):  ngspice tb gave Out=!(A+B) ✓ (topology is right)
- shorted GDS/LEF/mag:        `/soe/czeng14/projects/brainstorm-domino-tmp/sc_lsdl_nand_cmplx_x1/dbg/`
- full verbose LVS (both netlists): `…/sc_lsdl_nand_cmplx_x1/cmplx_lvs_verbose.log`
- render of shorted layout:    `…/sc_lsdl_nand_cmplx_x1/cmplx_shorted.png`
- DRC: 1×M1.2a + chip-level DF.13/14_LV (run dir `…/drc_runs`)

## DEBUG OUTCOME (timeboxed session) — marked OPTIONAL, use equivalents

| Step | Attempt | Result |
|---|---|---|
| 0 | Hard-stop signoff on internal-LVS fail; debug GDS under `debug/` only | done (signoff_cell.sh) |
| 1 | Locate shorts (trace_short.py) | **met1** horizontal spines merge nets: B↔DYN2 (x6.5–12.8, NMOS band) and CLK/OUT/DYN1/DYN2 across wide met1 runs |
| 2 | Placement sweep: SMT 200/500 cand @ T11 & T13; euler @ T11 & T13 | SMT routes but **LVS FAIL** (shorts persist); euler **does not route** |
| 6 | Predriver pullup 3.0→1.5 µm | **worse — no route** at T11/T13 |
| 3 | Placement-file separation (separate dyn1/dyn2 trees, cluster CLK, keep OUT off CLK spine) | **untried** — high effort, uncertain; the one remaining lever |

**Root mechanism:** the 16-FET / two-dyn / NAND-form-predriver cell exceeds lclayout's
met1 (horizontal) routing capacity at this cell height — the router lays long
horizontal met1 spines that merge multiple nets. Not a tracks/width/sizing problem
(all tried). It is a router-quality limit on this topology.

**DECISION (per timebox policy):** mark `lsdl_nand_cmplx_x1` (and `nand_cmplx_aoi`)
**OPTIONAL / stretch**. They are **functionally redundant**:
  - `nand_cmplx_x1` = !(A+B) = **`lsdl_nor2_x1`** (signed off, clean)
  - `nand_cmplx_aoi` = !((A·B)+(C·D)) = **`lsdl_aoi22_x1`** (signed off, clean)
Use the basic-cell equivalents for the tapeout. The complex two-tree form is the
paper's *timing* optimization, not a required function — it does not block progress.
If revisited: try Step 3 (placement-file) or hand-Magic this single cell.

## Things to try (router-coaxing, in rough order)
1. `--placer euler` or many more `--place-max-candidates` (e.g. 200) — different
   placements change which nets are adjacent and may avoid the B/DYN2 & CLK/OUT
   collisions.
2. Reduce predriver pullup width (2× PMOS @ 3.0u is wide → congestion); try 1.5–2.0u.
3. Provide a placement file (`--placement-file`) fixing the two trees apart so dyn1/
   dyn2 don't crowd the inputs.
4. Split into two physical rows / wider cell, or hand-Magic this one cell.
5. Accept the basic-cell equivalents (nor2 / aoi22) and mark the complex cells as a
   stretch optimization (they're functionally redundant).

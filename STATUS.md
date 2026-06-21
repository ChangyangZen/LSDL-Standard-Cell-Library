# LSDL library status (Wave 1)

Tag: **lsdl_wave1_basic_9cells_phys_signoff_v0** — see
`librecell/FREEZE_lsdl_wave1_basic_9cells_phys_signoff_v0.md` (SHA256 of all GDS/LEF).

## Signed off — physical (9 BASIC cells)
0 cell-level DRC · block Netgen LVS "Circuits match uniquely" · pin-access PASS · LEF audit PASS.
PEX timing/glitch validated on the deepest of each family (charge-share dyn floor > 3.5 V w/ parasitics).

| Cell | function | inputs |
|---|---|---|
| lsdl_inv_x1   | !A                    | A |
| lsdl_nand2_x1 | !(A1·A2)              | A1 A2 |
| lsdl_nand3_x1 | !(A1·A2·A3)           | A1 A2 A3 |
| lsdl_nand4_x1 | !(A1·A2·A3·A4)        | A1 A2 A3 A4 |
| lsdl_nor2_x1  | !(A1+A2)              | A1 A2 |
| lsdl_nor3_x1  | !(A1+A2+A3)           | A1 A2 A3 |
| lsdl_nor4_x1  | !(A1+A2+A3+A4)        | A1 A2 A3 A4 |
| lsdl_aoi21_x1 | !((A1·A2)+B)          | A1 A2 B |
| lsdl_aoi22_x1 | !((A1·A2)+(B1·B2))    | A1 A2 B1 B2 |

Plus the 11T physical-support library: `signoff_support_11t/` (tap, endcap, fill ×3) — every seam combo DRC-clean.

## Optional / blocked (2 COMPLEX cells)
- lsdl_nand_cmplx_x1  = !(A+B)            → **use lsdl_nor2_x1**  (router met1 shorts; see DEBUG_REPORT.md)
- lsdl_nand_cmplx_aoi = !((A·B)+(C·D))    → **use lsdl_aoi22_x1**
Functionally redundant timing-optimization cells; do not block tapeout. `COMPLEX_CELLS_OPTIONAL.md`.

## Deferred (not yet attempted)
- MUX2 (mux benchmark building block) — Wave 1 list, not in the adder-mapper sequence.
- Wave 2 wide cells (OR_TREE, MUX_SEG, PRI_ENC_CELL).

## No benchmark requires the complex cells
Adder: NAND/NOR/AOI/INV (the AOI22 covers the "hot path" the complex cell optimized).
Mux: AND/AOI22/MUX2 + Wave-2 MUX_SEG.  Encoder: OR family + Wave-2 OR_TREE/PRI_ENC_CELL.

## Conventions / collateral
- Pin naming: ALL-UPPERCASE (PIN_CONVENTION.md). LEF frozen uppercase; L5 Liberty/Verilog must match.
- LSDL cells are **clocked sequential** (positive-edge flop on CLK, inverting next_state) — Liberty must
  use the `ff` sequential model, NOT a combinational `function`.
- Next: **L5 Liberty generation** (conservative first pass → OpenSTA-accepted → adder block in LibreLane),
  then refine timing with PEX data.

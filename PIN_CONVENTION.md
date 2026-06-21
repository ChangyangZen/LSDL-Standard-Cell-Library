# LSDL library pin-naming convention (FROZEN at wave1 v0)

**Tool-facing collateral (LEF, Liberty, Verilog, DEF) uses ALL-UPPERCASE pin names**,
because the frozen LEFs (`signoff_*/*.lef`, written by lclayout) are uppercase and
LibreLane/OpenROAD require LEF == LIB == Verilog == DEF pin names to match exactly.

| Pin | Name(s) | Liberty role |
|---|---|---|
| inputs (single) | `A` | input; data |
| inputs (multi)  | `A1 A2 A3 A4`, and `B`/`B1 B2` for AOI second arm | input; data |
| clock | `CLK` | input; `clock : true` |
| output | `OUT` | output; driven by `ff` next_state |
| power | `VPWR` | `pg_pin … primary_power` |
| ground | `VGND` | `pg_pin … primary_ground` |

Confirmed uniform across all 9 signed-off LEFs (inv, nand2/3/4, nor2/3/4, aoi21/22).

## Rules for downstream collateral (L5 onward)
- **Liberty (.lib):** use `CLK`, `OUT`, `A`/`A1..`, etc. Sequential model
  (LSDL cells are clocked, NOT combinational): `ff(IQ,IQN){ clocked_on:"CLK";
  next_state:"<inverting function>"; }`, `pin(OUT){ function:"IQ"; }`,
  `pin(CLK){ clock:true; }`, `pg_pin(VPWR/VGND)`. next_state per cell:
  inv `A'`; nand2 `(A1 A2)'`; nand3 `(A1 A2 A3)'`; nor2 `(A1+A2)'`;
  aoi21 `((A1 A2)+B)'`; aoi22 `((A1 A2)+(B1 B2))'`.
- **Verilog wrapper (.v):** module ports uppercase, matching LEF/LIB exactly.
- **The existing `cells/lsdl_basic/lsdl_inv_x1.lib` and `.v` use mixed-case
  `Clk`/`Out` (pre-freeze, hand-authored) → REGENERATE uppercase in L5.**

## Hand-source SPICE exception
`cells/lsdl_basic/*.spice` and `librecell/*.sp` may keep mixed-case `Clk`/`Out` —
Netgen LVS is case-insensitive and already matches uniquely. Not tool-integration
critical. New collateral nonetheless follows the uppercase convention above.

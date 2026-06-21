# scripts/

Stubs for the three generators that consume `descriptor/*.yaml`.

| Script | Status | Purpose |
|---|---|---|
| `gen_liberty.py` | TODO (Wave 0) | descriptor + characterization JSON → `.lib` (positive-edge flop on Clk; setup/hold/min-pulse-width) |
| `gen_verilog_wrapper.py` | TODO (Wave 0) | descriptor → blackbox `.v` for yosys/LibreLane functional sim |
| `clk_ratio_characterize.py` | TODO (Wave 0) | ngspice harness measuring `(t_pre,min, t_eval,min, glitch_pct, charge_share_dip)` per (cell, corner) |

All three are scheduled as Wave 0 deliverables; no code yet because
Wave 0 hand-layout work has not begun. Schema for the descriptor is in
`../descriptor/SCHEMA.md`.

## Implementation notes (for when these get built)

- **Liberty pattern:** `ff (IQ, IQN) { clocked_on: "Clk"; }` per cell.
  Setup of inputs measured from Clk rising. C1 and C2 are SDC-level
  concerns; cells just declare `Clk`.
- **Characterization corner sweep:** 5 process × 3 temp × 3 Vdd = 45
  PVT points × per-cell stimulus set. Use SPICE caching aggressively.
  Inject `.ic` on dynamic nodes to avoid floating-node convergence
  failures.
- **Glitch sizing rule from paper (p. 278):** glitch on `out_b` < 10%
  VDD across all corners. Characterization script fails the cell if any
  corner exceeds this.

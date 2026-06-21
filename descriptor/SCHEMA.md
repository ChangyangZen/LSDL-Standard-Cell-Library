# Cell Descriptor Schema

Each LSDL cell has one YAML descriptor in this directory. The descriptor
is the single source of truth — Liberty, Verilog wrapper, and
characterization stimulus are generated from it. Layout (`.mag`) and
hand-source SPICE are authored separately and referenced by path.

## Schema

```yaml
name: lsdl_nand2_x1
library: lsdl_fd_sc_9t5v0
form: basic          # 'basic' (Fig. 1) | 'nand_cmplx' (Fig. 3a)
drive: 1             # 1, 2, 4
function: "!(A1 & A2)"   # Boolean expression in cell input pins

pins:
  - {name: Clk,  direction: input,  is_clock: true}
  - {name: A1,   direction: input}
  - {name: A2,   direction: input}
  - {name: Out,  direction: output}
  - {name: VPWR, direction: power}
  - {name: VGND, direction: ground}

n_tree:
  # For 'basic': a single tree producing dyn = NOT(<expr>).
  # For 'nand_cmplx': two trees, dyn1 and dyn2, ANDed via complex
  # output gate per Fig. 3a.
  - id: dyn
    expr: "A1 & A2"      # n-FET tree implements pulldown when expr=1
    stack_height: 2

sizing:
  precharge_w_um: 1.0
  foot_w_um: 0.8
  header_w_um: 0.8
  cut_feedback_w_um: 0.4
  predriver_p_w_um: 0.6
  predriver_n_w_um: 0.4
  feedback_p_w_um: 0.2
  feedback_n_w_um: 0.2
  output_driver_p_w_um: 1.5
  output_driver_n_w_um: 0.9
  n_tree_w_um: 0.8       # uniform unless overridden per-device

worst_case_eval_vector:
  # The input combination that produces the longest evaluate delay.
  # Used by clk_ratio_characterize.py to bound min_pulse_width_high.
  inputs: {A1: 1, A2: 1}

characterization:
  corners: [TT, SS, FF, SF, FS]
  vdd_range_v: [4.75, 5.0, 5.25]
  temperature_c: [-40, 25, 125]
  mc_points: 100         # Monte Carlo points at binding corner
  glitch_threshold_pct: 10   # paper sizing rule, p. 278

artifacts:
  spice_source: ../cells/lsdl_basic/lsdl_nand2_x1.spice
  magic_layout: ../cells/lsdl_basic/lsdl_nand2_x1.mag
  liberty_out:  ../cells/lsdl_basic/lsdl_nand2_x1.lib
  lef_out:      ../cells/lsdl_basic/lsdl_nand2_x1.lef
  verilog_out:  ../cells/lsdl_basic/lsdl_nand2_x1.v
```

## Field notes

- **`form: basic`** maps to paper Fig. 1. Single evaluation tree feeds
  the predriver inverter pair.
- **`form: nand_cmplx`** maps to paper Fig. 3(a). Two evaluation trees
  feed a NAND-form complex output gate. `n_tree` list must have exactly
  2 entries.
- **`function`** is the cell's logical Boolean expression at `Out`.
  Liberty emitter compares this to the n-tree definition for sanity
  checking.
- **`worst_case_eval_vector`** must drive every n-FET in the
  evaluation tree to its conducting state — produces the maximum
  pulldown current and thus the worst-case evaluate delay.
- **`glitch_threshold_pct`** is the hard sizing gate from the paper.
  Characterization fails if any corner exceeds this.

## Generation flow

```
descriptor/*.yaml
  ├── gen_liberty.py        →  cells/*/<name>.lib
  ├── gen_verilog_wrapper.py →  cells/*/<name>.v
  └── clk_ratio_characterize.py
       reads spice_source + Magic-extracted parasitics
       writes <name>_char.json with measured timing/power/glitch
       then gen_liberty.py re-runs to fold measured data into .lib
```

Magic `.mag` and the hand-source `.spice` are authored manually; LVS
(Netgen) compares the Magic-extracted netlist against the hand-source
SPICE for equivalence.

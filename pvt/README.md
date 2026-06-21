# PVT characterization data

One JSON per cell, written by `scripts/pvt_sweep.py`, consumed by
`scripts/gen_liberty.py`. These are the durable record of cell
characterization — version-controlled here, unlike the per-sim ngspice logs
and generated testbenches, which are regenerable and stay in
`/soe/czeng14/projects/brainstorm-domino-tmp/pvt_sweep/`.

Each file: 45 points = 5 corners (typical/ss/ff/sf/fs) × 3 temps
(-40/25/125 °C) × 3 VDDs (4.75/5.0/5.25 V).

```json
{
  "cell": "lsdl_nor2_x1",
  "overall_pass": true,
  "n_pvt": 45,
  "n_pass": 45,
  "results": [
    {
      "corner": "typical", "temp_c": -40, "vdd_v": 4.75,
      "pass": true, "failing": [],
      "meas": {
        "tpd_eval_hl": 1.81e-10,     // CLK rise -> Out transition (s)
        "v_dyn_low_min": -0.061,     // dyn floor under full discharge (V)
        "v_out_b_glitch": 0.062,     // out_b bump in a stay-high eval cycle
        ...                          // per-cell measurement set
      }
    }, ...
  ]
}
```

Status (2026-06-02): all 9 Wave 1 BASIC cells, 45/45 PASS each.
Liberty TT values are taken from the typical/25 °C/5.0 V entry; worst-case
`min_pulse_width_high` from the slowest passing point (SS/125 °C/4.75 V).

To re-characterize a cell after a SPICE/testbench change:
```bash
python3 lsdl_lib/scripts/pvt_sweep.py <cell>     # rewrites <cell>_pvt.json here
python3 lsdl_lib/scripts/gen_liberty.py --all --output lsdl_lib/lib/lsdl_fd_sc_9t5v0__tt_5v_25c.lib
```

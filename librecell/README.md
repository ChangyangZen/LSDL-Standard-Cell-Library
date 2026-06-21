# LibreCell GF180MCU cell-layout synthesis

Automated, SMT-verified (Z3) standard-cell layout for GF180MCU 5 V, 9-track.
Primary cell-synthesis path for this project (see plan `glowing-riding-shell.md`,
section "LibreCell Integration"). SO3-Cell / SMTCell-MH are kept in the project
docs for future advanced-node (FinFET) work only.

## Layout
- `venv/` — Python venv (created inside the IIC-OSIC-TOOLS container, mounted
  path) with `lclayout` 0.0.18, `z3-solver` 4.16, `pysmt`. klayout bindings come
  from the container's system site-packages (`--system-site-packages`).
- `tech_gf180mcu/` — LibreSilicon GF180MCU tech for lclayout. Source:
  https://gitlab.libresilicon.com/generator-tools/standard-cell-generator (`Tech.GF180MCU/`).
  - `librecell_tech.py` — the only file lclayout needs for layout: GF180 5 V DRC
    rules, GDS layers, 9×560 nm row. Env knobs: `TARGETVOLTAGE` (3.3V/5V/6V/10V),
    `TRACKS` (default 9), `DNWELL`.
  - `transistors.ngspice`, `design.ngspice` — GF180 SPICE models; needed only for
    downstream Liberty characterization, NOT for layout/LVS.
- `out/` — generated GDS/LEF/mag.

## Run a cell
```bash
cd /mada/users/czeng14/projects/brainstorm/domino
VENV=lsdl_lib/librecell/venv
./lsdl_lib/scripts/run_in_container.sh \
  "PYSMT_CYTHON=False TARGETVOLTAGE=5V TRACKS=9 DNWELL=True PYTHONHASHSEED=42 \
   $VENV/bin/lclayout \
     --tech  lsdl_lib/librecell/tech_gf180mcu/librecell_tech.py \
     --netlist <cell>.sp --cell <CELLNAME> \
     --output-dir lsdl_lib/librecell/out"
```

## Netlist contract (from lclayout's `lccommon.net_util`)
- `.subckt NAME <pin list>`; pins include VDD/VSS-style power nets.
- Devices: primitive 4-terminal MOSFET `M<n> D G S B model w=Xu l=Yu`.
- Channel type is taken from the **model name**: name starting with `n`
  (lowercased) → NMOS, otherwise PMOS. Use `nmos` / `pmos`.
- lclayout overrides the drawn gate length with the tech's
  `gate_length_{nmos,pmos}`; netlist `l=` is used for device matching.

## Gotchas
- `PYSMT_CYTHON=False` is required: pysmt otherwise tries to Cython-compile its
  SMT-LIB parser at import and fails (no Python.h in the container).
- `PYTHONHASHSEED=42` for reproducible results (lclayout is order-sensitive).
- Each container invocation is fresh; the venv lives on the mounted project path
  so it persists.
## Patches applied (L2 enablement bring-up)

To run on KLayout 0.30.8 + produce GF180-DRC-cleaner output, three fixes were made:

1. **`venv/.../lclayout/standalone.py`** `fill_all_notches`: `region += shape`
   → `region.insert(shape)`. KLayout 0.30.8 returns `PolygonWithProperties` from
   `Region.each()`, which makes `+=` ambiguous (fatal at post-process).
2. **`tech_gf180mcu/librecell_tech.py`** `gate_length_{nmos,pmos}`: the 5 V/6 V
   values were **swapped**. Set NMOS=600 nm, PMOS=500 nm (GF180 PL.2;
   nfet_05v0 Lmin=0.6, pfet_05v0 Lmin=0.5). Before the fix lclayout drew a
   DRC-illegal 0.5 µm NMOS and LVS mismatched on L. After: LVS SUCCESS.
3. **`tech_gf180mcu/librecell_tech.py`** `via_size[l_*_contact]`: 230 nm → 220 nm.
   CO.1 is an **exact-size** rule (`without_length(0.22um)`), so 230 nm contacts
   all failed. Cleared 20 CO.1 violations.

## L2 status (stock INVX1 spike)

- Pipeline runs end-to-end: place → route → notch-fill → SMT DRC-clean → LVS → GDS/LEF/mag/oas.
- **LVS: SUCCESS** against the input netlist.
- GF180 KLayout DRC: **8 cell-level violations** (down from 28), + DF.13_MV/DF.14_MV
  (chip-level taps, expected — well-tap auto-routing currently fails with "routing
  graph not connected").
- Remaining 8 = CO.6a (3, metal1 end-of-line over contact), M1.3 (1, metal1 min
  area), M2.3 (2, metal2 min area), DF.12 (2). All trace to the lclayout SMT
  min-area cleaner returning UNSAT on small pinned metal stubs — next bring-up step
  is metal-enclosure / routing-grid calibration (or widen metal min width).
- Run knobs that work: `TARGETVOLTAGE=5V TRACKS=9 DNWELL=False PYTHONHASHSEED=42`.

## L3 status (LSDL inverter)

**Result: lclayout generates a fully-routed, LVS-clean LSDL inverter** (`out/lsdl_inv_x1.gds`,
from `lsdl_inv_x1.sp`, 11 FETs, Belluomini Fig.1). This proves the core premise —
the SMT flow handles the LSDL feedback latch + single-Clk-to-4-gates fanout.

Key findings:
- **LSDL needs a taller row than 9T.** At `TRACKS=9` the routing graph is
  disconnected at every cell width (7–12) — the LSDL connectivity needs more
  horizontal channels. At **`TRACKS=11`** (and 13) it routes + LVS passes. So the
  LSDL library uses an 11-track row (separate from the 9T static-CMOS library;
  the plan already allows a separate LSDL library). Use `--placer smt`.
- A third lclayout patch was needed: `standalone._06_route` now catches the
  "routing graph not connected" assertion and returns False so the place&route
  loop tries the next placement (it previously crashed). EulerPlacer yields only
  1 placement; the SMT placer sweeps widths.
- DRC against the official GF180 deck: **41 cell-level violations, all root-caused**:
  - `PL.5a/b_LV` (10), `DF.12` (6), `NW.4`/`LPW.12` (2): missing 5V markers
    (DUALGATE 55/0) + implants (NPLUS 32/0, PPLUS 31/0) + well-mixing. lclayout's
    GF180 `output_map` omits DUALGATE and never generates implants — the
    libresilicon flow expected Magic to derive them.
  - `PL.5a/b_MV`: lclayout's **poly endcap over active (`gate_extension=220nm`) is
    short of GF180 PL.5** — a real geometry gap, surfaces once DUALGATE marks the
    gates as 5V.
  - `CO.6a` (16), `M1.3` (2), `M2.3` (5): metal end-of-line / min-area — the
    lclayout SMT min-area cleaner returns UNSAT on small pinned metal stubs.
- A crude GDS marker post-process (`librecell_postprocess.py`) was tried but is
  insufficient: derived implants violate NP.5a/PP.5a enclosure, and markers can't
  fix the poly-endcap geometry. Proper fix must be **in the lclayout tech/codegen**
  (generate DUALGATE + implants with correct enclosure; raise poly endcap; tune
  metal min-width/enclosure so the min-area cleaner is SAT). This is the next
  bring-up chunk — a multi-step enablement-hardening effort.

## DRC hardening progress (Step 0 baseline frozen in `baseline_lsdl_inv_x1/`)

True baseline (stale `.lyrdb` wiped): **33 cell-level**, LVS clean.
Use `gen_and_drc.sh <cell> [tracks]` — it wipes the run dir each time so counts
are never inflated by stale `.lyrdb` (the trap that made 33 look like 41/104).

| Step | Fix | Result |
|---|---|---|
| 0 | freeze baseline | 33, LVS ok |
| (5, taken early) | CO.6a: M1↔contact enclosure 40→60 nm | **33 → 16** (CO.6a 13→0; PL.5 10→6); LVS ok |
| 3 | DF.12: per-row NPLUS/PPLUS implant bands (single box/row) in `standalone._09_post_process` | 16 → 12 (DF.12 4→0); LVS ok |
| 2(well) | NW.4/LPW.12: clip LVPWELL out of NWELL in codegen | 12 → 10; LVS ok |
| 4(metal) | M1.3/M2.3: via1 landing-pad enclosure 40→70 nm (0.40 µm pad ≥0.1444 µm²) | 10 → **6 (PL.5-only)**; LVS ok |

| 1 (PL.5) | gate pitch 2→3 tracks (`unit_cell_width=3*560`): field-poly↔neighbor-COMP gap 0.08→0.36 µm ≥0.3 (MV) | 6 → **0**; LVS ok |
| 5 (markers) | `librecell_postprocess.py`: DUALGATE (single covering rect, +0.4 µm; avoids DV.2) + FET5VDEF | **0 cell-level + 5V-marked**; LVS ok |

### ✅ SIGN-OFF: `signoff_lsdl_inv_x1/` — 0 cell-level DRC, LVS clean, 5V-marked
Full progression: **33 → 16 → 12 → 10 → 6 → 0 → 0+5V**. Only 4 chip-level tap
rules (DF.13/14_MV) remain — satisfied by filler/endcap at PnR. The final flow:
`lclayout (TRACKS=11, 3-track gate pitch, --placer smt) → librecell_postprocess.py`.

`parse_drc.py` treats DF.13/14_LV/_MV as chip-level (tap-distance family).

Remaining 16: DF.12 (4 implants), PL.5a/b_LV (6, poly↔COMP spacing), M2.3 (3)/M1.3
(1, metal min-area), NW.4/LPW.12 (2, well-mixing). See
`baseline_lsdl_inv_x1/DIAGNOSIS.md` for per-class semantics and the revised order
(PL.5 spacing gates DUALGATE — do it before marking 5 V).

## Comparison cell (LSDL vs static CMOS, same SMT flow)

`lsdl_inv_x1` is semantically a **positive-edge flop with Out=!A** (not a
combinational inverter). The apples-to-apples SMT comparison cell is therefore a
**static-CMOS positive-edge D flip-flop with inverting output** (Q=!D) generated
through the same LibreCell flow/node — compare area, transistor count, delay.
Secondary baselines: a plain combinational static inverter (structural only, NOT
functionally equivalent — note the caveat) and the vendor
`gf180mcu_fd_sc_mcu9t5v0__dffq_1`/`__inv_1` as absolute references.

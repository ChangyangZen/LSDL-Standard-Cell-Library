# Lessons from building the LSDL inverter with LibreCell on GF180MCU

End-to-end record of taking `lsdl_inv_x1` from "nothing" to **0 cell-level DRC +
device-level Netgen LVS clean + bulk-closeable under a tap/filler row convention**,
using the open-source SMT cell generator **LibreCell (`lclayout`)** + the
LibreSilicon `Tech.GF180MCU` enablement. Companion to `README.md` (run commands +
patch list) and `baseline_lsdl_inv_x1/DIAGNOSIS.md` (per-class DRC semantics).

---

## 1. Why LibreCell, and the headline result

- LibreCell (`lclayout`) is open-source, uses **Z3 (SMT)** for correct-by-construction
  place-and-route, and there is a real **GF180MCU 5 V tech** for it. No commercial
  license (unlike ASTRAN/SO3-Cell which need Gurobi). Chosen as the project's cell tool;
  SO3-Cell/SMTCell-MH kept for future advanced-node work.
- It auto-generated a routed, LVS-clean **LSDL inverter** — the feedback latch +
  single-Clk-to-4-gates fanout that was hard to hand-route in Magic.
- **DRC progression: 33 → 16 → 12 → 10 → 6 → 0** cell-level, LVS clean throughout.

## 2. Tool bring-up gotchas (lclayout 0.0.18 + KLayout 0.30.8 + community tech)

These are install/version frictions, each cost a debugging cycle:

- **pysmt Cython parser** tries to JIT-compile at import and fails (no `Python.h`
  in the container) → set **`PYSMT_CYTHON=False`**.
- **KLayout 0.30.8 API drift**: `Region.each()` yields `PolygonWithProperties`, so
  `region += shape` is ambiguous → patch to **`region.insert(shape)`**
  (`standalone.py` `fill_all_notches`).
- **Unroutable placement crashed the whole run**: the routing graph builds an
  `assert False, 'Routing graph is not connected.'`. The place-and-route loop is
  designed to try the *next* placement, but the assert aborted it → patch
  `standalone._06_route` to **catch the AssertionError and return False** so the
  loop retries. (EulerPlacer yields only 1 placement; `--placer smt` sweeps widths.)
- **`PYTHONHASHSEED=42`** for reproducibility (lclayout is order-sensitive).
- The IIC-OSIC-TOOLS container is **ephemeral** → put the venv on the *mounted*
  project path so it persists across invocations.

## 3. Community GF180 tech-file bugs we found and fixed

The LibreSilicon `Tech.GF180MCU` is rough (author TODOs). Real bugs:

- **Gate lengths swapped**: had `gate_length_nmos=500 nm / pmos=600 nm`. GF180 PL.2
  is the opposite — **NMOS Lmin=0.6 µm, PMOS Lmin=0.5 µm** (matches nfet_05v0/pfet_05v0
  and our hand-source). Before the fix lclayout drew a DRC-illegal 0.5 µm NMOS and
  Netgen mismatched on L. After: LVS passes.
- **CO.1 contact size**: tech used 230 nm, but **CO.1 is an *exact*-size rule**
  (`without_length(0.22µm)`) → 230 nm contacts all failed. Set to **220 nm**.
- **CO.6a (M1↔contact end-of-line)**: M1-contact enclosure 40 nm gave 0.04 µm EOL
  overlap; rule needs 0.06 → set enclosure **60 nm**.
- **Min-area via pads**: via1 landing-pad = `via1(0.26)+2×0.04 = 0.34 µm` = 0.1156 µm²
  < Mn.3 0.1444 → bumped via1 enclosure **40→70 nm** (0.40 µm pad). The SMT
  min-area cleaner returned UNSAT on these pinned pads; the fix is to make pads
  **born larger**, not to grow them post-hoc.
- **No 5 V markers / implants generated**: `output_map` omits DUALGATE, and the
  transistor codegen never drew NPLUS/PPLUS. Added both (see §4).

## 4. The DRC-fix methodology that worked (33 → 0)

**Always wipe the DRC run dir before each run.** `.lyrdb` files accumulate in the
run dir (not in `drc_run_*` subdirs); `parse_drc.py` aggregates *all* of them, so
stale results inflate counts — 33 looked like 41 then 104. `gen_and_drc.sh` wipes
the dir every time. Track per-rule **and** total; a patch that "regresses" may just
be stale markers or LV↔MV rule re-grouping.

Per-class fixes, in the order that worked:

| Class | Root cause | Fix |
|---|---|---|
| CO.1 (20) | contacts 230 nm, rule is exact 0.22 | tech: contact size 220 nm |
| CO.6a (13) | M1 EOL over contact 0.04 µm | tech: M1↔contact enclosure 60 nm |
| DF.12 (4) | COMP not covered by implant | codegen: **per-row** NPLUS/PPLUS bands |
| NW.4 / LPW.12 (2) | LVPWELL overlaps NWELL | codegen: **clip LVPWELL out of NWELL** |
| M1.3 / M2.3 (4) | via pads < min area | tech: via1 enclosure 70 nm (born-larger) |
| PL.5a/b (6) | field-poly↔neighbor-COMP 0.08 µm | **widen gate pitch 2→3 tracks** → 0.36 µm |
| DV.2 (after markers) | jagged DUALGATE pieces < 0.44 µm apart | single covering DUALGATE rectangle |

Hard-won principles:

- **Implants: per-ROW bands, not per-device.** Per-device implant boxes
  (`active ± 0.23`) exploded NP.5a/PP.5a/PP.5dii (16 → 118) because of
  shared-diffusion boundary artifacts. A single implant box per row (bbox of all
  same-channel active, grown 0.24 µm) covers all gates with ≥0.23 µm overlap and
  has no internal NP.2/PP.2 gaps.
- **PL.5 is a *spacing* rule, not an endcap rule.** `PL.5a/b = field-Poly2 to COMP
  separation` (≥0.1 µm LV, **≥0.3 µm MV**). The 0.08 µm gap = `pitch − w/2 −
  gate_length/2`, where active width `w` is forced to span the gate pitch for
  diffusion sharing. Increasing **gate pitch** (`unit_cell_width` 2→3 tracks) is
  what opens the gap. Do **not** add `(l_poly, l_diffusion)` min-spacing — that
  forbids the gate sitting on its own diffusion.
- **Markers go in AFTER PL.5 is clean.** Adding DUALGATE flips gates LV→MV, which
  *raises* the field-poly↔COMP requirement 0.1→0.3 µm. Marking 5 V before the
  spacing is fixed makes PL.5 strictly worse.
- **Markers may be a post-process; implants must be codegen.** DUALGATE/FET5VDEF
  are non-electrical rectangles → safe as a GDS post-process
  (`librecell_postprocess.py`). Implants have enclosure rules tied to device
  geometry → must be generated with the cells (a crude implant post-process failed).
- DUALGATE as a **single covering rectangle** (bbox of poly+COMP + 0.4 µm), not a
  `.sized()` of the jagged outline — the jagged version left pieces < 0.44 µm apart
  (DV.2).

## 5. LVS lessons (official Netgen, not the internal checker)

- **lclayout's internal LVS ≠ official Netgen.** "LVS SUCCESS" in lclayout is its
  own KLayout extractor vs the input netlist. The sign-off LVS is **Magic
  `ext2spice` + Netgen + GF180 setup** vs the hand-source SPICE.
- Magic extraction was excellent: **11 devices, correct `pfet_05v0`/`nfet_05v0`,
  W/L matching, net names intact.** The debug order (device count → types → W/L →
  bulk → labels → opens/shorts) is the right triage.
- **Bulk is the one standalone gap.** A tapless cell extracts PMOS body = floating
  nwell (`w_0_616#`), NMOS body = `VSUBS` — not VPWR/VGND. Netgen: device count
  matches, **net count 12 vs 10** (the 2 extra are the untied wells).
- **Labeling the nwell "VPWR" does NOT fix it** — it produces `VPWR` *and*
  `VPWR_uq0` (two disconnected nets), which *proves* the nwell has no physical tie.
  A label can't substitute for a tap.

## 6. Tap/well convention + the row contract (decision: filler-based taps)

- **Functional cells stay tapless** (stock GF180 convention). nwell→VPWR and
  substrate→VGND ties come from **tap/endcap/fill cells** at block assembly. This
  keeps logic cells small and is why DF.13/14 are chip-level.
- **Validated end-to-end** (Option 3): an abutted `tap | inv | tap` block →
  wells merge to one polygon → **Netgen "Netlists match uniquely"** with PMOS
  bulk=VPWR, NMOS bulk=VGND, and **DF.13/14 gone**. Proof the convention closes.
- **The 11T LSDL row needs its own support cells** — stock GF180 fill/tap are 9T
  and won't abut.

### 11T row contract (use these as shared constants, do NOT recompute per cell)
From the signed-off inverter:
- cell height **6.16 µm** (11 × 0.56); boundary layer 63/0 at `x[0,width] y[0,6.16]`.
- **VPWR rail** (M1 34/0): `y[5.47, 6.40]`, full width.
- **VGND rail** (M1 34/0): `y[-0.24, 0.69]`, full width.
- **NWELL** (21/0): `y[2.22, 6.42]`, spans full width to both side boundaries.
- **LVPWELL** (204/0): `y[0, 2.22]`, clipped to NOT overlap NWELL.
- **gate pitch**: 3 tracks (`unit_cell_width = 3*560 nm`).
Support cells (tap/endcap/fill) must use these **exact** y-ranges so abutted well
layers form continuous row-level bands, not colliding rectangles.

## 7. Seam-debugging methodology for support cells (L6)

Abutment seams are where new DRC appears. Methodology:

1. **Tiny seam regression suite** — don't debug only the full block. Test:
   `tap|inv`, `inv|tap`, `tap|inv|tap`, `endcap|inv|endcap`, `fill|inv|fill`.
   Run official KLayout DRC after each → isolates left vs right abutment vs tap
   geometry vs inverter boundary vs missing continuation.
2. **Fix the well seam first (NW.4/LPW.12)** — match support-cell NWELL/LVPWELL
   y-ranges to the inverter's exactly; NWELL continues across boundaries; LVPWELL
   trimmed from NWELL by the required spacing.
3. **Fix the DUALGATE seam (DV.2)** — support-cell DUALGATE extends to the cell
   boundary so it abuts the neighbor's marker with no thin unmarked slit and no
   illegal overlap. Visual check at the seam.
4. **Build the whole support set**, not just a tap: `lsdl_tap_11t`,
   `lsdl_endcap_11t`, `lsdl_fill_11t_{1,2,4}`. PnR won't always place tap next to
   logic, so `tap|fill`, `fill|inv`, `inv|fill`, `fill|endcap` must all be legal.
5. **L6 debug order**: freeze passing block → build real tap (height+rails) →
   match well y-ranges → extend markers to abutment-safe boundaries → DRC tap
   alone → tap|inv → inv|tap → tap|inv|tap → add fill/endcap & test every seam →
   re-run Netgen LVS to confirm bulk still closes.
6. **Record each DRC marker** as (rule, left/right seam, x relative to boundary,
   layers, inside-tap / inside-inv / crossing-seam). Marker at the boundary →
   row-contract/support-cell fix. Inside tap → tap geometry. Inside inv → inverter
   boundary keepout (last resort).
7. **Do NOT fix L6 by modifying the inverter first.** The inverter is already cell-
   DRC clean, device-LVS clean, bulk-closeable. Fix support-cell wells/markers/
   boundaries first; touch the inverter only if seam tests prove its boundary is
   fundamentally incompatible with any legal support cell.

## 7b. L6 outcome — 11T support cells built and seam-clean

Built `lsdl_tap_11t / endcap_11t / fill_11t_{1,2,4}` to the row contract. The three
fixes that made abutment clean (vs the throwaway tap):
1. **Row-contract well y-ranges, NO overhang** — wells span `[0,W]` and abut at the
   exact boundary pitch (overhang had caused NW.4/LPW.12).
2. **DUALGATE spans the boundary in X** (continuous row band) for every cell — the
   inverter's marker was inset 0.26 µm, leaving a sub-0.44 µm DV.2 seam gap; the
   shared post-process now makes it boundary-to-boundary.
3. **Rectangularize NWELL/LVPWELL to clean bands** in the post-process — lclayout's
   per-FET well boxes leave a jagged top edge; at the seam that became a 0.06 µm
   NW.2a notch. Replacing with clean row-band rectangles removes it.

Results (official KLayout DRC): tap/endcap/fill_2/fill_4 standalone **0**; every
seam combo (tap|inv, inv|tap, tap|inv|tap, endcap|inv|endcap, fill|inv|fill,
tap|fill, fill|endcap, and a full 7-cell row) **0 cell-level**; DF.13/14 vanish once
a tap is in the row. Step-10 LVS on tap|inv|tap: **"Netlists match uniquely"**,
bulk=VPWR/VGND. `fill_11t_1` (1 track) has isolation-only NW.1a_MV+DV.5 (nwell/
dualgate min-width at 0.56 µm) — fillers are never placed alone, and it's clean in
every row context.

## 7c. L7 outcome — clean block LVS with declared ports

**Result: block-level Netgen LVS now reports "Circuits match uniquely" — no port
errors.** Steps:
1. lclayout annotates *every* net with hundreds of texts (DYN ×48, …) on all
   layers → Magic `port makeall` grabs them all (10+ pins, internal nets exposed).
   Fix: `mk_ports_gds.py` strips ALL texts and inserts exactly the 5 I/O labels on
   metal1 at the pin positions → `port makeall` yields exactly `A Clk Out VPWR VGND`.
2. The extracted `.subckt` pin line then matches the hand-source name+order exactly.
3. **Run LVS on the block (tap|inv|tap), not the standalone cell** — the tapless
   cell can't match (bulk floats by convention); in the block the taps close
   nwell→VPWR / sub→VGND and it matches uniquely.
4. **Do NOT use `ext2spice cthresh 0 / rthresh 0`** for LVS — that turns ON
   parasitic-cap extraction (adds C devices) and breaks the match. `ext2spice lvs`
   alone is the no-parasitic LVS mode.
5. LEF: lclayout writes all pins `DIRECTION INOUT` and VGND `USE POWER`.
   `fix_lef_pins.py` sets A/Clk=INPUT, Out=OUTPUT (SIGNAL), VPWR=POWER, VGND=GROUND
   for PnR. Scripts: `declare_magic_ports.tcl`, `mk_ports_gds.py`, `fix_lef_pins.py`.

## 7d. L4 outcome — the flow GENERALIZED (NAND2, zero new tech patches)

`lsdl_nand2_x1` (12 FETs = INV + series-NMOS `XNB`; 6 pins `A1 A2 Clk Out VPWR VGND`;
new charge-share node `nint`) went through the **identical** flow:
- `gen_and_drc.sh lsdl_nand2_x1 11` → **routed first try at 11T** (the series-NMOS stack
  was the risk; it converged), internal LVS SUCCESS, **0 cell-level DRC**.
- markers + 5V → 0 cell-level; seams `tap|nand2|tap`, `fill2|nand2|fill2` → 0.
- block Netgen LVS → **"Circuits match uniquely"**, 12 devices / 12 nets, bulk=VPWR/VGND,
  `nint` matched, no port errors. LEF pins corrected.

**No new tech patches were needed** — only three generic, one-time script generalizations:
`mk_ports_gds.py` now **auto-detects** each I/O net's metal1 label position (no hardcoded
coords); `fix_lef_pins.py` classifies by name pattern (A*/Clk=input, Out*=output,
VPWR/VGND=power/ground); `build_support.py combo` accepts any logic cell. This confirms the
flow is a **library generator**, not a one-off. Artifact: `signoff_lsdl_nand2_x1/`.

## 7e. Pin-access: lclayout grid ≠ LibreLane PnR grid (W1-A2)

A pin-access gate (`check_pin_access.py`) caught a **library-wide PnR blocker** before
Wave 1: lclayout places met2 signal-pin pads on its own grid (gate pitch/2 = 0.84 µm,
offset 0), but LibreLane met2 routes on **vertical tracks at x = 0.28 + 0.56·k**. They
coincide only every 1680 µm, so most pins (CLK, A, A1, A2) land **between** tracks →
TritonRoute gets **no access point**. Only pins that happen to sit on an odd multiple of
0.84 (e.g. OUT @ 0.84) are reachable.

Fix = **per-pin snap** (`snap_pin_access.py`), NOT a global cell shift (which fixes some
pins and breaks others on different sub-grids). For each signal pin: add an **on-net met2
access pad** = union(original pad, via-safe 0.56 µm box centered on the nearest met2 track).
Critical rules learned:
- **Only ADD met2 metal; never move the label.** First attempt relocated labels to met2,
  which broke the downstream met1-only label detection and LVS. The pad connects to the net
  through the existing via1 under the original pad, so Magic/LVS (which bind the met1 I/O
  label) are undisturbed.
- **Drive snap from the LEF pin rects, not GDS labels** — lclayout writes hundreds of
  net-annotation labels, so "nearest GDS label" grabbed a full-width rail for OUT. The LEF
  has exactly one met2 PORT rect per signal pin = the authoritative pad.
- **GDS and LEF must agree**: snap writes a `pinmap.json`; `fix_lef_pins.py` emits the same
  rect into the LEF, so the router doesn't target a phantom access point.
- Power pins (VPWR/VGND) are NOT snapped — rails, accessed by the PDN.
Result: inv + nand2 → DRC 0, block LVS match uniquely, **pin-access PASS**, LEF audit PASS.

## 7f. The hardened one-command flow: `signoff_cell.sh`

`signoff_cell.sh <cell> [tracks]` runs the entire hardened chain and prints a 4-gate
PASS/FAIL summary: lclayout → markers → port-clean → **snap** → LEF → KLayout DRC →
block Netgen LVS (tap|cell|tap) → **pin-access** + **LEF-audit** gates. Pins auto-read from
the `.subckt` line. This is the Wave-1 per-cell entry point. Collateral gate scripts:
`audit_lef.py`, `check_pin_access.py`, `snap_pin_access.py` (+ `fix_lef_pins.py --pin-map`).

## 7g. PEX timing/glitch gate (W1-A3)

Re-run the cell's testbench on the **parasitic-extracted** netlist to confirm eval
delay + the paper glitch/charge-share rules survive layout capacitance.
- **Caps-only extraction** (`extract all` + `ext2spice cthresh 0`, NO resistance):
  adds ~50 cap devices AND **preserves named internal nodes** (out_b, dyn) because
  nets aren't split. `subcircuit top off` would flatten but **loses the labels**
  (uses `a_276_24#`), so keep subckt mode.
- Expose probe nodes as **extra subckt pins**: `mk_ports_gds.py --pins
  A,Clk,Out,VPWR,VGND,dyn,out_b` (from the **markers gds**, which still has the
  internal labels) → `port makeall` → `.subckt cell A Clk Out VPWR VGND dyn out_b`.
- **Tie tapless bulk** in the extracted netlist (`pex_validate.py fix-bulk`):
  VSUBS→VGND, nwell node→VPWR (standalone cell has no taps).
- `pex_validate.py mk-tb` rewrites the schematic testbench: swap the `.include` for
  the PEX netlist, instantiate with the probe pins, de-hierarchy `v(Xinst.out_b)`→
  `v(out_b)`. No inline `*` comment on the instance line (ngspice only takes `$`).
- **A metal-less diffusion node (NAND2 `nint`, the series-stack mid-node) has no
  label and cannot be a probe pin** — its parasitic is folded into the adjacent
  `dyn` net, so drop it from the probe set.

Results (schematic → PEX): INV tpd 0.215→0.346 ns (≪2 ns), glitch negligible,
Out latched. NAND2 tpd 0.42 ns, **charge-share floor v_dyn_share 4.53 V > 3.5 V**
(the key LSDL metric survives parasitics), Out=0 under A1·A2. Both PASS.
Scripts: `pex_extract.tcl` (flat variant), `pex_validate.py`, `declare_magic_ports.tcl`
`PEX_CAPS=1`.

## 7h. Phase-A hardening complete
Three PnR-trust gates built + proven on inv & nand2, on top of DRC+LVS:
**LEF-vs-GDS audit**, **pin-access** (with the met2-track snap), **PEX timing/glitch**.
The pin-access gate caught a library-wide grid mismatch before Wave 1 — the reason to
harden first. `signoff_cell.sh` runs the layout gates per cell in one command; PEX runs
where a per-cell testbench exists.

## 7i. Wave 1 BASIC family generated (W1-B1)

Polarity decision: basic LSDL cell is **inverting** (`Out = !(eval-tree conducts)`).
Series stacks → NAND, parallel → NOR (matches Belluomini paper; no true AND/OR
primitives — De Morgan in synthesis). Generated via `signoff_cell.sh` + per-cell
`.sp` (lclayout) + hand-source `.spice` (LVS), eval-NMOS width scaled by stack
height (NAND3 1.0 µm, NAND4 1.2 µm):
- NAND3, NAND4 (series); NOR2, NOR3, NOR4 (parallel); AOI21, AOI22 (series-parallel).
- All: 0 cell-level DRC, block LVS match uniquely, pin-access PASS, LEF audit PASS,
  **first try** except NOR3 (see below). PEX-validated on the family-deepest cells
  (NAND4 charge-share dyn 4.57 V; NOR4 single-path discharge; AOI22 arm-A share 4.49 V)
  — all > 3.5 V floor with full parasitics.

**Spacing-aware snap (robustness fix from NOR3):** the met2 pin-access snap can
enlarge a pad into a neighbor net's met2 → M2.2a. Fix: `snap_pin_access.py` now
tries BOTH nearest tracks and picks one whose access pad clears 0.28 µm to other-net
met2 (the "if nearest collides, use the other track" rule); flags if neither clears.
Pre-snap NOR3 was DRC-clean — the snap was the cause, now self-correcting.

**Testbench meas-window note:** quickly-authored `.meas` windows can capture the
prior cycle's latched value or a legit eval-state level (NAND4 `v_out_cyc3`, NOR4
`v_out_b_glitch`). The definitive functional metric is the **dyn floor** (charge-share
> 3.5 V proves no false discharge). Window Out checks on the *settled* tail of the
cycle (AOI22 `v_out_cyc3_settled` @60-64 ns did this right). Refine per-cell windows
when authoring the full PVT testbenches.

MUX2 deferred (not in the adder-mapper sequence). Reusable: `pex_gate.sh`,
`TEMPLATE_lsdl_cell.sp`, `wave1_tb_plan.md`.

## 7j. COMPLEX (Fig 3a) cells — router-created shorts, marked optional (W1-B2)

`lsdl_nand_cmplx_x1` (16 FETs, two dynamic nodes dyn1/dyn2, NAND-form predriver =
parallel PMOS pullup + series NMOS pulldown) **fails lclayout's internal LVS**: the
router merges nets on **met1** (the horizontal routing layer) — long horizontal met1
spines short B↔DYN2 and CLK/OUT/DYN1/DYN2. Debugged as a *connectivity* failure, not
DRC (DRC only saw 1×M1.2a; shorts are not geometric — LVS is the gate).

Lessons:
- **lclayout writes NO normal GDS on internal-LVS fail.** `signoff_cell.sh` now
  hard-stops (`LVS result: FAILED` → save `--ignore-lvs` GDS under `debug/`, mark
  `FAILED_CONNECTIVITY`, exit) and deletes stale `out/*.gds` first — so a failed run
  can't yield a misleading "DRC 0". LVS, not DRC, is the connectivity gate.
- **Trace shorts by net intent, not geometry:** `trace_short.py` finds a metal
  polygon carrying labels of >1 net (the bridge) + its layer/coord. Here: met1.
- **Tried and failed:** placement sweep (SMT 200/500, euler, T11/T13 — shorts persist
  or no-route), predriver resize 3.0→1.5 µm (no route, worse). Not a tracks/width/
  sizing issue — a router-capacity limit on this dense topology.
- **Decision:** marked OPTIONAL. The complex cells are functionally redundant —
  `nand_cmplx_x1`=!(A+B)=`nor2`, `nand_cmplx_aoi`=!((A·B)+(C·D))=`aoi22` — both already
  signed off. Tapeout uses the basic equivalents (`COMPLEX_CELLS_OPTIONAL.md`). The
  complex form is the paper's timing optimization, not a required function. Remaining
  untried lever: a `--placement-file` separating dyn1/dyn2 trees, or hand-Magic.

## 8. Reusable assets produced
- `gen_and_drc.sh` — regenerate a cell + wiped-run-dir DRC + LVS line.
- `librecell_postprocess.py` — add DUALGATE + FET5VDEF (markers only).
- `magic_extract.tcl` — Magic GDS→SPICE extraction for Netgen.
- `build_tap_block.py` — throwaway tap + abutted block builder (block-LVS proof).
- `baseline_/best_/signoff_lsdl_inv_x1/` — frozen checkpoints with MANIFESTs.

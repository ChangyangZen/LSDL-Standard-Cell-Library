# lsdl_nor8_x1 — EXPERIMENTAL / QUARANTINED (not library-usable)

```
status:        NOT SIGNABLE
experimental:  true
use_in_blocks: false        # do NOT instantiate in synthesis/generation
DRC:           cell-level clean after foot=0.8 fix (DF.16=0), BUT
LVS:           FAILED (real signal opens)
```

## Why quarantined

`lsdl_nor8_x1` (8-input parallel-NMOS NOR, 18 devices, 25.2 × 6.16 µm on the 11T
row) **routes but is not electrically correct**. lclayout's post-route minimum-area
fixer cannot legalize the metal that bridges the Clk and Out distribution nets in
the congested wide cell, so those nets are left **open**:

```
Routing successful
  → Minimum area fixing: UNSAT (Constraints not satisfiable)
  → critical Clk/Out bridge not legalized
  → real signal opens
  → lclayout internal LVS: FAILED
```

Block-level Netgen LVS (`tap | nor8 | tap`) confirmed the opens (devices 18=18,
"device classes equivalent", but pin matching fails):
- **Clk split**: `{MFOOT, MCUTFB}` on the labeled Clk pin vs `{MPRE, MHDR}` on
  unlabeled island `a_4644#` — physically disconnected.
- **Out split**: output-driver drains/pin vs the feedback gates `{MFBP, MFBN}` on
  unlabeled island `a_3972#` — physically disconnected.

## Why it is structural, not bad luck

Two independent placements failed identically at the **same step**:
- `PYTHONHASHSEED=42`, candidates=30 → min-area UNSAT → Clk/Out opens.
- `PYTHONHASHSEED=1`,  candidates=40 → min-area UNSAT → LVS FAILED, no GDS.

The min-area UNSAT is congestion-driven: an 18-device cell in the 11T width leaves
no DRC-legal room for the Clk/Out bridge wires. Re-placement does not help, and
NOR16 (~26 devices) would be strictly worse. (The earlier DF.16_MV was a separate,
self-inflicted issue — an over-wide MFOOT — and was fixed by reverting to W=0.8.)

## Decision

`lsdl_nor8_x1` and `lsdl_nor16_x1` are **deferred**. Wide single-gate OR cells are
not built via lclayout. The priority/mux benchmarks compose wide ORs from the
**signed-off NOR4 + NAND4**:

```
OR16 = NAND4(NOR4(a0..a3), NOR4(a4..a7), NOR4(a8..a11), NOR4(a12..a15))
     = a0 | a1 | ... | a15      # NMOS-only evaluate in both stages (the LSDL showcase)
```

Reviving NOR8 as a real cell would require lclayout-internals work (pre-routed
fixed Clk/Out trunks before global routing — "Plan B") — out of scope; not on the
critical path.

## Artifacts (kept for reference, not for use)
- `lsdl_nor8_x1.sp`, `../cells/lsdl_basic/lsdl_nor8_x1.spice` (foot=0.8 source)
- `out/lsdl_nor8_x1{,_5v}.gds` (the open, --ignore-lvs GDS)
- logs: `brainstorm-domino-tmp/lsdl_nor8_x1_gen.log`, `nor8_seed{1,42}.log`,
  `sc_lsdl_nor8_x1/{blk.spice,lvs.log}`

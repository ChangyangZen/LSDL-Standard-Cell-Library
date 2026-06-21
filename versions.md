# Toolchain & PDK versions

This library is built and signed off against the versions below. Pin these
(ideally by image digest) to reproduce the signed-off views.

| Component | Version | Notes |
|---|---|---|
| PDK | **GF180MCU `gf180mcuD`** | installed separately (not vendored); Apache-2.0 |
| Container | `hpretl/iic-osic-tools:latest` | **pin a digest** for reproducibility |
| OpenROAD | `26Q2-1164-g08f67ee5e` | pin-access / abstract LEF checks |
| KLayout | `0.30.8` | DRC sign-off (GF180 `run_drc.py`) |
| Magic + Netgen | (from IIC-OSIC-TOOLS) | `ext2spice` + LVS |
| LibreCell `lclayout` | `0.0.18` | Z3 SMT place-and-route; see `librecell/` patches |
| ngspice | (from IIC-OSIC-TOOLS) | PVT characterization (`scripts/pvt_sweep.py`) |

## LibreCell run environment
```
PYSMT_CYTHON=False  TARGETVOLTAGE=5V  TRACKS=11  DNWELL=False  PYTHONHASHSEED=42
lclayout --placer smt --place-max-candidates 30
```

## Sign-off gates (per cell)
- KLayout DRC: **0 cell-level** violations (chip-level DF.13/14 tap rules deferred to block assembly).
- Netgen LVS vs hand-source SPICE: **Circuits match uniquely**.
- See each `librecell/signoff_<cell>/MANIFEST.txt` for the frozen view set + LVS log.

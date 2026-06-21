#!/usr/bin/env python3
"""overlay_eval.py — overlay the LSDL raw-eval node (dyn) against the static-CMOS
NAND2 output, each aligned to its own trigger, to compare pure-logic transition
speed directly. Both nodes = !(A1.A2): they FALL when A1=A2=1.

LSDL  : dyn  (col in lsdl dat) falls after the Clk evaluate edge.
CMOS  : Out  (col in cmos dat) falls after the switching input edge.
"""
import numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt

L = np.loadtxt("/soe/czeng14/projects/brainstorm-domino-tmp/nand2_wave.dat")
C = np.loadtxt("/soe/czeng14/projects/brainstorm-domino-tmp/cmos_nand2_wave.dat")
# lsdl dat vectors: Clk,A1,A2,dyn,out_b,Out,isup -> value cols 1,3,5,7,9,11,13
tL = L[:, 0]; clk = L[:, 1]; dyn = L[:, 7]
# cmos dat vectors: A1,A2,Out,isup -> value cols 1,3,5,7
tC = C[:, 0]; a2 = C[:, 3]; outc = C[:, 5]

def first_cross(t, v, lo, hi, rising, thr=2.5):
    m = (t >= lo) & (t <= hi)
    tt, vv = t[m], v[m]
    for i in range(1, len(tt)):
        if rising and vv[i-1] < thr <= vv[i]:  return tt[i]
        if not rising and vv[i-1] > thr >= vv[i]: return tt[i]
    return None

# LSDL: Clk evaluate edge of cyc2 (~25ns), dyn then discharges
tL0 = first_cross(tL, clk, 24e-9, 26e-9, rising=True)
# CMOS: A2 rising edge that makes Out fall (~30ns)
tC0 = first_cross(tC, a2, 29e-9, 31e-9, rising=True)

fig, ax = plt.subplots(figsize=(9, 5))
ax.plot((tL - tL0) * 1e12, dyn, "tab:green", lw=2,
        label="LSDL  dyn  (raw n-tree NAND eval)")
ax.plot((tC - tC0) * 1e12, outc, "tab:red", lw=2, ls="--",
        label="CMOS  NAND2 out (combinational)")
ax.axhline(2.5, color="0.7", lw=0.8, ls=":")
ax.set_xlim(-50, 500); ax.set_ylim(-0.3, 5.5)
ax.set_xlabel("time since trigger (ps)   [LSDL: Clk eval edge | CMOS: input edge]")
ax.set_ylabel("voltage (V)")
ax.set_title("Pure-logic transition: LSDL dyn vs static CMOS NAND2 — both !(A1·A2) falling")
ax.legend(); ax.grid(alpha=0.3)
fig.tight_layout(); fig.savefig("/soe/czeng14/projects/brainstorm-domino-tmp/eval_overlay.png", dpi=120)
print("wrote eval_overlay.png  (LSDL trig=%.3fns  CMOS trig=%.3fns)" % (tL0*1e9, tC0*1e9))

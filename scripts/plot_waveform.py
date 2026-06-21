#!/usr/bin/env python3
"""plot_waveform.py — stacked "logic-analyzer" plot of an ngspice wrdata dump.

Each voltage signal gets its OWN horizontal lane (no overlap), with a distinct
color + line style + marker per ROLE so inputs/clock/internal/output are easy to
tell apart. Supply current (role 'cur') goes in a bottom panel.

wrdata writes interleaved (time,value) column pairs in the order of the .control
`wrdata` line. Pass that order as <spec>.

Usage:
  plot_waveform.py <wave.dat> <out.png> <title> <spec>
  spec = comma list of name:role, in wrdata column order, e.g.
         "Clk:clk,A1:in,A2:in,dyn:int,out_b:int,Out:out,isup:cur"
roles: clk | in | int | out | cur
"""
from __future__ import annotations
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

dat, png, title, spec = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
sig = [tuple(s.split(":")) for s in spec.split(",")]
raw = np.loadtxt(dat)
t = raw[:, 0] * 1e9  # ns

STYLE = {  # role -> (color, linestyle, marker, label-prefix)
    "clk": ("black",      "-",  "",  "CLK "),
    "in":  ("tab:blue",   "-",  "o", "IN  "),
    "int": ("tab:green",  "--", "",  "int "),
    "out": ("tab:red",    "-",  "s", "OUT "),
}
volt = [(n, r, raw[:, 2 * i + 1]) for i, (n, r) in enumerate(sig) if r != "cur"]
curs = [(n, raw[:, 2 * i + 1]) for i, (n, r) in enumerate(sig) if r == "cur"]

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True,
                               gridspec_kw={"height_ratios": [len(volt), 2]})
# stack each voltage signal into its own lane (top = first signal)
lane_h, gap = 1.0, 0.35
N = len(volt)
yticks, ylabels = [], []
for k, (n, r, v) in enumerate(volt):
    base = (N - 1 - k) * (lane_h + gap)
    color, ls, mk, pre = STYLE.get(r, ("gray", "-", "", ""))
    vn = np.clip(v / 5.0, -0.05, 1.05)            # normalise 0..5V -> 0..1 lane
    # sparse markers so shape is visible but not dense
    me = max(1, len(t) // 60)
    ax1.plot(t, base + vn * lane_h, color=color, ls=ls, lw=1.6,
             marker=mk, markevery=me, ms=4, markerfacecolor="none")
    ax1.axhline(base, color="0.85", lw=0.6)        # lane baseline
    yticks.append(base + lane_h / 2); ylabels.append(f"{pre}{n}")
ax1.set_yticks(yticks); ax1.set_yticklabels(ylabels, fontsize=9)
ax1.set_ylim(-0.3, (N - 1) * (lane_h + gap) + lane_h + 0.3)
ax1.set_title(title); ax1.grid(axis="x", alpha=0.3)
ax1.text(0.01, 0.99, "○=input  □=output  ─black=clock  --green=internal",
         transform=ax1.transAxes, va="top", fontsize=8, color="0.3")

tmax = t[-1]
for n, v in curs:
    m = t >= 0.03 * tmax                            # mask t=0 uic start-up spike (scale-agnostic)
    ax2.plot(t[m], v[m] * 1e6, "tab:purple", lw=1.0, label=n)
    w = m & (t >= 0.2 * tmax) & (t <= 0.95 * tmax)  # avg over the steady middle
    ax2.set_title(f"I(VPWR): peak {(v[m]*1e6).max():.0f} µA, "
                  f"avg {(v[w]*1e6).mean():.1f} µA", fontsize=9)
ax2.set_ylabel("I (µA)"); ax2.set_xlabel("time (ns)"); ax2.grid(alpha=0.3)
fig.tight_layout(); fig.savefig(png, dpi=110)
print(f"wrote {png} ({len(t)} pts)")

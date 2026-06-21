#!/usr/bin/env python3
"""plot_lsdl_2ghz.py — multi-role stacked waveform for LSDL NAND2 @ 2 GHz.
Labels each lane by functional role, marks the 250ps evaluate window, and
annotates the clk-to-dyn (before latch) and clk-to-Out (after latch) delays.
"""
import numpy as np, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

dat  = sys.argv[1]
png  = sys.argv[2]
raw  = np.loadtxt(dat)
t    = raw[:, 0] * 1e9   # ns

# column order: Clk, A1, A2, dyn, out_b, Out, isup
Clk, A1, A2, dyn, outb, Out, isup = [raw[:, 2*i+1] for i in range(7)]

# ------------------------------------------------------------------
# lane definitions: (name, data, color, linestyle, marker, role_label)
LANES = [
    ("Clk",        Clk,  "black",       "-",  "",  "clock"),
    ("A1  [input]",A1,   "tab:blue",    "-",  "o", "input"),
    ("A2  [input]",A2,   "cornflowerblue","-","o", "input"),
    ("dyn  [DYNAMIC NODE\nbefore latch]",
                   dyn,  "tab:green",   "--", "",  "int"),
    ("out_b  [LATCHED NODE\n= what keeper holds]",
                   outb, "purple",      "--", "",  "int"),
    ("Out  [REGISTERED OUTPUT\nafter latch + driver]",
                   Out,  "tab:red",     "-",  "s", "output"),
]
N   = len(LANES)
lh, gap = 1.0, 0.4

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13, 9), sharex=True,
                                gridspec_kw={"height_ratios": [N, 1.8]})

yticks, ylabels = [], []
for k, (nm, v, col, ls, mk, _) in enumerate(LANES):
    base = (N - 1 - k) * (lh + gap)
    vn   = np.clip(v / 5.0, -0.05, 1.05)
    me   = max(1, len(t) // 80)
    ax1.plot(t, base + vn * lh, color=col, ls=ls, lw=1.7,
             marker=mk, markevery=me, ms=4, markerfacecolor="none", zorder=3)
    ax1.axhline(base, color="0.88", lw=0.6, zorder=1)
    yticks.append(base + lh / 2); ylabels.append(nm)

# shade evaluate windows (Clk high: 0.25..0.5, 0.75..1.0, 1.25..1.5, 1.75..2.0 ns)
for t0 in [0.25, 0.75, 1.25, 1.75]:
    ax1.axvspan(t0, t0 + 0.25, alpha=0.06, color="tab:orange", zorder=0)

# annotate clk-to-dyn delay on the 2nd eval edge (~0.75 ns trigger)
ax1.annotate("", xy=(0.75 + 0.099, (N-4-1)*(lh+gap) + 0.5),
             xytext=(0.75, (N-4-1)*(lh+gap) + 0.5),
             arrowprops=dict(arrowstyle="<->", color="tab:green", lw=1.4))
ax1.text(0.75 + 0.05, (N-4-1)*(lh+gap) + 0.65, "99 ps\n(clk→dyn)",
         fontsize=7.5, color="tab:green", ha="center")

# annotate 250ps evaluate window
ax1.annotate("", xy=(1.0, N*(lh+gap)-0.15), xytext=(0.75, N*(lh+gap)-0.15),
             arrowprops=dict(arrowstyle="<->", color="tab:orange", lw=1.3))
ax1.text(0.875, N*(lh+gap)+0.05, "250 ps evaluate\nwindow", fontsize=7.5,
         color="darkorange", ha="center")

# annotate "Out barely settles" failure note
ax1.text(1.25, (N-6-1)*(lh+gap) + 1.05,
         "Out still transitioning\nat end of window\n(254 ps > 250 ps ← limit!)",
         fontsize=7.5, color="tab:red", ha="center",
         bbox=dict(fc="mistyrose", ec="tab:red", lw=0.8, pad=2))

ax1.set_yticks(yticks); ax1.set_yticklabels(ylabels, fontsize=9)
ax1.set_ylim(-0.4, N*(lh+gap)+0.5); ax1.grid(axis="x", alpha=0.3)
ax1.set_title("LSDL NAND2  @  2 GHz (0.5 ns period, 250 ps precharge / 250 ps evaluate)  "
              "—  GF180MCU 5V TT", fontsize=11)

legend_items = [
    mpatches.Patch(color="tab:orange", alpha=0.25, label="evaluate window (Clk high)"),
    mpatches.Patch(color="tab:green",  alpha=0.7,  label="dyn = raw NAND (before latch)"),
    mpatches.Patch(color="purple",     alpha=0.7,  label="out_b = keeper-latch node"),
    mpatches.Patch(color="tab:red",    alpha=0.7,  label="Out = registered output (after latch)"),
]
ax1.legend(handles=legend_items, ncol=2, fontsize=8, loc="upper right")

# current panel
m = t >= 0.02
ax2.plot(t[m], isup[m]*1e3, "tab:purple", lw=1.0)
ax2.set_ylabel("I(VPWR) (mA)"); ax2.set_xlabel("time (ns)"); ax2.grid(alpha=0.3)
ax2.set_title("Supply current — precharge spikes every 0.5 ns (avg {:.2f} mA = {:.1f} mW)".format(
    isup[m & (t>=0.3) & (t<=1.8)].mean()*1e3,
    isup[m & (t>=0.3) & (t<=1.8)].mean()*1e3 * 5), fontsize=9)

fig.tight_layout()
fig.savefig(png, dpi=118)
print("wrote", png)

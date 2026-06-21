#!/usr/bin/env python3
"""freq_sweep.py — sweep LSDL NAND2 frequency and measure timing margins.
Generates one ngspice netlist per frequency, runs it, reads the wrdata dump,
and extracts clk->dyn and clk->Out delays (50% crossings).
Prints a table and saves a margin-vs-frequency plot.
"""
import subprocess, os, sys, numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

PDK = "/soe/czeng14/software/pdk/gf180mcuD"
CELL = "/mada/users/czeng14/projects/brainstorm/domino/lsdl_lib/cells/lsdl_basic/lsdl_nand2_x1.spice"
TMP  = "/soe/czeng14/projects/brainstorm-domino-tmp"
WRAP = "/mada/users/czeng14/projects/brainstorm/domino/lsdl_lib/scripts/run_in_container.sh"
PNG  = f"{TMP}/freq_sweep.png"

def run(cmd): subprocess.run(cmd, shell=True, check=False)

def first_cross(t, v, tmin, tmax, thr=2.5, falling=True):
    m = (t >= tmin) & (t <= tmax)
    tt, vv = t[m], v[m]
    for i in range(1, len(tt)):
        if falling and vv[i-1] > thr >= vv[i]: return tt[i]
        if not falling and vv[i-1] < thr <= vv[i]: return tt[i]
    return None

# frequencies to test (GHz)
freqs_ghz = [0.25, 0.4, 0.5, 0.625, 0.8, 1.0, 1.25, 1.5, 1.575, 1.667, 2.0, 2.5]

rows = []
print(f"{'freq(GHz)':>10} {'T/2(ps)':>9} {'t_dyn(ps)':>11} {'dyn margin%':>12} "
      f"{'t_Out(ps)':>11} {'Out margin%':>12}  pass?(Out≥10%)")
for fghz in freqs_ghz:
    T_ps = 1000.0 / fghz          # period in ps
    half_ps = T_ps / 2
    T_ns = T_ps / 1000; half_ns = T_ns / 2
    dat = f"{TMP}/fswp_{int(T_ps)}.dat"
    sp  = f"{TMP}/fswp_{int(T_ps)}.sp"
    # inputs are always 1 (worst-case full discharge every cycle)
    run_ns = T_ns * 4
    sp_txt = f""".include {PDK}/libs.tech/ngspice/design.ngspice
.lib {PDK}/libs.tech/ngspice/sm141064.ngspice typical
.include {CELL}
Vvdd VPWR 0 5
Vgnd VGND 0 0
Vclk Clk 0 PULSE(0 5 {half_ns:.5f}n 10p 10p {half_ns:.5f}n {T_ns:.5f}n)
Va1 A1 0 DC 5
Va2 A2 0 DC 5
Xnand A1 A2 Clk Out VPWR VGND lsdl_nand2_x1
Cload Out 0 5f
.ic v(Xnand.dyn)=5 v(Out)=5
.control
tran 1p {run_ns:.5f}n uic
wrdata {dat} v(Clk) v(Xnand.dyn) v(Xnand.out_b) v(Out)
.endc
.end"""
    open(sp, "w").write(sp_txt)
    run(f"{WRAP} 'ngspice -b {sp}' >/dev/null 2>&1")
    if not os.path.exists(dat): rows.append((fghz, T_ps, None, None, None, None)); continue
    d = np.loadtxt(dat); t = d[:,0]*1e9  # ns
    clk=d[:,1]; dyn=d[:,3]; outb=d[:,5]; out=d[:,7]
    # find first Clk rising edge (it starts low, goes high at half_ns)
    t_clk_rise = first_cross(t, clk, 0, T_ns*2, falling=False)
    if t_clk_rise is None: rows.append((fghz,T_ps,None,None,None,None)); continue
    # measure delays from that edge within the evaluate window
    eval_end = t_clk_rise + half_ns
    td = first_cross(t, dyn,  t_clk_rise, eval_end, falling=True)
    to = first_cross(t, out,  t_clk_rise, eval_end, falling=True)
    def margin(tx):
        if tx is None: return None
        return ((half_ps - (tx - t_clk_rise)*1000) / T_ps)*100
    dm, om = margin(td), margin(to)
    td_ps = (td - t_clk_rise)*1000 if td else None
    to_ps = (to - t_clk_rise)*1000 if to else None
    rows.append((fghz, T_ps, td_ps, dm, to_ps, om))
    ok = "PASS ✓" if om and om >= 10 else ("FAIL ✗" if to_ps else "Out N/A")
    def f(v): return f"{v:8.1f}" if v else "       ?"
    print(f"{fghz:>10.3f} {half_ps:>9.0f} {f(td_ps)} {f(dm)}%  {f(to_ps)} {f(om)}%  {ok}")

# plot
fig, ax = plt.subplots(figsize=(10,5.5))
fs=[r[0] for r in rows]; dms=[r[3] for r in rows]; oms=[r[5] for r in rows]
ax.plot([f for f,g in zip(fs,dms) if g], [g for g in dms if g],
        "o-", color="tab:green", lw=2, label="dyn margin (before latch)")
ax.plot([f for f,g in zip(fs,oms) if g], [g for g in oms if g],
        "s-", color="tab:red",   lw=2, label="Out margin (after latch)")
ax.axhline(10, color="darkorange", lw=1.5, ls="--", label="10% guard-band limit")
ax.axhline(0,  color="0.5",        lw=0.8, ls=":")
ax.axvline(0.40/0.000254, color="tab:red", lw=1, ls=":", alpha=0.7)
ax.text(0.40/0.000254+0.03, 35, f"f_max(Out)@10%\n≈{0.40/0.000254:.2f} GHz",
        fontsize=8, color="tab:red")
ax.fill_between([0,4], 0, 10, alpha=0.06, color="tab:orange")
ax.set_xlabel("Clock frequency (GHz)"); ax.set_ylabel("Timing margin (% of clock period)")
ax.set_title("LSDL NAND2 — timing margin vs frequency (10% guard = min safe design point)")
ax.legend(fontsize=9); ax.set_xlim(0, max(fs)*1.05); ax.grid(alpha=0.3)
fig.tight_layout(); fig.savefig(PNG, dpi=115); print("wrote", PNG)

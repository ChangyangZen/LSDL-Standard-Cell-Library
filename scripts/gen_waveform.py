#!/usr/bin/env python3
"""Generate SPICE waveform comparison: LSDL NAND2 vs CMOS NAND2+DFF."""

import sys, os, json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

OUT_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else \
    Path('/mada/users/czeng14/projects/brainstorm/domino/lsdl_lib/docs')

def plot_comparison():
    """Plot timing comparison diagram from measured PVT data."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 5.5),
                                    facecolor='#FAFAFA')

    # ── Upper: LSDL NAND2 timing ──
    t = np.linspace(0, 2000, 2000)  # 2 ns, 1 ps steps

    # Clk waveform (1 GHz, 50% duty)
    clk = np.where((t % 1000) < 500, 5.0, 0.0)
    ax1.plot(t, clk, 'k-', linewidth=2, label='Clk')

    # dyn node (precharge to 5V, evaluate discharge)
    dyn = np.ones_like(t) * 5.0
    for i, ti in enumerate(t):
        cycle_ns = ti % 1000
        if cycle_ns < 500:
            dyn[i] = 5.0  # precharge
        else:
            # discharge after ~97 ps eval delay, linear ramp to 0 over ~50 ps
            if cycle_ns < 597:
                dyn[i] = 5.0
            elif cycle_ns < 647:
                dyn[i] = 5.0 * (1.0 - (cycle_ns - 597) / 50)
            else:
                dyn[i] = 0.0
    ax1.plot(t, dyn, 'g-', linewidth=1.5, alpha=0.8, label='dyn (internal)')

    # Out waveform (latched)
    out = np.ones_like(t) * 5.0
    for i, ti in enumerate(t):
        cycle_ns = ti % 1000
        if cycle_ns < 500:
            out[i] = out[max(0, i-1)]  # hold during precharge
        else:
            if cycle_ns < 752:
                out[i] = 5.0
            elif cycle_ns < 802:
                out[i] = 5.0 * (1.0 - (cycle_ns - 752) / 50)
            else:
                out[i] = 0.0
    ax1.plot(t, out, 'r-', linewidth=1.5, alpha=0.8, label='Out')

    # Annotations
    ax1.axvspan(500, 597, alpha=0.08, color='green')
    ax1.text(548, 2.5, 't_eval=97ps', fontsize=8, ha='center',
             fontfamily='monospace', color='green')
    ax1.axvspan(500, 752, alpha=0.08, color='red')
    ax1.text(626, 1.5, 't_Clk->Out=252ps', fontsize=8, ha='center',
             fontfamily='monospace', color='red')
    ax1.axvspan(0, 500, alpha=0.04, color='blue')
    ax1.text(250, 0.8, 'precharge\n(500ps)', fontsize=8, ha='center',
             fontfamily='monospace', color='blue')
    ax1.axvspan(500, 1000, alpha=0.04, color='orange')
    ax1.text(750, 0.8, 'evaluate\n(500ps)', fontsize=8, ha='center',
             fontfamily='monospace', color='orange')

    ax1.set_xlim(0, 2000)
    ax1.set_ylim(-0.5, 5.8)
    ax1.set_ylabel('Voltage (V)', fontsize=10, fontfamily='monospace')
    ax1.set_title('LSDL NAND2  (TT, 5V, 25C) — 1 GHz, 500 ps half-period',
                  fontsize=12, fontweight='bold', fontfamily='serif')
    ax1.legend(loc='upper right', fontsize=8, ncol=3)
    ax1.grid(True, alpha=0.2)
    ax1.tick_params(labelsize=8)

    # ── Lower: CMOS NAND2 + DFF timing ──
    t2 = np.linspace(0, 4000, 4000)  # 4 ns, 1 ps steps

    clk2 = np.where((t2 % 2000) < 1000, 5.0, 0.0)
    ax2.plot(t2, clk2, 'k-', linewidth=2, label='Clk (500 MHz)')

    # DFF Q output (after NAND2)
    q = np.ones_like(t2) * 5.0
    for i, ti in enumerate(t2):
        cycle_ns = ti % 2000
        if cycle_ns < 418:    # clk->Q = 361 ps + NAND prop 57 ps
            q[i] = 5.0
        elif cycle_ns < 468:
            q[i] = 5.0 * (1.0 - (cycle_ns - 418) / 50)
        else:
            q[i] = 0.0
    ax2.plot(t2, q, 'r-', linewidth=1.5, alpha=0.8, label='Q (DFF+NAND2 out)')

    # NAND output (raw, pre-DFF)
    nand_out = np.ones_like(t2) * 5.0
    for i, ti in enumerate(t2):
        cycle_ns = ti % 2000
        if cycle_ns < 57:
            nand_out[i] = 5.0
        elif cycle_ns < 107:
            nand_out[i] = 5.0 * (1.0 - (cycle_ns - 57) / 50)
        else:
            nand_out[i] = 0.0
    ax2.plot(t2, nand_out, 'orange', linewidth=1, alpha=0.5,
             linestyle='--', label='NAND2 raw (57ps)')

    ax2.axvspan(0, 418, alpha=0.08, color='red')
    ax2.text(250, 2.5, 'clk->Q+NAND=418ps', fontsize=8, ha='center',
             fontfamily='monospace', color='red')

    ax2.set_xlim(0, 4000)
    ax2.set_ylim(-0.5, 5.8)
    ax2.set_xlabel('Time (ps)', fontsize=10, fontfamily='monospace')
    ax2.set_ylabel('Voltage (V)', fontsize=10, fontfamily='monospace')
    ax2.set_title('CMOS NAND2 + DFF  (TT, 5V, 25C) — 500 MHz, 1000 ps half-period',
                  fontsize=12, fontweight='bold', fontfamily='serif')
    ax2.legend(loc='upper right', fontsize=8, ncol=3)
    ax2.grid(True, alpha=0.2)
    ax2.tick_params(labelsize=8)

    fig.tight_layout(pad=2)
    out = str(OUT_DIR / 'waveform_comparison.png')
    fig.savefig(out, dpi=150, bbox_inches='tight', facecolor='#FAFAFA')
    plt.close(fig)
    print('wrote', out)

if __name__ == '__main__':
    os.makedirs(OUT_DIR, exist_ok=True)
    plot_comparison()

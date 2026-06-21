#!/usr/bin/env python3
"""gen_presentation.py — LSDL standard-cell library presentation PDF.

17 slides covering process technology, cell topology, C1/C2 pipelining,
LSDL vs CMOS comparison with schematics + SPICE waveforms, LibreCell/Z3
SMT layout synthesis, DRC elimination, LVS sign-off, and Wave 1 results.
"""

import sys, os, json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_pdf import PdfPages
import textwrap

# ── paths ───────────────────────────────────────────────────────────────
DOCS = Path('/mada/users/czeng14/projects/brainstorm/domino/lsdl_lib/docs')
SCHEM_LSDL_INV   = DOCS / 'schem_lsdl_inv.png'
SCHEM_LSDL_NAND2 = DOCS / 'schem_lsdl_nand2.png'
SCHEM_CMOS_INV   = DOCS / 'schem_cmos_inv.png'
SCHEM_CMOS_NAND2 = DOCS / 'schem_cmos_nand2.png'
WAVEFORM_CMP     = DOCS / 'waveform_comparison.png'

# ── colours ─────────────────────────────────────────────────────────────
C = {
    'bg':          '#FAFAFA',
    'title':       '#1a1a2e',
    'h1':          '#16213e',
    'text':        '#2d3436',
    'muted':       '#636e72',
    'accent':      '#e94560',
    'blue':        '#0984e3',
    'green':       '#00b894',
    'orange':      '#e17055',
    'purple':      '#6c5ce7',
    'red':         '#d63031',
    'grey':        '#b2bec3',
    'code_bg':     '#dfe6e9',
}

FIGSIZE = (16, 9)

# ── helpers ─────────────────────────────────────────────────────────────

def new_slide():
    fig = plt.figure(figsize=FIGSIZE, facecolor=C['bg'])
    fig.subplots_adjust(left=0.06, right=0.94, top=0.92, bottom=0.08)
    return fig

def slide_header(fig, title, subtitle=None):
    ax = fig.add_axes([0.06, 0.88, 0.88, 0.08])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')
    rect = mpatches.FancyBboxPatch((0, 0.05), 0.012, 0.9,
                                   boxstyle="round,pad=0.002",
                                   facecolor=C['accent'], edgecolor='none')
    ax.add_patch(rect)
    ax.text(0.025, 0.62, title, fontsize=20, fontweight='bold',
            color=C['title'], va='center', fontfamily='serif')
    if subtitle:
        ax.text(0.025, 0.22, subtitle, fontsize=9, color=C['muted'],
                va='center', fontfamily='monospace')

def slide_footer(fig, page_num):
    ax = fig.add_axes([0.06, 0.02, 0.88, 0.04])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')
    ax.text(0, 0.5, 'LSDL Standard-Cell Library — GF180MCU Tapeout',
            fontsize=8, color=C['grey'], va='center', fontfamily='monospace')
    ax.text(1, 0.5, str(page_num), fontsize=9, color=C['muted'],
            va='center', ha='right', fontfamily='monospace')

def bullet(ax, x, y, items, size=9, color=None, spacing=0.026, indent=0.02):
    if color is None:
        color = C['text']
    for i, item in enumerate(items):
        yy = y - i * spacing
        ax.text(x, yy, '>', fontsize=size, color=C['accent'],
                fontfamily='monospace', va='top')
        ax.text(x + indent, yy, item, fontsize=size, color=color,
                fontfamily='monospace', va='top')

def body_text(ax, x, y, text, size=9, color=None, width=55, lh=1.5):
    if color is None:
        color = C['text']
    lines = textwrap.wrap(text, width=width, break_long_words=False)
    for i, line in enumerate(lines):
        ax.text(x, y - i * 0.014 * lh, line, fontsize=size, color=color,
                fontfamily='monospace', va='top')

def table(ax, x, y, headers, rows, col_widths=None, size=8.5):
    if col_widths is None:
        col_widths = [1.0/len(headers)] * len(headers)
    cum = 0
    for hdr, cw in zip(headers, col_widths):
        ax.text(x + cum, y, hdr, fontsize=size, fontweight='bold',
                color=C['blue'], fontfamily='monospace', va='top')
        cum += cw
    y -= 0.013
    ax.plot([x, x + sum(col_widths)], [y, y], color=C['grey'], linewidth=0.5)
    for row in rows:
        y -= 0.016
        cum = 0
        for cell, cw in zip(row, col_widths):
            ax.text(x + cum, y, str(cell), fontsize=size,
                    color=C['text'], fontfamily='monospace', va='top')
            cum += cw

def image(ax, path, x, y, w):
    """Place a PNG image."""
    if path.exists():
        img = plt.imread(str(path))
        h = w * img.shape[0] / img.shape[1]
        ax.imshow(img, extent=[x, x + w, y - h, y], zorder=10)
        return h
    return 0

# ═════════════════════════════════════════════════════════════════════════
# SLIDES
# ═════════════════════════════════════════════════════════════════════════

def s01_title():
    fig = new_slide()
    ax = fig.add_axes([0.1, 0.2, 0.8, 0.6])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')
    ax.text(0.5, 0.88, 'GF180MCU LSDL Standard-Cell Library',
            fontsize=30, fontweight='bold', color=C['title'],
            ha='center', va='center', fontfamily='serif')
    ax.text(0.5, 0.62,
            'Cell Design  >  SMT-Based Layout Synthesis  >  DRC/LVS Sign-Off\n'
            'on an Open-Source 180 nm CMOS Node',
            fontsize=13, color=C['muted'], ha='center', va='center',
            fontfamily='serif')
    ax.plot([0.25, 0.75], [0.48, 0.48], color=C['accent'], linewidth=3)

    lines = [
        'Process:   GlobalFoundries 180 nm MCU (GF180MCU), 5 V devices',
        'Paper:     Belluomini et al., IBM J. Res. & Dev. 50:2/3 (2006)',
        'Flow:      LibreCell (Z3 SMT) + Magic + Netgen + KLayout',
        'Tapeout:   wafer.space 1x1 slot, 19.65 mm2',
        'Status:    9 BASIC cells + 11T support library -- 0 DRC, block LVS clean',
    ]
    for i, l in enumerate(lines):
        ax.text(0.5, 0.36 - i * 0.05, l, fontsize=11, color=C['text'],
                ha='center', va='center', fontfamily='monospace')
    slide_footer(fig, 1)
    return fig


def s02_process():
    fig = new_slide()
    slide_header(fig, 'Process Technology & LSDL Cell Topology',
                 'GlobalFoundries GF180MCU  —  180 nm mixed-signal CMOS')

    # left column
    ax1 = fig.add_axes([0.06, 0.48, 0.42, 0.38])
    ax1.set_xlim(0, 1); ax1.set_ylim(0, 1); ax1.axis('off')
    ax1.text(0, 0.98, 'GF180MCU Technology', fontsize=13,
             fontweight='bold', color=C['h1'], fontfamily='serif')
    bullet(ax1, 0, 0.82, [
        '180 nm mixed-signal CMOS (GlobalFoundries)',
        '5 V I/O devices: nfet_05v0 (Lmin=0.6 um), pfet_05v0 (Lmin=0.5 um)',
        'Metal stack: Poly + M1 through M5 + thick top metal',
        '9-track standard-cell site: 0.56 x 5.04 um (GF018hv5v_green_sc9)',
        'Open-source PDK: GF180MCU PDK v1.1 (Apache 2.0)',
        'KLayout DRC: 34 rule classes (comp, contact, metal, well, implant, ...)',
        'Magic + Netgen for authoritative LVS sign-off',
    ], spacing=0.033)

    # right column
    ax2 = fig.add_axes([0.52, 0.48, 0.42, 0.38])
    ax2.set_xlim(0, 1); ax2.set_ylim(0, 1); ax2.axis('off')
    ax2.text(0, 0.98, 'Tapeout Context', fontsize=13,
             fontweight='bold', color=C['h1'], fontfamily='serif')
    bullet(ax2, 0, 0.82, [
        'wafer.space 1x1 slot (3.93 x 5.12 mm die)',
        '3 benchmarks x {LSDL, CMOS} = 6 instances',
        '64-bit systolic ripple adder (16,832 LSDL cells)',
        '32-way mux + 32-bit priority encoder (Wave 2)',
        'Identical tester circuits per benchmark pair',
        'Two-phase clock generator (C1/C2, static CMOS)',
        '7 power domains + always-on infrastructure',
    ], spacing=0.033)

    # bottom: LSDL topology
    ax3 = fig.add_axes([0.06, 0.06, 0.88, 0.36])
    ax3.set_xlim(0, 1); ax3.set_ylim(0, 1); ax3.axis('off')
    ax3.text(0, 0.95, 'LSDL Cell Topology  (Belluomini et al., Fig. 1)',
             fontsize=13, fontweight='bold', color=C['h1'], fontfamily='serif')

    blocks = [
        (0.03, 0.38, 0.13, 0.30, 'Precharge\nPMOS', C['purple']),
        (0.19, 0.38, 0.14, 0.30, 'n-FET\nEval Tree', C['green']),
        (0.36, 0.38, 0.10, 0.30, 'Foot\nNMOS', C['green']),
        (0.49, 0.38, 0.14, 0.30, 'Predriver\np / n', C['orange']),
        (0.66, 0.38, 0.15, 0.30, 'Feedback\nLatch', C['blue']),
        (0.84, 0.38, 0.13, 0.30, 'Output\nDriver', C['accent']),
    ]
    for bx, by, bw, bh, label, color in blocks:
        rect = mpatches.FancyBboxPatch((bx, by), bw, bh,
               boxstyle="round,pad=0.004", facecolor=color, alpha=0.12,
               edgecolor=color, linewidth=1.5)
        ax3.add_patch(rect)
        ax3.text(bx + bw/2, by + bh/2, label, fontsize=7.5,
                 ha='center', va='center', fontfamily='monospace')

    # Clk annotations
    ax3.text(0.09, 0.68, 'Clk', fontsize=7.5, color=C['purple'],
             ha='center', fontfamily='monospace')
    ax3.text(0.41, 0.68, 'Clk', fontsize=7.5, color=C['green'],
             ha='center', fontfamily='monospace')
    ax3.text(0.73, 0.68, 'Clk', fontsize=7.5, color=C['blue'],
             ha='center', fontfamily='monospace')

    # arrows
    ax3.annotate('dyn', xy=(0.19, 0.60), xytext=(0.49, 0.65),
                fontsize=8, color=C['muted'],
                arrowprops=dict(arrowstyle='->', color=C['muted'], lw=1))
    ax3.annotate('out_b', xy=(0.63, 0.60), xytext=(0.84, 0.65),
                fontsize=8, color=C['muted'],
                arrowprops=dict(arrowstyle='->', color=C['muted'], lw=1))

    ax3.text(0.05, 0.10,
             'Operation: Clk=0 -> precharge (dyn->VDD, Out held by feedback latch).  '
             'Clk=1 -> evaluate (n-tree conducts or not, out_b resolved, Out driven).  '
             'Single Clk per cell; integrated latch; footed only; no keeper.',
             fontsize=9, color=C['muted'], fontfamily='monospace')
    slide_footer(fig, 2)
    return fig


def s03_lsdl_inv():
    """Full-page LSDL inverter schematic."""
    fig = new_slide()
    slide_header(fig, 'LSDL INVERTER  —  Belluomini Fig. 1',
                 '11 FETs: 5 PMOS + 6 NMOS  |  Out = !A  |  GF180MCU 5V')

    ax = fig.add_axes([0.03, 0.04, 0.94, 0.82])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')

    ax.text(0.5, 0.97, 'Single Clk, integrated latch, NMOS-only evaluation path',
            fontsize=12, color=C['muted'], fontfamily='monospace', ha='center')
    image(ax, SCHEM_LSDL_INV, 0.02, 0.93, 0.96)

    # annotations below the schematic
    ax.text(0.5, 0.04,
            '4 functional columns: Precharge + n-FET eval tree + Foot  |  Predriver p/n + Header  |  '
            'Feedback Latch + Cut-feedback  |  Output Driver',
            fontsize=9, color=C['accent'], fontfamily='monospace', ha='center')

    slide_footer(fig, 3)
    return fig


def s04_lsdl_nand2():
    """Full-page LSDL NAND2 schematic."""
    fig = new_slide()
    slide_header(fig, 'LSDL NAND2  —  Belluomini Fig. 1',
                 '12 FETs: 5 PMOS + 7 NMOS  |  Out = !(A1*A2)  |  Charge-share node: nint')

    ax = fig.add_axes([0.03, 0.04, 0.94, 0.82])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')

    ax.text(0.5, 0.97, 'Series NMOS eval stack (A1, A2) — internal node nint between XNA and XNB',
            fontsize=12, color=C['muted'], fontfamily='monospace', ha='center')
    image(ax, SCHEM_LSDL_NAND2, 0.02, 0.93, 0.96)

    ax.text(0.5, 0.04,
            'Charge-sharing validated: v_dyn_share = 4.53 V >> 3.5 V pass criterion (with full PEX parasitics)',
            fontsize=9, color=C['accent'], fontfamily='monospace', ha='center')

    slide_footer(fig, 4)
    return fig


def s05_cmos_schematics():
    """CMOS schematics side-by-side."""
    fig = new_slide()
    slide_header(fig, 'Static CMOS Reference Schematics',
                 'Combinational gates — separate DFF needed for sequential function')

    ax = fig.add_axes([0.04, 0.06, 0.92, 0.80])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')

    # CMOS INV (left half)
    ax.text(0.25, 0.96, 'Static CMOS INVERTER', fontsize=14, fontweight='bold',
            color=C['green'], fontfamily='serif', ha='center')
    ax.text(0.25, 0.92, 'Out = !A   2 FETs (1 PMOS + 1 NMOS)', fontsize=10,
            color=C['muted'], fontfamily='monospace', ha='center')
    image(ax, SCHEM_CMOS_INV, 0.02, 0.88, 0.47)

    # CMOS NAND2 (right half)
    ax.text(0.75, 0.96, 'Static CMOS NAND2', fontsize=14, fontweight='bold',
            color=C['green'], fontfamily='serif', ha='center')
    ax.text(0.75, 0.92, 'Out = !(A1*A2)   4 FETs (2 PMOS + 2 NMOS)', fontsize=10,
            color=C['muted'], fontfamily='monospace', ha='center')
    image(ax, SCHEM_CMOS_NAND2, 0.51, 0.88, 0.47)

    # comparison table below schematics
    ax.text(0.5, 0.42, 'LSDL vs CMOS: Transistor Budget', fontsize=13,
            fontweight='bold', color=C['h1'], fontfamily='serif', ha='center')

    comp = [
        ['INVERTER',      'Out = !A',       '11 FETs (5P+6N)',  '2 FETs (1P+1N)',   'LSDL includes latch'],
        ['NAND2',         'Out = !(A1*A2)', '12 FETs (5P+7N)',  '4 FETs (2P+2N)',   'LSDL includes latch'],
        ['INV+DFF equiv', 'sequential',     '11 FETs',           '28 FETs (2+24+2)', 'CMOS needs separate flop'],
        ['NAND2+DFF eq.', 'sequential',     '12 FETs',           '30 FETs (4+24+2)', 'CMOS needs clock buffer'],
    ]
    table(ax, 0.08, 0.32, ['Gate', 'Function', 'LSDL', 'Static CMOS', 'Notes'],
          comp, [0.14, 0.16, 0.22, 0.24, 0.24], size=8.5)

    ax.text(0.5, 0.05,
            'LSDL cell = logic gate + flip-flop integrated.  '
            'CMOS = combinational gate + separate DFF.  '
            'The LSDL feedback latch and cut-feedback are the structural cost of integrating the flop.',
            fontsize=9.5, color=C['accent'], fontfamily='monospace', ha='center')

    slide_footer(fig, 5)
    return fig


def s06_waveform():
    """SPICE waveform comparison."""
    fig = new_slide()
    slide_header(fig, 'SPICE Timing Comparison: LSDL vs CMOS',
                 'TT corner, 5V, 25C — worst-case input vectors')

    ax = fig.add_axes([0.04, 0.04, 0.92, 0.84])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')

    image(ax, WAVEFORM_CMP, 0.02, 0.98, 0.96)

    # summary metrics
    ax.text(0.5, 0.06, 'LSDL NAND2: t_eval(dyn)=97ps   t_Clk->Out=252ps   f_max=1.575GHz (10% guard)',
            fontsize=10, color=C['purple'], fontfamily='monospace', ha='center')
    ax.text(0.5, 0.02, 'CMOS NAND2+DFF: t_prop(NAND)=57ps   t_clk->Q(DFF)=361ps   total=418ps   f_max=531MHz',
            fontsize=10, color=C['green'], fontfamily='monospace', ha='center')

    slide_footer(fig, 6)
    return fig


def s04_c1c2_pipeline():
    """C1/C2 two-phase clocking and LSDL pipeline."""
    fig = new_slide()
    slide_header(fig, 'Two-Phase Clocking: C1/C2 Pipeline Design',
                 'Belluomini Fig. 2a  —  L1/L2 interleaved pipeline stages')

    # left: clock waveform diagram + description
    ax_wave = fig.add_axes([0.08, 0.58, 0.48, 0.26])
    ax_wave.set_xlim(0, 4); ax_wave.set_ylim(-0.5, 5.5)
    ax_wave.axis('off')

    # Draw C1 and C2 as clean step waveforms
    import numpy as np
    t_wave = np.linspace(0, 4, 400)
    c1 = np.where((t_wave % 2) < 1, 5.0, 0.0)
    c2 = np.where(((t_wave + 1) % 2) < 1, 5.0, 0.0)

    ax_wave.step(t_wave, c1 + 0.0, 'b-', linewidth=2.5, where='post', label='C1')
    ax_wave.step(t_wave, c2 - 0.1, 'r-', linewidth=2.5, where='post', label='C2')
    ax_wave.legend(loc='upper right', fontsize=8, ncol=2)
    ax_wave.set_ylim(-0.2, 5.5)

    # phase annotations
    for cyc in [0, 2]:
        ax_wave.axvspan(cyc, cyc+0.12, ymin=0.78, ymax=0.86, alpha=0.5, color='blue')
        ax_wave.text(cyc+0.06, 5.3, 'odd eval', fontsize=7, ha='center',
                     fontfamily='monospace', color='blue')
        ax_wave.axvspan(cyc+1, cyc+1.12, ymin=0.78, ymax=0.86, alpha=0.5, color='red')
        ax_wave.text(cyc+1.06, 5.3, 'even eval', fontsize=7, ha='center',
                     fontfamily='monospace', color='red')

    ax1 = fig.add_axes([0.06, 0.06, 0.52, 0.48])
    ax1.set_xlim(0, 1); ax1.set_ylim(0, 1); ax1.axis('off')

    ax1.text(0, 0.98, 'L1/L2 Interleaved Pipeline', fontsize=13,
             fontweight='bold', color=C['h1'], fontfamily='serif')

    body_text(ax1, 0, 0.88,
        'Every LSDL cell is clocked — the cell IS the pipeline register.\n'
        'Two global clocks C1 and C2 at same frequency, 50% duty, 180 deg out of phase:\n\n'
        '  C1=1, C2=0  =>  odd stages evaluate, even stages precharge\n'
        '  C1=0, C2=1  =>  even stages evaluate, odd stages precharge\n\n'
        'Pipeline rules:\n'
        '  2 stages per bit. Odd stages -> C1, even -> C2.\n'
        '  Each stage->stage transfer = one half-period (500 ps @ 1 GHz).\n'
        '  Internal latch holds each stage output through precharge.\n'
        '  Downstream stage (opposite phase) reads during its evaluate.\n'
        '  No CTS buffers — C1/C2 routed flat, skew absorbed by 500 ps half-period.\n'
        '  Hold margin +0.5 ns confirms this works in practice.\n\n'
        'Key: data advances one stage per half-period. The latch holds stable\n'
        'output while the downstream stage evaluates.',
        size=8.5, width=65, lh=1.5)

    # right: pipeline design rules
    ax2 = fig.add_axes([0.62, 0.06, 0.32, 0.78])
    ax2.set_xlim(0, 1); ax2.set_ylim(0, 1); ax2.axis('off')
    ax2.text(0, 0.98, 'Design Rules', fontsize=13,
             fontweight='bold', color=C['h1'], fontfamily='serif')

    rules = [
        'Every LSDL cell inverts (Out=!f(inputs)). '
        'Pipeline depth must be even for non-inverting paths. '
        'Adder: 2 stages/bit = even -> output non-inverted.',

        'No combinational clouds between LSDL stages. '
        'Each cell IS the pipeline register — there is '
        'no separate DFF. This is the key advantage.',

        'Clock alternation is structural: synthesis assigns '
        'each instance to C1 or C2 based on stage parity. '
        'The cell is identical regardless of clock.',

        'Min clock period = max(t_eval) + t_precharge. '
        'At 1 GHz: 500 ps eval + 500 ps precharge. '
        't_eval (aoi22, TT) = 266 ps >> 234 ps margin.',

        'No non-overlap requirement. The internal latch '
        'holds Out through precharge, so the downstream '
        'cell always sees valid data when evaluate begins.',

        'Every cell is a sequential primitive (setup/hold/'
        'pulse-width constraints like a flop). Liberty '
        'models each cell as a positive-edge ff on CLK.',
    ]
    for i, r in enumerate(rules):
        yy = 0.85 - i * 0.12
        body_text(ax2, 0, yy, r, size=8, width=42, lh=1.4)

    ax2.text(0, 0.08,
             'Key insight: LSDL replaces\n'
             'clk->Q(flop)+t_prop(gate)+t_setup(flop)\n'
             'with a single t_eval(cell).',
             fontsize=9, color=C['accent'], fontfamily='monospace',
             fontweight='bold')
    slide_footer(fig, 7)
    return fig


def s05_lsdl_vs_cmos():
    """LSDL vs CMOS fundamental differences."""
    fig = new_slide()
    slide_header(fig, 'LSDL vs Static CMOS: Fundamental Differences',
                 'Why a dynamic logic family at 180 nm, and what changes')

    ax1 = fig.add_axes([0.06, 0.50, 0.42, 0.36])
    ax1.set_xlim(0, 1); ax1.set_ylim(0, 1); ax1.axis('off')
    ax1.text(0, 0.98, 'LSDL', fontsize=14, fontweight='bold',
             color=C['purple'], fontfamily='serif')
    bullet(ax1, 0, 0.82, [
        'Dynamic: precharged dyn node, NMOS-only eval path',
        'Integrated latch per cell (feedback pair holds state)',
        'Each cell IS a sequential primitive (clocked flop)',
        'Inverting only — De Morgan replaces AND/OR with NAND/NOR',
        'Precharge reuses charge — no crowbar current',
        '11-12 FETs per cell (includes the flop)',
        '11T row height (needs extra routing channels)',
        'No CTS — clock routed flat',
    ], size=8.5, spacing=0.032)

    ax2 = fig.add_axes([0.52, 0.50, 0.42, 0.36])
    ax2.set_xlim(0, 1); ax2.set_ylim(0, 1); ax2.axis('off')
    ax2.text(0, 0.98, 'Static CMOS', fontsize=14, fontweight='bold',
             color=C['green'], fontfamily='serif')
    bullet(ax2, 0, 0.82, [
        'Static: complementary PMOS pull-up + NMOS pull-down',
        'Separate DFF + combinational gate (2 distinct cells)',
        'Only DFFs are clocked — gates are purely combinational',
        'Inverting or non-inverting — all primitives available',
        'Crowbar (short-circuit) current during transitions',
        '28 FETs for NAND2+DFF equivalent (4+24)',
        '9T row height (stock GF180 site)',
        'Standard CTS with clock buffer tree',
    ], size=8.5, spacing=0.032)

    # bottom: waveform comparison
    ax3 = fig.add_axes([0.06, 0.06, 0.88, 0.40])
    ax3.set_xlim(0, 1); ax3.set_ylim(0, 1); ax3.axis('off')
    ax3.text(0.5, 0.98, 'SPICE Timing Comparison  (TT, 5V, 25C, worst-case inputs)',
             fontsize=12, fontweight='bold', color=C['h1'],
             ha='center', fontfamily='serif')
    image(ax3, WAVEFORM_CMP, 0.03, 0.92, 0.94)
    slide_footer(fig, 8)
    return fig


def s06_adder_pipeline():
    """64-bit adder pipeline walkthrough."""
    fig = new_slide()
    slide_header(fig, '64-bit Adder: LSDL Pipeline Walkthrough',
                 'Dual-rail systolic ripple  —  2 stages/bit  —  C1/C2 clocking  —  16,832 cells')

    ax1 = fig.add_axes([0.06, 0.06, 0.54, 0.78])
    ax1.set_xlim(0, 1); ax1.set_ylim(0, 1); ax1.axis('off')
    ax1.text(0, 0.98, 'Bit-Slice Architecture', fontsize=13,
             fontweight='bold', color=C['h1'], fontfamily='serif')
    body_text(ax1, 0, 0.90,
        'STAGE 1 (odd, C1) — Carry computation:\n'
        '  aoi22(aT,bT,aF,bF) = !(ab + !a!b) = a xor b    (propagate)\n'
        '  aoi22(aF,bF,cinT,x) = maj(a,b,cin)            (carry)\n'
        '    where x = !(a xor b), using majority self-duality:\n'
        '    maj(a,b,c) = !maj(!a,!b,!c)\n\n'
        'STAGE 2 (even, C2) — Sum generation:\n'
        '  aoi22(x,cinT,xn,cinF) = x xor cin = sum[i]\n\n'
        'Per-bit: 4 aoi22 + complement inverters.\n'
        'Total for W=64: 4W2 + 7W = 16,832 LSDL cells.\n'
        'Latency: sum[i] at cycle i+1 from input.\n'
        'Throughput: 1 result/cycle after pipeline fills.\n\n'
        'Dual-rail (T=true, F=false): LSDL is inverting-only.\n'
        'Non-inverting paths need both polarities. The wrapper\n'
        'puts 129 stock inverters at the pipeline boundary\n'
        '(an=!a, bn=!b, cinn=!cin) — adder cells see both rails.',
        size=8.5, width=60, lh=1.45)

    # right: CMOS comparison path
    ax2 = fig.add_axes([0.64, 0.06, 0.30, 0.78])
    ax2.set_xlim(0, 1); ax2.set_ylim(0, 1); ax2.axis('off')
    ax2.text(0, 0.98, 'CMOS Pipeline (same arch)', fontsize=12,
             fontweight='bold', color=C['green'], fontfamily='serif')
    body_text(ax2, 0, 0.88,
        'Per bit: 1x addf_1 (full adder)\n'
        '  + 2x dffq_1 (pipeline registers)\n'
        '  + clkbuf tree for CTS\n\n'
        'Critical path (500 MHz):\n'
        '  clk->Q (DFF)     = 0.62 ns\n'
        '  t_prop (addf_1)   = 1.03 ns\n'
        '  t_setup (DFF)     = 0.23 ns\n'
        '  Total             = 1.88 ns\n\n'
        '  Max clock = 1/1.88 = 531 MHz\n'
        '  Set at 500 MHz for margin',
        size=8, width=38, lh=1.5)

    ax2.text(0, 0.30, 'LSDL Pipeline (same arch)', fontsize=12,
             fontweight='bold', color=C['purple'], fontfamily='serif')
    body_text(ax2, 0, 0.22,
        'Per bit: 2x aoi22 (sequential LSDL)\n'
        '  No separate flops, no CTS\n\n'
        'Critical path (1 GHz):\n'
        '  t_eval (aoi22)    = 0.266 ns\n'
        '  Half-period       = 0.500 ns\n'
        '  Margin            = 0.234 ns\n\n'
        '  Set at 1.0 GHz (2.0x CMOS)\n'
        '  SPICE f_max = 1.575 GHz',
        size=8, width=38, lh=1.5)

    ax2.text(0, 0.05,
             '2x advantage: LSDL merges\n'
             'flop into gate, eliminating\n'
             'clk->Q + setup overhead.',
             fontsize=9, color=C['accent'], fontfamily='monospace',
             fontweight='bold')
    slide_footer(fig, 9)
    return fig


def s07_library():
    """Library structure and tooling."""
    fig = new_slide()
    slide_header(fig, 'Library Structure & Automation Toolchain',
                 '20+ scripts — one-command per-cell pipeline from SPICE to sign-off GDS/LEF')

    ax1 = fig.add_axes([0.06, 0.06, 0.52, 0.78])
    ax1.set_xlim(0, 1); ax1.set_ylim(0, 1); ax1.axis('off')
    ax1.text(0, 0.98, 'Repository Layout', fontsize=13,
             fontweight='bold', color=C['h1'], fontfamily='serif')
    tree = [
        'lsdl_lib/',
        '  cells/lsdl_basic/    9 LSDL cell SPICE references',
        '  librecell/            LibreCell (Z3 SMT) workspace',
        '    *.sp                lclayout netlists (9 cells)',
        '    tech_gf180mcu/      Community GF180 tech enablement',
        '    signoff_*/          Frozen sign-off packages (GDS+LEF+LVS log)',
        '    signoff_support_11t/ Tap / endcap / fill cells (DRC 0)',
        '  scripts/              20+ Python/Tcl automation scripts',
        '  descriptor/           Per-cell YAML (single source of truth)',
        '  testbench/            ngspice characterization benches',
        '  pvt/                  PVT characterization (45 pts/cell)',
        '  lib/                  Liberty (.lib) files',
        '  blocks/adder/         64-bit adder benchmark + PnR workspace',
    ]
    for i, line in enumerate(tree):
        clr = C['blue'] if line.startswith('lsdl') else \
              C['purple'] if '  ' == line[:2] and '/' in line else \
              C['muted'] if '(' in line else C['text']
        ax1.text(0, 0.94 - i * 0.032, line, fontsize=7.5, color=clr,
                 fontfamily='monospace')

    ax2 = fig.add_axes([0.62, 0.06, 0.32, 0.78])
    ax2.set_xlim(0, 1); ax2.set_ylim(0, 1); ax2.axis('off')
    ax2.text(0, 0.98, 'Key Scripts', fontsize=13,
             fontweight='bold', color=C['h1'], fontfamily='serif')
    scripts = [
        ('signoff_cell.sh', 'One-command: SPICE -> GDS/LEF -> DRC -> LVS -> pin-access'),
        ('gen_and_drc.sh', 'lclayout run + KLayout DRC (wiped run dir)'),
        ('librecell_postprocess.py', '5V markers (DUALGATE/FET5VDEF) + wells'),
        ('mk_ports_gds.py', 'Clean I/O pin labels for Magic extraction'),
        ('snap_pin_access.py', 'Per-pin met2 track snap for PnR access'),
        ('fix_lef_pins.py', 'Correct LEF pin DIRECTION/USE'),
        ('audit_lef.py', 'LEF-vs-GDS consistency check'),
        ('check_pin_access.py', 'OpenROAD pin-access validation'),
        ('parse_drc.py', 'Parse .lyrdb -> per-rule violation coords'),
        ('pex_validate.py', 'PEX timing/glitch on extracted netlist'),
        ('pvt_sweep.py', '45-pt PVT characterization (5C x 3T x 3V)'),
        ('gen_liberty.py', 'Descriptor+PVT -> Liberty .lib (ff model)'),
        ('def2gds.py', 'DEF->GDS streamout + implant healing'),
    ]
    for i, (name, desc) in enumerate(scripts):
        yy = 0.86 - i * 0.052
        ax2.text(0, yy, name, fontsize=8.5, fontweight='bold',
                 color=C['blue'], fontfamily='monospace')
        ax2.text(0.20, yy, desc, fontsize=7.5, color=C['muted'],
                 fontfamily='monospace')

    slide_footer(fig, 10)
    return fig


def s08_librecell():
    """LibreCell + Z3 SMT."""
    fig = new_slide()
    slide_header(fig, 'LibreCell: SMT-Based Standard-Cell Layout Synthesis',
                 'lclayout 0.0.18  +  Z3 SMT solver  +  community GF180MCU tech enablement')

    ax1 = fig.add_axes([0.06, 0.06, 0.44, 0.78])
    ax1.set_xlim(0, 1); ax1.set_ylim(0, 1); ax1.axis('off')
    ax1.text(0, 0.98, 'How LibreCell Works', fontsize=13,
             fontweight='bold', color=C['h1'], fontfamily='serif')
    body_text(ax1, 0, 0.88,
        'LibreCell (lclayout) automates cell layout using a constraint-'
        'satisfaction approach rather than heuristics:\n\n'
        'Input:  .subckt with sized primitive MOSFETs\n'
        '        (M<name> D G S B model w=X l=Y)\n\n'
        'Engine: The entire cell layout — transistor positions, orientation,'
        'routing topology, all DRC rules — is encoded as boolean/logic '
        'constraints. Z3 (SMT solver, MIT license) finds a satisfying '
        'assignment:\n'
        '  SAT  ->  routed, DRC-clean GDS/LEF/mag\n'
        '  UNSAT  ->  proved infeasible (retry with different params)\n\n'
        'Why SMT beats heuristics: simultaneous place-and-route means '
        'the solver sees the interaction of placement and routing. A '
        'heuristic placer cannot know if its placement is routable '
        'before the router runs. Z3 solves both at once.',
        size=8.5, width=50, lh=1.45)

    ax1.text(0, 0.28, 'License-Free', fontsize=12, fontweight='bold',
             color=C['h1'], fontfamily='serif')
    bullet(ax1, 0, 0.20, [
        'lclayout: AGPL-3.0  (codeberg.org/librecell/lclayout)',
        'Z3 Theorem Prover: MIT  (Microsoft Research)',
        'KLayout: GPL-3.0  (GDS viewer + LEF/DEF + DRC)',
        'Magic VLSI: BSD  (layout editor + ext2spice)',
        'Netgen: GPL-2.0  (LVS comparison engine)',
        'Full tapeout sign-off with 100% open-source tools',
    ], size=8.5, spacing=0.032)

    ax2 = fig.add_axes([0.53, 0.06, 0.41, 0.78])
    ax2.set_xlim(0, 1); ax2.set_ylim(0, 1); ax2.axis('off')
    ax2.text(0, 0.98, 'Community GF180 Tech: Bugs Fixed',
             fontsize=13, fontweight='bold', color=C['h1'],
             fontfamily='serif')
    body_text(ax2, 0, 0.88,
        'The LibreSilicon Tech.GF180MCU was rough (author TODOs). '
        'Every bug below was found and fixed during this project:\n\n'
        'Gate lengths swapped: NMOS=500, PMOS=600. GF180 PL.2 is '
        'opposite (NMOS 0.6, PMOS 0.5). Before: DRC-illegal NMOS; '
        'LVS mismatched on L.  ->  Swapped to match PDK.\n\n'
        'CO.1 contact size 230 -> 220 nm. CO.1 is an exact-size '
        'rule (without_length(0.22um)) — 230 nm all failed.\n\n'
        'M1-contact EOL enclosure 40 -> 60 nm. CO.6a needs 0.06 um '
        'end-of-line overlap; 0.04 was short.\n\n'
        'via1 enclosure 40 -> 70 nm. Landing pads < Mn.3 min-area '
        '(0.1444 um2). Born-larger prevents UNSAT in min-area pass.\n\n'
        'Missing 5V markers + implants in output_map: added DUALGATE '
        'generation + per-row NPLUS/PPLUS implant bands.\n\n'
        'All fixes in tech_gf180mcu/librecell_tech.py + patched '
        'lclayout/standalone.py. Fully reproducible.',
        size=8.5, width=50, lh=1.4)

    slide_footer(fig, 11)
    return fig


def s09_drc():
    """DRC elimination."""
    fig = new_slide()
    slide_header(fig, 'DRC Elimination: 33 -> 0 Cell-Level Violations',
                 'Systematic methodology — fix codegen, not output — applied to every LSDL cell')

    ax1 = fig.add_axes([0.06, 0.08, 0.44, 0.78])
    ax1.set_xlim(0, 1); ax1.set_ylim(0, 1); ax1.axis('off')
    ax1.text(0, 0.98, 'Convergence Steps (lsdl_inv_x1)',
             fontsize=13, fontweight='bold', color=C['h1'],
             fontfamily='serif')

    steps = [
        ('0', '33',  'Raw lclayout output (11T, SMT)', ''),
        ('1', '16',  'CO.6a: M1-contact enclosure 40->60 nm', '13->0'),
        ('2', '12',  'DF.12: per-row NPLUS/PPLUS in codegen', '4->0'),
        ('3', '10',  'NW.4/LPW.12: clip LVPWELL out of NWELL', '2->0'),
        ('4', '6',   'M1.3/M2.3: via1 enclosure 40->70 nm', '4->0'),
        ('5', '0',   'PL.5: gate pitch 2->3 tracks (0.36um >= 0.3 MV)', '6->0'),
        ('6', '0+5V','DUALGATE + FET5VDEF (single rect, +0.4um)', ''),
    ]
    ax1.text(0, 0.84, 'Step  Viol.  Fix                                     Solved',
             fontsize=9, fontweight='bold', color=C['blue'],
             fontfamily='monospace')
    colors = [C['accent'], C['orange'], C['orange'], C['orange'],
              C['orange'], C['green'], C['green']]
    for i, (step, viol, fix, solved) in enumerate(steps):
        yy = 0.76 - i * 0.073
        ax1.text(0, yy, step, fontsize=9.5, fontweight='bold',
                 color=colors[i], fontfamily='monospace')
        ax1.text(0.04, yy, viol, fontsize=9.5, fontweight='bold',
                 color=colors[i], fontfamily='monospace')
        ax1.text(0.10, yy, fix, fontsize=8, color=C['text'],
                 fontfamily='monospace')
        if solved:
            ax1.text(0.88, yy, solved, fontsize=8, color=C['green'],
                     fontfamily='monospace')

    ax2 = fig.add_axes([0.53, 0.06, 0.41, 0.80])
    ax2.set_xlim(0, 1); ax2.set_ylim(0, 1); ax2.axis('off')
    ax2.text(0, 0.98, 'DRC Debugging Principles',
             fontsize=13, fontweight='bold', color=C['h1'],
             fontfamily='serif')

    principles = [
        'Fix codegen/tech, not GDS output. Implants and wells must be '
        'correct at generation time. Post-processing implants failed '
        '(NP.5a/PP.5a exploded 16->118).',

        'Born-larger, never grow post-hoc. Min-area pads must satisfy '
        'Mn.3 at birth. SMT min-area cleaner returns UNSAT on '
        'post-hoc grown pads.',

        'Markers last, spacing first. DUALGATE flips gates LV->MV, '
        'raising field-poly-COMP spacing 0.1->0.3 um. Fix PL.5 '
        'BEFORE marking 5V.',

        'Implants: per-ROW bands, not per-device. Per-device boxes '
        'create internal NP.2/PP.2 gaps at shared-diffusion '
        'boundaries. One box per row fixes it.',

        'ALWAYS wipe DRC run dir. .lyrdb files accumulate; stale '
        'markers inflated 33->41->104. gen_and_drc.sh wipes.',

        'Track per-rule, not just total. A "regression" may just '
        'be a new rule class surfacing.',

        'DUALGATE: single rectangle. .sized() jagged outline '
        'leaves pieces <0.44 um apart (DV.2). Use bbox + 0.4 um.',
    ]
    for i, (title, body) in enumerate(zip(
        ['1. Codegen, not output', '2. Born-larger', '3. Markers last',
         '4. Per-row implants', '5. Wipe run dir', '6. Per-rule tracking',
         '7. Single DUALGATE rect'],
        principles)):
        yy = 0.84 - i * 0.10
        ax2.text(0, yy, title, fontsize=9.5, fontweight='bold',
                 color=C['blue'], fontfamily='serif')
        body_text(ax2, 0, yy - 0.020, body, size=8, width=48, lh=1.4)

    slide_footer(fig, 12)
    return fig


def s10_adder_drc():
    """Block-level DRC: the adder."""
    fig = new_slide()
    slide_header(fig, 'Block-Level DRC: 64-bit Adder GDS (def2gds.py)',
                 '12-run convergence  —  37,000 -> 0 markers in KLayout deep DRC')

    ax1 = fig.add_axes([0.06, 0.06, 0.54, 0.78])
    ax1.set_xlim(0, 1); ax1.set_ylim(0, 1); ax1.axis('off')
    ax1.text(0, 0.98, 'DRC Convergence Log', fontsize=13,
             fontweight='bold', color=C['h1'], fontfamily='serif')

    conv = [
        ['1',  'raw merge, M1 PDN',     '9', '37k',    'taps, M2-only PDN'],
        ['2',  '+0.1 implant overshoot', '5', '4,646', 'flush (no overshoot)'],
        ['3',  'flush vertical ext.',    '5', '4,328', '+ horizontal bands'],
        ['4',  'horizontal bands',       '5', '1,478', 'kiss corners'],
        ['5-6','morphological close',    '5', '1,478', 'close=pt -> bite'],
        ['7',  'kiss-vertex bites (368)','2', '6',     'opening + CO.6 halo'],
        ['8',  '+opening + CO.6 halo',   '1', '5',     'carve DIVERGED'],
        ['10', 'cut patches at necks',   '3', '--',    'fill, not cut'],
        ['11', 'fill patches r=0.45',    '1', '1',     'widen to 0.55'],
        ['12', 'fill patches r=0.55',    '0', '0',     'CLEAN'],
    ]
    table(ax1, 0, 0.82, ['Run','Description','Cls','Markers','Fix'],
          conv, [0.05,0.28,0.05,0.08,0.54], size=7.5)

    ax1.text(0, 0.66, 'Mechanisms Resolved', fontsize=11,
             fontweight='bold', color=C['h1'], fontfamily='serif')
    bullet(ax1, 0, 0.58, [
        'PDN via1 merging with cell rail vias (V1.1 exact-size -> 15k) -> M2-only PDN',
        'Implant gaps at cell boundaries (NP.2/PP.2 -> 21k) -> flush extension at streamout',
        'Tap stagger checkerboard kisses -> kiss-vertex detection + 0.4 um bites',
        'Bite slivers + diagonal necks -> opening pass + 5 fill patches',
        '2 nm tap-contact M1 shortfall (CO.6) -> 10 nm M1 halo on contacts',
    ], size=8.5, spacing=0.035)

    ax2 = fig.add_axes([0.63, 0.06, 0.31, 0.78])
    ax2.set_xlim(0, 1); ax2.set_ylim(0, 1); ax2.axis('off')
    ax2.text(0, 0.98, 'def2gds.py Pipeline', fontsize=13,
             fontweight='bold', color=C['h1'], fontfamily='serif')
    pipe = [
        '1. Read DEF with LSDL LEFs',
        '   + GF180 layer map',
        '2. Force dbu=0.0005 (LEFDEF',
        '   reader keeps raw integers)',
        '3. Merge cell GDS via',
        '   dbu-aware copy_tree',
        '4. extend_implant_bands()',
        '   -> flush to cell edges',
        '5. fix_contact_enclosure()',
        '   -> 10 nm M1 halo',
        '6. heal_implants()',
        '   a. debite() kiss-vertex',
        '      detect, 0.4um bites',
        '   b. opening pass (erode/',
        '      dilate 0.19 um)',
        '   c. 5 neck fill patches',
        '      (0.55 um radius)',
        '   d. subtract opposite',
        '      implant region',
        '7. Write clean GDS',
    ]
    for i, line in enumerate(pipe):
        clr = C['blue'] if line[0].isdigit() else C['text']
        bold = line[0].isdigit()
        ax2.text(0, 0.88 - i * 0.038, line, fontsize=8, color=clr,
                 fontfamily='monospace', fontweight='bold' if bold else 'normal')

    slide_footer(fig, 13)
    return fig


def s11_lvs():
    """LVS sign-off."""
    fig = new_slide()
    slide_header(fig, 'LVS Sign-Off: Magic ext2spice + Netgen',
                 'Authoritative LVS against hand-source SPICE reference')

    ax1 = fig.add_axes([0.06, 0.06, 0.48, 0.78])
    ax1.set_xlim(0, 1); ax1.set_ylim(0, 1); ax1.axis('off')
    ax1.text(0, 0.98, 'LVS Flow', fontsize=13,
             fontweight='bold', color=C['h1'], fontfamily='serif')

    flow = [
        ('INPUT', 'Hand-source .spice', C['blue']),
        ('1. lclayout', 'Z3 SMT -> GDS + LEF + mag', C['text']),
        ('2. Postprocess', '5V markers + implants', C['text']),
        ('3. mk_ports_gds', 'Strip labels, insert I/O pins', C['text']),
        ('4. Magic extract', 'load GDS -> extract all -> ext2spice lvs', C['text']),
        ('5. Block assembly', 'build_support.py: tap|cell|tap', C['text']),
        ('6. Netgen', 'netgen -batch lvs {extracted} {hand-source} {gf180_setup}', C['text']),
        ('RESULT', '"Circuits match uniquely", bulk=VPWR/VGND', C['green']),
    ]
    for i, (label, body, color) in enumerate(flow):
        yy = 0.84 - i * 0.095
        ax1.text(0, yy, label, fontsize=9.5, fontweight='bold',
                 color=color, fontfamily='monospace')
        ax1.text(0.18, yy, body, fontsize=8.5, color=C['muted'],
                 fontfamily='monospace')

    ax2 = fig.add_axes([0.57, 0.06, 0.37, 0.78])
    ax2.set_xlim(0, 1); ax2.set_ylim(0, 1); ax2.axis('off')
    ax2.text(0, 0.98, 'LVS Lessons', fontsize=13,
             fontweight='bold', color=C['h1'], fontfamily='serif')
    lessons = [
        'lclayout internal LVS != official Netgen. Sign-off is '
        'Magic ext2spice + Netgen with GF180 setup.',

        'Run LVS on tap|cell|tap, not standalone. A tapless cell '
        'has floating wells -> bulk mismatch (+2 nets).',

        'Labeling the nwell "VPWR" does NOT fix bulk. It creates '
        'VPWR + VPWR_uq0 (two disconnected nets). Only abutted '
        'taps physically close the tie.',

        'No cthresh/rthresh for LVS. Those enable parasitic-cap '
        'extraction (adds C devices) and break device matching. '
        'Use "ext2spice lvs" alone.',

        'Port hygiene: lclayout writes hundreds of labels. '
        'mk_ports_gds.py strips ALL, inserts 5 I/O labels only.',

        'Debug order: device count -> types -> W/L -> bulk nets '
        '-> labels -> opens/shorts. Topology-first, nets last.',
    ]
    for i, l in enumerate(lessons):
        yy = 0.84 - i * 0.12
        body_text(ax2, 0, yy, l, size=8, width=42, lh=1.4)

    slide_footer(fig, 14)
    return fig


def s12_wave1():
    """Wave 1 results."""
    fig = new_slide()
    slide_header(fig, 'Wave 1 Results: 9 BASIC Cells + Support Library',
                 'All: 0 cell-level DRC  |  Block LVS clean  |  Pin-access PASS  |  LEF audit PASS')

    ax1 = fig.add_axes([0.06, 0.08, 0.48, 0.78])
    ax1.set_xlim(0, 1); ax1.set_ylim(0, 1); ax1.axis('off')
    ax1.text(0, 0.98, 'Signed-Off LSDL Cells', fontsize=13,
             fontweight='bold', color=C['h1'], fontfamily='serif')

    cells = [
        ['lsdl_inv_x1',   '!A',                     'A',             '11T'],
        ['lsdl_nand2_x1', '!(A1*A2)',               'A1, A2',        '11T'],
        ['lsdl_nand3_x1', '!(A1*A2*A3)',            'A1, A2, A3',    '11T'],
        ['lsdl_nand4_x1', '!(A1*A2*A3*A4)',         'A1-A4',         '11T'],
        ['lsdl_nor2_x1',  '!(A1+A2)',               'A1, A2',        '11T'],
        ['lsdl_nor3_x1',  '!(A1+A2+A3)',            'A1, A2, A3',    '11T'],
        ['lsdl_nor4_x1',  '!(A1+A2+A3+A4)',         'A1-A4',         '11T'],
        ['lsdl_aoi21_x1', '!((A1*A2)+B)',           'A1, A2, B',     '11T'],
        ['lsdl_aoi22_x1', '!((A1*A2)+(B1*B2))',     'A1,A2,B1,B2',   '11T'],
    ]
    table(ax1, 0, 0.82, ['Cell', 'Function', 'Inputs', 'Row'],
          cells, [0.20, 0.26, 0.30, 0.06], size=8)

    ax1.text(0, 0.66, 'Support: lsdl_tap_11t, lsdl_endcap_11t, lsdl_fill_11t_{1,2,4} (all DRC 0)',
             fontsize=8, color=C['muted'], fontfamily='monospace')

    ax1.text(0, 0.58, 'PVT Timing (TT, 5V, 25C, eval fall)', fontsize=11,
             fontweight='bold', color=C['h1'], fontfamily='serif')
    pvt = ['inv: 214 ps', 'nand2: 216 ps', 'nand3: 278 ps', 'nand4: 312 ps',
           'nor2: 227 ps', 'nor3: 263 ps', 'nor4: 291 ps',
           'aoi21: 266 ps', 'aoi22: 296 ps']
    ax1.text(0, 0.50, '  '.join(pvt[:5]), fontsize=8.5, color=C['text'],
             fontfamily='monospace')
    ax1.text(0, 0.46, '  '.join(pvt[5:]), fontsize=8.5, color=C['text'],
             fontfamily='monospace')

    ax2 = fig.add_axes([0.57, 0.06, 0.37, 0.78])
    ax2.set_xlim(0, 1); ax2.set_ylim(0, 1); ax2.axis('off')
    ax2.text(0, 0.98, 'PEX Validation', fontsize=13,
             fontweight='bold', color=C['h1'], fontfamily='serif')
    body_text(ax2, 0, 0.88,
        'Deepest cell per family validated with parasitic-extracted '
        'netlists (Magic RC extraction + ngspice):\n\n'
        'lsdl_inv_x1:\n'
        '  tpd: schematic 215ps -> PEX 346ps (<< 2ns)\n'
        '  glitch negligible, Out latched correctly\n\n'
        'lsdl_nand2_x1: (series NMOS stack)\n'
        '  charge-share floor v_dyn_share = 4.53 V\n'
        '  >> 3.5 V pass criterion\n\n'
        'lsdl_nand4_x1: (deepest series, 4 NMOS)\n'
        '  dyn floor 4.57 V with full parasitics\n\n'
        'lsdl_aoi22_x1: (series-parallel)\n'
        '  arm-A share node floor 4.49 V\n\n'
        'All > 3.5 V. Parasitic capacitance does\n'
        'not cause false discharge of the\n'
        'dynamic node.',
        size=8.5, width=45, lh=1.4)

    slide_footer(fig, 15)
    return fig


def s13_flow():
    """Hardened flow."""
    fig = new_slide()
    slide_header(fig, 'The Hardened One-Command Flow',
                 'signoff_cell.sh <cell> [tracks]  ->  SPICE to sign-off GDS/LEF with 4-gate PASS/FAIL')

    ax1 = fig.add_axes([0.06, 0.08, 0.88, 0.60])
    ax1.set_xlim(0, 1); ax1.set_ylim(0, 1); ax1.axis('off')

    stages = [
        ('1. lclayout', 'Z3 SMT\nplace+route\n11T row\n3-track\npitch', C['purple']),
        ('2. Markers', 'DUALGATE\nFET5VDEF\nwell rect.\nimplants', C['blue']),
        ('3. Ports', 'Strip labels\nI/O pins\nmetal1\nauto-detect', C['green']),
        ('4. Snap', 'met2 track\nspacing-\naware snap', C['orange']),
        ('5. LEF fix', 'DIRECTION\nUSE correct\nPIN map', C['accent']),
        ('6. DRC', 'KLayout\nfull deck\nparse_drc\n0 cell-lvl', C['red']),
        ('7. LVS', 'tap|cell|tap\nnetgen\n"Circuits\nmatch"', C['purple']),
        ('8. Gates', 'pin-access\n+ LEF audit\nPASS', C['green']),
    ]
    bw = 0.11
    gap = 0.005
    for i, (title, body, color) in enumerate(stages):
        x = 0.01 + i * (bw + gap)
        rect = mpatches.FancyBboxPatch((x, 0.15), bw, 0.60,
               boxstyle="round,pad=0.006", facecolor=color, alpha=0.12,
               edgecolor=color, linewidth=1.5)
        ax1.add_patch(rect)
        ax1.text(x + bw/2, 0.72, title, fontsize=8.5, fontweight='bold',
                 color=color, ha='center', va='top', fontfamily='monospace')
        for j, line in enumerate(body.split('\n')):
            ax1.text(x + bw/2, 0.58 - j * 0.05, line, fontsize=7.2,
                     color=C['text'], ha='center', va='top',
                     fontfamily='monospace')
        if i < len(stages) - 1:
            ax1.annotate('', xy=(x + bw + gap, 0.45), xytext=(x + bw, 0.45),
                        arrowprops=dict(arrowstyle='->', color=C['grey'], lw=1.2))

    ax2 = fig.add_axes([0.06, 0.02, 0.88, 0.18])
    ax2.set_xlim(0, 1); ax2.set_ylim(0, 1); ax2.axis('off')
    ax2.text(0, 0.85, '4 PnR-Trust Gates', fontsize=11,
             fontweight='bold', color=C['h1'], fontfamily='serif')
    gates = [
        ('G1: DRC', '0 cell-level violations\n(DF.13/14 chip-level)'),
        ('G2: LVS', '"Circuits match uniquely"\nbulk = VPWR/VGND'),
        ('G3: Pin-Access', '>=1 legal on-grid\nmet2 access point/pin'),
        ('G4: LEF Audit', 'PORT rects on real metal\nlayers/USE/DIRECTION ok'),
    ]
    for i, (gate, desc) in enumerate(gates):
        x = 0.02 + i * 0.24
        ax2.text(x, 0.45, gate, fontsize=10, fontweight='bold',
                 color=C['blue'], fontfamily='monospace')
        for j, line in enumerate(desc.split('\n')):
            ax2.text(x, 0.15 - j * 0.05, line, fontsize=8, color=C['muted'],
                     fontfamily='monospace')

    slide_footer(fig, 16)
    return fig


def s14_performance():
    """Performance comparison."""
    fig = new_slide()
    slide_header(fig, 'Performance: LSDL vs CMOS — 64-bit Adder Pair',
                 'Same systolic ripple architecture, GF180MCU 5V — comparison isolates the logic family')

    ax1 = fig.add_axes([0.06, 0.06, 0.44, 0.78])
    ax1.set_xlim(0, 1); ax1.set_ylim(0, 1); ax1.axis('off')
    ax1.text(0, 0.98, 'Block-Level PnR Results', fontsize=13,
             fontweight='bold', color=C['h1'], fontfamily='serif')
    comp = [
        ['Clock freq',      '1 GHz',           '500 MHz',         '2.0x faster'],
        ['Cell count',      '16,832 LSDL',     '4,224 CMOS',      '--'],
        ['Die area',        '1,549 um2',       '766 um2',         '--'],
        ['Core util',       '60.3%',           '60.2%',           '--'],
        ['Setup slack',     '+0.078 ns',       '+0.003 ns',       '--'],
        ['Hold slack',      '+0.50 ns',        '+0.135 ns',       '--'],
        ['Route DRC',       '0',               '0',               '--'],
        ['Foundry DRC',     'CLEAN (12 runs)', 'pending',         '--'],
        ['Clock dist',      'C1+C2 flat',      'CTS clkbuf tree', '--'],
    ]
    table(ax1, 0, 0.82, ['Metric','LSDL Adder64','CMOS Adder64','Adv.'],
          comp, [0.18,0.26,0.24,0.16], size=8)

    ax1.text(0, 0.62, 'Cell-Level (TT, 5V, 25C)', fontsize=11,
             fontweight='bold', color=C['h1'], fontfamily='serif')
    cell = [
        ['Clk->Out',  '252 ps', '418 ps (361+57)', '1.66x faster'],
        ['Power',     '17.6 uW','44.6 uW',         '2.5x lower'],
        ['FET count', '12',     '28 (4+24)',        '2.3x fewer'],
    ]
    table(ax1, 0, 0.52, ['','LSDL NAND2','CMOS NAND2+DFF',''],
          cell, [0.15,0.18,0.33,0.18], size=8)

    ax2 = fig.add_axes([0.53, 0.06, 0.41, 0.78])
    ax2.set_xlim(0, 1); ax2.set_ylim(0, 1); ax2.axis('off')
    ax2.text(0, 0.98, 'Tester Infrastructure', fontsize=13,
             fontweight='bold', color=C['h1'], fontfamily='serif')
    body_text(ax2, 0, 0.88,
        'Identical testers per adder pair:\n\n'
        'FSM: /6 Johnson counter (self-starting)\n'
        '10-vector ROM, sampled at exact first arrival\n'
        '"correct" + "incorrect" LED pins\n\n'
        'f_max: sweep external clock until incorrect LED\n'
        '(adder always fails before tester)\n\n'
        'Tester (stock 9T, 278x278 um):\n'
        '  Setup: +0.012 ns @ 0.9 ns (1.11 GHz)\n'
        '  Hold: +0.49 ns, Route DRC: 0\n\n'
        'Key design decisions:\n'
        '  - Identical gate-level netlist for both adders\n'
        '  - LSDL wrapper adds 129 inverters for dual-rail\n'
        '  - Same physical distance adder<->tester\n'
        '  - Tester always outlasts both adders',
        size=8.5, width=50, lh=1.4)

    slide_footer(fig, 17)
    return fig


def s15_comparison():
    """Cell-level comparison."""
    fig = new_slide()
    slide_header(fig, 'LSDL vs CMOS: Cell-Level Comparison & Project Summary',
                 'Same SMT flow, same GF180 node — identical sign-off standard')

    ax1 = fig.add_axes([0.06, 0.06, 0.50, 0.78])
    ax1.set_xlim(0, 1); ax1.set_ylim(0, 1); ax1.axis('off')
    ax1.text(0, 0.98, 'Cell-Level Comparison', fontsize=13,
             fontweight='bold', color=C['h1'], fontfamily='serif')

    items = [
        ('Transistors', 'INV: 11 FETs (5P+6N)', 'INV+DFF: 28 FETs'),
        ('Row height', '11T (6.16 um)', '9T (5.04 um)'),
        ('Generation', 'LibreCell/Z3, TRACKS=11', 'LibreCell/Z3, TRACKS=9'),
        ('DRC', '0 cell-level (KLayout deep)', '0 cell-level (same deck)'),
        ('LVS', 'tap|cell|tap, Netgen', 'tap|cell|tap, Netgen'),
        ('Liberty', 'Sequential ff (clocked_on: CLK)', 'Comb + separate DFF'),
        ('Clock', 'C1/C2 flat, no CTS', 'CTS with clkbuf tree'),
        ('Power', '17.6 uW (precharge reuse)', '44.6 uW (crowbar)'),
    ]
    for i, (topic, lsd, cmos) in enumerate(items):
        yy = 0.84 - i * 0.085
        ax1.text(0, yy, topic, fontsize=9, fontweight='bold',
                 color=C['blue'], fontfamily='monospace')
        ax1.text(0, yy-0.023, lsd, fontsize=8.2, color=C['purple'],
                 fontfamily='monospace')
        ax1.text(0.35, yy-0.023, cmos, fontsize=8.2, color=C['green'],
                 fontfamily='monospace')

    ax2 = fig.add_axes([0.59, 0.06, 0.35, 0.78])
    ax2.set_xlim(0, 1); ax2.set_ylim(0, 1); ax2.axis('off')
    ax2.text(0, 0.98, 'Project Status', fontsize=13,
             fontweight='bold', color=C['h1'], fontfamily='serif')
    bullet(ax2, 0, 0.84, [
        '9 LSDL BASIC cells physically signed off',
        '0 cell-level DRC, block LVS clean',
        'Pin-access + LEF audit PASS on all cells',
        '11T support library seam-clean',
        'PEX: charge-share floor >3.5V with parasitics',
        'Liberty .lib with measured PVT data',
        '64-bit adder PnR: 1 GHz, +0.078 ns, DRC 0',
        '12-run adder GDS DRC: 37k -> 0',
        'Identical CMOS adder: 500 MHz, DRC 0',
        'Tester macros: 1.11 GHz ceiling, DRC 0',
        'def2gds.py: reusable implant-healing pipeline',
    ], size=8.5, spacing=0.036)

    ax2.text(0, 0.28, 'Remaining', fontsize=11,
             fontweight='bold', color=C['h1'], fontfamily='serif')
    bullet(ax2, 0, 0.18, [
        'Block LVS for CMOS adder64',
        'PEX glitch gate on adder critical nets',
        'Wave 2 wide cells (OR_TREE, MUX_SEG, PRI_ENC)',
        'Mux + encoder benchmark blocks',
        'Full-chip integration + tapeout submission',
    ], size=8, spacing=0.032)

    slide_footer(fig, 18)
    return fig


def s16_toolflow():
    """End-to-end tool flow."""
    fig = new_slide()
    slide_header(fig, 'End-to-End Tool Flow',
                 'From SPICE netlist to tapeout-ready GDS')

    ax = fig.add_axes([0.06, 0.06, 0.88, 0.78])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')

    phases = [
        ('CELL DESIGN', 0.04, [
            'Hand-source\n.spice',
            'lclayout\nnetlist .sp',
            'gen_and_drc.sh\n(Z3 SMT -> GDS)',
            'librecell_\npostprocess.py',
            'signoff_cell.sh\n(4-gate PASS/FAIL)',
        ], C['purple']),
        ('BLOCK P&R', 0.37, [
            'Verilog netlist\n(16,832 cells)',
            'make_pnr_\ncollateral.py\n(LEF sanitization)',
            'run_pnr.tcl\n(OpenROAD: floorplan,\nplace, route, timing)',
            'Route DRC 0\n+ setup/hold\nclosure',
            'write DEF +\nOpenROAD DB',
        ], C['blue']),
        ('STREAMOUT', 0.70, [
            'def2gds.py\n(LEFDEF read,\ncell merge,\nimplant heal)',
            'extend+debite+\nneck fill+CO\nhalo patches',
            'KLayout deep\nDRC (GF180\nfull deck)',
            '-> CLEAN GDS',
            'def2gds_cmos.py\n(stock SCL,\nno implant heal)',
        ], C['green']),
    ]
    for phase_name, x_start, steps, color in phases:
        ax.text(x_start + 0.135, 0.92, phase_name, fontsize=11,
                fontweight='bold', color=color, ha='center',
                fontfamily='serif')
        for i, step in enumerate(steps):
            sx = x_start + i * 0.067
            rect = mpatches.FancyBboxPatch((sx, 0.06), 0.063, 0.78,
                   boxstyle="round,pad=0.004", facecolor=color, alpha=0.08,
                   edgecolor=color, linewidth=1)
            ax.add_patch(rect)
            for j, line in enumerate(step.split('\n')):
                ax.text(sx + 0.0315, 0.78 - j * 0.042, line, fontsize=7.2,
                        color=C['text'], ha='center', va='top',
                        fontfamily='monospace')
            if i < len(steps) - 1:
                ax.annotate('', xy=(sx + 0.063 + 0.004, 0.45),
                           xytext=(sx + 0.063, 0.45),
                           arrowprops=dict(arrowstyle='->', color=C['grey'], lw=1))

    for (x1, x2) in [(0.33, 0.37), (0.66, 0.70)]:
        ax.annotate('', xy=(x2, 0.45), xytext=(x1, 0.45),
                   arrowprops=dict(arrowstyle='->', color=C['muted'], lw=2))

    ax.text(0.5, 0.01,
            'LibreCell (Z3)    Magic    Netgen    KLayout    OpenROAD    Yosys    ngspice    Python',
            fontsize=7.5, color=C['grey'], ha='center', fontfamily='monospace')

    slide_footer(fig, 19)
    return fig


def s17_conclusion():
    """Conclusion."""
    fig = new_slide()
    slide_header(fig, 'Summary & References')

    ax = fig.add_axes([0.06, 0.06, 0.88, 0.78])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')
    ax.text(0, 0.95, 'Key Takeaways', fontsize=15, fontweight='bold',
            color=C['h1'], fontfamily='serif')

    takeaways = [
        'LSDL integrates a latch inside every cell, replacing the '
        'domino + separate latch pair. The result is 2.0x higher '
        'frequency and 2.5x lower power than static CMOS at 180 nm.',

        'LibreCell + Z3 SMT automates cell layout with correct-by-'
        'construction DRC. The GF180MCU community tech, once hardened, '
        'produces DRC-clean cells from SPICE in one command.',

        'DRC elimination is systematic: fix codegen/tech-file parameters, '
        'not GDS; wipe stale markers; track per-rule. The same methodology '
        'scaled from a single cell (33->0) to the full 64-bit adder (37k->0).',

        'Block LVS on abutted tap|cell|tap assemblies, not standalone '
        'cells. Wells merge at boundaries, bulk ties close, and Netgen '
        'reports "Circuits match uniquely."',

        'The def2gds.py implant-healing pipeline is proven on the 64-bit '
        'adder (12-run convergence, 37k->0 markers) and is reusable for '
        'every future LSDL block.',
    ]
    for i, item in enumerate(takeaways):
        body_text(ax, 0, 0.80 - i * 0.12, item, size=9.5, width=90, lh=1.5)

    ax.text(0, 0.18, 'References', fontsize=13, fontweight='bold',
            color=C['h1'], fontfamily='serif')
    refs = [
        '[1] Belluomini et al., "LSDL circuits for high-speed low-power circuit design," IBM JRD 50:2/3, 2006.',
        '[2] GF180MCU PDK: github.com/google/gf180mcu-pdk (Apache 2.0)',
        '[3] LibreCell: codeberg.org/librecell/lclayout (AGPL-3.0)',
        '[4] LibreSilicon GF180 tech: gitlab.libresilicon.com/generator-tools/standard-cell-generator',
        '[5] OpenROAD: github.com/The-OpenROAD-Project/OpenROAD',
        '[6] Magic VLSI: opencircuitdesign.com/magic',
        '[7] Netgen: opencircuitdesign.com/netgen',
        '[8] KLayout: klayout.de (GPL-3.0)',
        '[9] Z3: github.com/Z3Prover/z3 (MIT, Microsoft Research)',
    ]
    for i, ref in enumerate(refs):
        ax.text(0, 0.10 - i * 0.022, ref, fontsize=7.5, color=C['muted'],
                fontfamily='monospace')

    slide_footer(fig, 20)
    return fig


# ═════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════

def main(out_pdf):
    pdf_path = Path(out_pdf)
    slides = [
        s01_title, s02_process, s03_lsdl_inv, s04_lsdl_nand2,
        s05_cmos_schematics, s06_waveform,
        s04_c1c2_pipeline, s05_lsdl_vs_cmos, s06_adder_pipeline, s07_library,
        s08_librecell, s09_drc, s10_adder_drc, s11_lvs, s12_wave1,
        s13_flow, s14_performance, s15_comparison, s16_toolflow,
        s17_conclusion,
    ]

    print(f'Generating {len(slides)} slides -> {pdf_path} ...')
    with PdfPages(str(pdf_path)) as pdf:
        for i, fn in enumerate(slides):
            fig = fn()
            pdf.savefig(fig, dpi=150)
            plt.close(fig)
            print(f'  slide {i+1:2d}/{len(slides)}  done')
    print(f'Wrote {pdf_path} ({pdf_path.stat().st_size / 1024:.0f} KB)')


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else \
        '/mada/users/czeng14/projects/brainstorm/domino/lsdl_lib/docs/' \
        'lsdl_presentation.pdf'
    main(out)

#!/usr/bin/env python3
"""schem_box.py — clean box-style transistor schematics for the NAND2 cells.
Each FET is a labelled box with Gate(left) / Drain(top) / Source(bottom) pins;
nets are drawn as orthogonal wires + named dots. Generates both LSDL and CMOS.
Usage: schem_box.py <lsdl.png> <cmos.png>
"""
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

NETC = {"dyn": "tab:green", "out_b": "purple", "Out": "tab:red", "OUT": "tab:red"}

def fet(ax, x, y, name, typ, g, w=1.05, h=0.66):
    """draw a FET box centered at (x,y); return pin coords."""
    fc = "#ffe9e9" if typ == "P" else "#e9f0ff"
    ax.add_patch(FancyBboxPatch((x-w/2, y-h/2), w, h, boxstyle="round,pad=0.02",
                 fc=fc, ec="black", lw=1.2, zorder=3))
    ax.text(x, y+0.07, name, ha="center", va="center", fontsize=8.5, zorder=4)
    ax.text(x, y-0.16, f"{typ}MOS", ha="center", va="center", fontsize=6.5, color="0.4", zorder=4)
    gp, dp, sp = (x-w/2, y), (x, y+h/2), (x, y-h/2)          # gate, drain, source
    # gate stub + label
    ax.plot([gp[0]-0.5, gp[0]], [y, y], "k", lw=1, zorder=2)
    ax.text(gp[0]-0.58, y, g, ha="right", va="center", fontsize=8,
            color=NETC.get(g, "black"), zorder=4)
    return {"g": gp, "d": dp, "s": sp}

def wire(ax, p1, p2, c="k"):
    ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=c, lw=1.1, zorder=2)

def vwire(ax, p, y, c="k"): wire(ax, p, (p[0], y), c)
def node(ax, p, label=None, open_=False):
    ax.plot(*p, "o", ms=4, mfc=("white" if open_ else "black"), mec="black", zorder=5)
    if label: ax.text(p[0]+0.12, p[1]+0.14, label, fontsize=7.5,
                       color=NETC.get(label, "black"), zorder=5)

def rails(ax, x0, x1, vp, vg):
    ax.plot([x0, x1], [vp, vp], "tab:red", lw=2.2, zorder=1)
    ax.text(x0-0.2, vp, "VPWR", ha="right", va="center", fontsize=9, color="tab:red")
    ax.plot([x0, x1], [vg, vg], "tab:blue", lw=2.2, zorder=1)
    ax.text(x0-0.2, vg, "VGND", ha="right", va="center", fontsize=9, color="tab:blue")

def finish(ax, title, xlim, ylim):
    ax.set_title(title, fontsize=11)
    ax.set_xlim(*xlim); ax.set_ylim(*ylim); ax.set_aspect("equal"); ax.axis("off")

# ---------------- LSDL NAND2 (12 FETs) ----------------
def lsdl(png):
    fig, ax = plt.subplots(figsize=(13, 7)); VP, VG = 9.5, 0.5
    rails(ax, 1.0, 18.5, VP, VG)
    # Col A: precharge + eval tree + foot
    xA = 2.5
    pre = fet(ax, xA, 8.4, "XPRE", "P", "Clk"); vwire(ax, pre["s"], VP, "tab:red"); vwire(ax, pre["d"], 7.3)
    node(ax, (xA, 7.3), "dyn")
    na = fet(ax, xA, 6.5, "XNA", "P" if False else "N", "A1"); vwire(ax, na["d"], 7.3)
    node(ax, (xA, 5.6), "nint", True); vwire(ax, na["s"], 5.6)
    nb = fet(ax, xA, 4.8, "XNB", "N", "A2"); vwire(ax, nb["d"], 5.6)
    node(ax, (xA, 3.9), "foot_top", True); vwire(ax, nb["s"], 3.9)
    ft = fet(ax, xA, 3.1, "XFOOT", "N", "Clk"); vwire(ax, ft["d"], 3.9); vwire(ax, ft["s"], VG, "tab:blue")
    # Col B: predriver (dyn -> out_b)
    xB = 7.0
    pdp = fet(ax, xB, 8.4, "XPDRVP", "P", "dyn"); vwire(ax, pdp["s"], VP, "tab:red"); vwire(ax, pdp["d"], 7.3)
    node(ax, (xB, 7.3), "out_b")
    pdn = fet(ax, xB, 6.3, "XPDRVN", "N", "dyn"); vwire(ax, pdn["d"], 7.3)
    node(ax, (xB, 5.3), "hdr_src", True); vwire(ax, pdn["s"], 5.3)
    hdr = fet(ax, xB, 4.4, "XHDR", "N", "Clk"); vwire(ax, hdr["d"], 5.3); vwire(ax, hdr["s"], VG, "tab:blue")
    # Col C: keeper + cut-feedback
    xC = 11.5
    fbp = fet(ax, xC, 8.4, "XFBP", "P", "Out"); vwire(ax, fbp["s"], VP, "tab:red"); vwire(ax, fbp["d"], 7.4)
    node(ax, (xC, 7.4), "cut_fb_src", True)
    cut = fet(ax, xC, 6.5, "XCUTFB", "P", "Clk"); vwire(ax, cut["d"], 7.4)
    ax.text(cut["s"][0]+0.1, cut["s"][1]-0.45, "out_b", fontsize=7.5, color="purple"); vwire(ax, cut["s"], 5.4)
    node(ax, (xC, 5.4), None)
    fbn = fet(ax, xC, 3.3, "XFBN", "N", "Out"); vwire(ax, fbn["d"], 5.4)
    ax.text(fbn["d"][0]+0.1, 4.7, "out_b", fontsize=7.5, color="purple"); vwire(ax, fbn["s"], VG, "tab:blue")
    # Col D: output driver
    xD = 15.8
    odp = fet(ax, xD, 8.4, "XODRVP", "P", "out_b"); vwire(ax, odp["s"], VP, "tab:red"); vwire(ax, odp["d"], 6.0)
    node(ax, (xD, 6.0), None); wire(ax, (xD, 6.0), (17.8, 6.0)); ax.text(17.9, 6.0, "OUT", color="tab:red", fontsize=10, va="center")
    odn = fet(ax, xD, 5.0, "XODRVN", "N", "out_b"); vwire(ax, odn["d"], 6.0); vwire(ax, odn["s"], VG, "tab:blue")
    finish(ax, "LSDL NAND2 (Belluomini Fig.1) — Out=!(A1·A2)   12 FETs   "
               "[precharge+eval | predriver | keeper/cut-fb | output]", (-0.5, 19.5), (-0.3, 10.3))
    ax.text(9.5, -0.05, "gate label = driving net (green=dyn, purple=out_b, red=Out); precharge high then conditional discharge",
            ha="center", fontsize=7.5, color="0.4")
    fig.tight_layout(); fig.savefig(png, dpi=115); print("wrote", png)

# ---------------- static CMOS NAND2 (4 FETs) ----------------
def cmos(png):
    fig, ax = plt.subplots(figsize=(6.5, 6)); VP, VG = 7.5, 0.5
    rails(ax, 1.0, 7.5, VP, VG)
    p1 = fet(ax, 2.5, 6.2, "MP1", "P", "A1"); vwire(ax, p1["s"], VP, "tab:red")
    p2 = fet(ax, 5.0, 6.2, "MP2", "P", "A2"); vwire(ax, p2["s"], VP, "tab:red")
    vwire(ax, p1["d"], 4.7); vwire(ax, p2["d"], 4.7); wire(ax, (2.5, 4.7), (5.0, 4.7))
    node(ax, (3.75, 4.7)); wire(ax, (3.75, 4.7), (6.8, 4.7)); ax.text(6.9, 4.7, "OUT", color="tab:red", fontsize=10, va="center")
    n1 = fet(ax, 3.75, 3.8, "MN1", "N", "A1"); vwire(ax, n1["d"], 4.7)
    node(ax, (3.75, 2.9), "nint", True); vwire(ax, n1["s"], 2.9)
    n2 = fet(ax, 3.75, 2.1, "MN2", "N", "A2"); vwire(ax, n2["d"], 2.9); vwire(ax, n2["s"], VG, "tab:blue")
    finish(ax, "static CMOS NAND2 — Out=!(A1·A2)   4 FETs", (-0.5, 8.5), (-0.2, 8.3))
    fig.tight_layout(); fig.savefig(png, dpi=115); print("wrote", png)

lsdl(sys.argv[1]); cmos(sys.argv[2])

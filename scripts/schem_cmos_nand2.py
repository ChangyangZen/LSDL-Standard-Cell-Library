#!/usr/bin/env python3
"""schem_cmos_nand2.py — transistor-level schematic of the static CMOS NAND2."""
import schemdraw
import schemdraw.elements as elm

OUT = "/soe/czeng14/projects/brainstorm-domree-tmp/x"  # overwritten by argv
import sys
out = sys.argv[1] if len(sys.argv) > 1 else "/soe/czeng14/projects/brainstorm-domino-tmp/cmos_nand2_schem.svg"

with schemdraw.Drawing(file=out, show=False) as d:
    d.config(fontsize=11)
    # VPWR rail
    d += (vpwr := elm.Line().right().length(7).at((0, 7)).color('red'))
    d += elm.Label().at((-0.6, 7)).label('VPWR')
    # pull-up: two PMOS in parallel (gates A1, A2), sources to VPWR, drains to OUT
    d += (p1 := elm.PFet().at((2, 5.5)).anchor('source').label('MP1', 'left', ofst=0.3))
    d += (p2 := elm.PFet().at((5, 5.5)).anchor('source').label('MP2', 'right', ofst=0.3))
    d += elm.Line().at(p1.source).to((2, 7)).color('red')      # P1 src -> VPWR
    d += elm.Line().at(p2.source).to((5, 7)).color('red')      # P2 src -> VPWR
    d += elm.Label().at(p1.gate).label('A1', 'left')
    d += elm.Label().at(p2.gate).label('A2', 'right')
    # OUT node: P drains join
    d += elm.Line().at(p1.drain).to((2, 3.5))
    d += elm.Line().at(p2.drain).to((5, 3.5))
    d += elm.Line().at((2, 3.5)).to((5, 3.5))
    d += elm.Line().at((3.5, 3.5)).to((7, 3.5))
    d += elm.Dot().at((3.5, 3.5))
    d += elm.Label().at((7.2, 3.5)).label('OUT', 'right')
    # pull-down: two NMOS in series (gates A1, A2): OUT -> nint -> VGND
    d += (n1 := elm.NFet().at((3.5, 3.5)).anchor('drain').label('MN1', 'right', ofst=0.3))
    d += elm.Label().at(n1.gate).label('A1', 'left')
    d += elm.Dot(open=True).at(n1.source).label('nint', 'right')
    d += (n2 := elm.NFet().at(n1.source).anchor('drain').label('MN2', 'right', ofst=0.3))
    d += elm.Label().at(n2.gate).label('A2', 'left')
    # VGND rail
    d += elm.Line().at(n2.source).to((3.5, 0)).color('blue')
    d += elm.Line().right().length(7).at((0, 0)).color('blue')
    d += elm.Label().at((-0.6, 0)).label('VGND')
    d += elm.Label().at((3.5, 7.6)).label('static CMOS NAND2   OUT = !(A1·A2)   (4 FETs)')
print("wrote", out)

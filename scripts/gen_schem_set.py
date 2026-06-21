#!/usr/bin/env python3
"""Generate 4 schematic images for LSDL vs CMOS comparison.
All elements shifted right by X0=1.5 so left-side labels stay in bounds."""

import sys, os
from pathlib import Path
import schemdraw
import schemdraw.elements as elm

OUT_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else \
    Path('/mada/users/czeng14/projects/brainstorm/domino/lsdl_lib/docs')

X0 = 1.5   # global right-shift so negative-x labels are in bounds

def draw_lsdl_inv():
    out = str(OUT_DIR / 'schem_lsdl_inv.png')
    d = schemdraw.Drawing(file=out, show=False, dpi=150)
    d.config(fontsize=9)
    VP, VG = 12.0, 0.5
    R = 17.0  # rail right extent

    d.add(elm.Line().at((X0, VP)).right().length(R).color('#d63031'))
    d.add(elm.Label().at((X0-0.5, VP)).label('VPWR'))
    d.add(elm.Line().at((X0, VG)).right().length(R).color('#0984e3'))
    d.add(elm.Label().at((X0-0.5, VG)).label('VGND'))

    xA = X0 + 2.5
    pre = elm.PFet().at((xA, VP)).anchor('source')
    d.add(pre)
    d.add(elm.Label().at(pre.gate).label('Clk', 'left'))
    d.add(elm.Line().at(pre.drain).to((xA, 8.5)))
    d.add(elm.Dot().at((xA, 8.5)))
    d.add(elm.Label().at((xA+0.3, 8.7)).label('dyn', 'right').color('green'))
    nt = elm.NFet().at((xA, 8.5)).anchor('drain')
    d.add(nt)
    d.add(elm.Label().at(nt.gate).label('A', 'left'))
    d.add(elm.Dot(open=True).at(nt.source))
    d.add(elm.Label().at(nt.source).label('ft', 'right'))
    ft = elm.NFet().at(nt.source).anchor('drain')
    d.add(ft)
    d.add(elm.Label().at(ft.gate).label('Clk', 'left'))
    d.add(elm.Line().at(ft.source).to((xA, VG)))

    xB = X0 + 7.0
    pdp = elm.PFet().at((xB, VP)).anchor('source')
    d.add(pdp)
    d.add(elm.Label().at(pdp.gate).label('dyn', 'left').color('green'))
    d.add(elm.Line().at(pdp.drain).to((xB, 7.5)))
    d.add(elm.Dot().at((xB, 7.5)))
    d.add(elm.Label().at((xB+0.3, 7.7)).label('out_b', 'right').color('purple'))
    pdn = elm.NFet().at((xB, 7.5)).anchor('drain')
    d.add(pdn)
    d.add(elm.Label().at(pdn.gate).label('dyn', 'left').color('green'))
    d.add(elm.Dot(open=True).at(pdn.source))
    d.add(elm.Label().at(pdn.source).label('hdr', 'right'))
    hdr = elm.NFet().at(pdn.source).anchor('drain')
    d.add(hdr)
    d.add(elm.Label().at(hdr.gate).label('Clk', 'left'))
    d.add(elm.Line().at(hdr.source).to((xB, VG)))

    xC = X0 + 11.2
    fbp = elm.PFet().at((xC, VP)).anchor('source')
    d.add(fbp)
    d.add(elm.Label().at(fbp.gate).label('Out', 'left').color('red'))
    d.add(elm.Label().at(fbp.drain).label('cut_fb', 'right'))
    cut = elm.PFet().at(fbp.drain).anchor('source')
    d.add(cut)
    d.add(elm.Label().at(cut.gate).label('Clk', 'left'))
    d.add(elm.Line().at(cut.drain).to((xC, 7.5)))
    d.add(elm.Label().at((xC, 7.3)).label('out_b', 'right').color('purple'))
    fbn = elm.NFet().at((xC, 3.2)).anchor('drain')
    d.add(fbn)
    d.add(elm.Label().at(fbn.drain).label('out_b', 'right').color('purple'))
    d.add(elm.Label().at(fbn.gate).label('Out', 'left').color('red'))
    d.add(elm.Line().at(fbn.source).to((xC, VG)))

    xD = X0 + 15.0
    odp = elm.PFet().at((xD, VP)).anchor('source')
    d.add(odp)
    d.add(elm.Label().at(odp.gate).label('out_b', 'left').color('purple'))
    d.add(elm.Line().at(odp.drain).to((xD, 5.5)))
    d.add(elm.Dot().at((xD, 5.5)))
    d.add(elm.Line().at((xD, 5.5)).to((X0+16.5, 5.5)))
    d.add(elm.Label().at((X0+16.7, 5.5)).label('OUT', 'right').color('red'))
    odn = elm.NFet().at((xD, 5.5)).anchor('drain')
    d.add(odn)
    d.add(elm.Label().at(odn.gate).label('out_b', 'left').color('purple'))
    d.add(elm.Line().at(odn.source).to((xD, VG)))

    d.add(elm.Label().at((X0+8, 13.2)).label(
        'LSDL INVERTER  (Belluomini Fig.1)  Out = !A   '
        '11 FETs: 5 PMOS + 6 NMOS'))
    d.draw()
    print('wrote', out)


def draw_lsdl_nand2():
    out = str(OUT_DIR / 'schem_lsdl_nand2.png')
    d = schemdraw.Drawing(file=out, show=False, dpi=150)
    d.config(fontsize=9)
    VP, VG = 12.0, 0.5
    R = 17.0

    d.add(elm.Line().at((X0, VP)).right().length(R).color('#d63031'))
    d.add(elm.Label().at((X0-0.5, VP)).label('VPWR'))
    d.add(elm.Line().at((X0, VG)).right().length(R).color('#0984e3'))
    d.add(elm.Label().at((X0-0.5, VG)).label('VGND'))

    xA = X0 + 2.5
    pre = elm.PFet().at((xA, VP)).anchor('source')
    d.add(pre)
    d.add(elm.Label().at(pre.gate).label('Clk', 'left'))
    d.add(elm.Line().at(pre.drain).to((xA, 8.3)))
    d.add(elm.Dot().at((xA, 8.3)))
    d.add(elm.Label().at((xA+0.3, 8.5)).label('dyn', 'right').color('green'))
    na = elm.NFet().at((xA, 8.3)).anchor('drain')
    d.add(na)
    d.add(elm.Label().at(na.gate).label('A1', 'left'))
    d.add(elm.Dot(open=True).at(na.source))
    d.add(elm.Label().at(na.source).label('nint', 'right'))
    nb = elm.NFet().at(na.source).anchor('drain')
    d.add(nb)
    d.add(elm.Label().at(nb.gate).label('A2', 'left'))
    d.add(elm.Dot(open=True).at(nb.source))
    d.add(elm.Label().at(nb.source).label('ft', 'right'))
    ft = elm.NFet().at(nb.source).anchor('drain')
    d.add(ft)
    d.add(elm.Label().at(ft.gate).label('Clk', 'left'))
    d.add(elm.Line().at(ft.source).to((xA, VG)))

    xB = X0 + 7.0
    pdp = elm.PFet().at((xB, VP)).anchor('source')
    d.add(pdp)
    d.add(elm.Label().at(pdp.gate).label('dyn', 'left').color('green'))
    d.add(elm.Line().at(pdp.drain).to((xB, 7.5)))
    d.add(elm.Dot().at((xB, 7.5)))
    d.add(elm.Label().at((xB+0.3, 7.7)).label('out_b', 'right').color('purple'))
    pdn = elm.NFet().at((xB, 7.5)).anchor('drain')
    d.add(pdn)
    d.add(elm.Label().at(pdn.gate).label('dyn', 'left').color('green'))
    d.add(elm.Dot(open=True).at(pdn.source))
    d.add(elm.Label().at(pdn.source).label('hdr', 'right'))
    hdr = elm.NFet().at(pdn.source).anchor('drain')
    d.add(hdr)
    d.add(elm.Label().at(hdr.gate).label('Clk', 'left'))
    d.add(elm.Line().at(hdr.source).to((xB, VG)))

    xC = X0 + 11.2
    fbp = elm.PFet().at((xC, VP)).anchor('source')
    d.add(fbp)
    d.add(elm.Label().at(fbp.gate).label('Out', 'left').color('red'))
    d.add(elm.Label().at(fbp.drain).label('cut_fb', 'right'))
    cut = elm.PFet().at(fbp.drain).anchor('source')
    d.add(cut)
    d.add(elm.Label().at(cut.gate).label('Clk', 'left'))
    d.add(elm.Line().at(cut.drain).to((xC, 7.5)))
    d.add(elm.Label().at((xC, 7.3)).label('out_b', 'right').color('purple'))
    fbn = elm.NFet().at((xC, 3.2)).anchor('drain')
    d.add(fbn)
    d.add(elm.Label().at(fbn.drain).label('out_b', 'right').color('purple'))
    d.add(elm.Label().at(fbn.gate).label('Out', 'left').color('red'))
    d.add(elm.Line().at(fbn.source).to((xC, VG)))

    xD = X0 + 15.0
    odp = elm.PFet().at((xD, VP)).anchor('source')
    d.add(odp)
    d.add(elm.Label().at(odp.gate).label('out_b', 'left').color('purple'))
    d.add(elm.Line().at(odp.drain).to((xD, 5.5)))
    d.add(elm.Dot().at((xD, 5.5)))
    d.add(elm.Line().at((xD, 5.5)).to((X0+16.5, 5.5)))
    d.add(elm.Label().at((X0+16.7, 5.5)).label('OUT', 'right').color('red'))
    odn = elm.NFet().at((xD, 5.5)).anchor('drain')
    d.add(odn)
    d.add(elm.Label().at(odn.gate).label('out_b', 'left').color('purple'))
    d.add(elm.Line().at(odn.source).to((xD, VG)))

    d.add(elm.Label().at((X0+8, 13.2)).label(
        'LSDL NAND2  (Belluomini Fig.1)  Out = !(A1*A2)   '
        '12 FETs: 5 PMOS + 7 NMOS  [charge-share node: nint]'))
    d.draw()
    print('wrote', out)


def draw_cmos_inv():
    out = str(OUT_DIR / 'schem_cmos_inv.png')
    d = schemdraw.Drawing(file=out, show=False, dpi=150)
    d.config(fontsize=11)
    d.add(elm.Line().at((X0, 7)).right().length(5).color('#d63031'))
    d.add(elm.Label().at((X0-0.5, 7)).label('VPWR'))
    p1 = elm.PFet().at((X0+3, 7)).anchor('source')
    d.add(p1)
    d.add(elm.Label().at(p1.gate).label('A', 'left'))
    d.add(elm.Line().at(p1.drain).to((X0+3, 4.0)))
    d.add(elm.Dot().at((X0+3, 4.0)))
    d.add(elm.Line().at((X0+3, 4.0)).to((X0+5.5, 4.0)))
    d.add(elm.Label().at((X0+5.7, 4.0)).label('OUT', 'right').color('red'))
    n1 = elm.NFet().at((X0+3, 4.0)).anchor('drain')
    d.add(n1)
    d.add(elm.Label().at(n1.gate).label('A', 'left'))
    d.add(elm.Line().at(n1.source).to((X0+3, 0.5)))
    d.add(elm.Line().at((X0, 0.5)).right().length(5).color('#0984e3'))
    d.add(elm.Label().at((X0-0.5, 0.5)).label('VGND'))
    d.add(elm.Label().at((X0+3, 7.8)).label(
        'Static CMOS INVERTER   Out = !A   (2 FETs)'))
    d.draw()
    print('wrote', out)


def draw_cmos_nand2():
    out = str(OUT_DIR / 'schem_cmos_nand2.png')
    d = schemdraw.Drawing(file=out, show=False, dpi=150)
    d.config(fontsize=11)
    d.add(elm.Line().at((X0, 8)).right().length(8).color('#d63031'))
    d.add(elm.Label().at((X0-0.5, 8)).label('VPWR'))
    p1 = elm.PFet().at((X0+3, 6.5)).anchor('source')
    p2 = elm.PFet().at((X0+6, 6.5)).anchor('source')
    d.add(p1); d.add(p2)
    d.add(elm.Line().at(p1.source).to((X0+3, 8)).color('#d63031'))
    d.add(elm.Line().at(p2.source).to((X0+6, 8)).color('#d63031'))
    d.add(elm.Label().at(p1.gate).label('A1', 'left'))
    d.add(elm.Label().at(p2.gate).label('A2', 'right'))
    d.add(elm.Line().at(p1.drain).to((X0+3, 4.0)))
    d.add(elm.Line().at(p2.drain).to((X0+6, 4.0)))
    d.add(elm.Line().at((X0+3, 4.0)).to((X0+6, 4.0)))
    d.add(elm.Line().at((X0+4.5, 4.0)).to((X0+8.5, 4.0)))
    d.add(elm.Dot().at((X0+4.5, 4.0)))
    d.add(elm.Label().at((X0+8.7, 4.0)).label('OUT', 'right').color('red'))
    n1 = elm.NFet().at((X0+4.5, 4.0)).anchor('drain')
    d.add(n1)
    d.add(elm.Label().at(n1.gate).label('A1', 'left'))
    d.add(elm.Dot(open=True).at(n1.source))
    d.add(elm.Label().at(n1.source).label('nint', 'right'))
    n2 = elm.NFet().at(n1.source).anchor('drain')
    d.add(n2)
    d.add(elm.Label().at(n2.gate).label('A2', 'left'))
    d.add(elm.Line().at(n2.source).to((X0+4.5, 0.5)))
    d.add(elm.Line().at((X0, 0.5)).right().length(8).color('#0984e3'))
    d.add(elm.Label().at((X0-0.5, 0.5)).label('VGND'))
    d.add(elm.Label().at((X0+4.5, 8.7)).label(
        'Static CMOS NAND2   Out = !(A1*A2)   (4 FETs)'))
    d.draw()
    print('wrote', out)


if __name__ == '__main__':
    os.makedirs(OUT_DIR, exist_ok=True)
    draw_lsdl_inv()
    draw_lsdl_nand2()
    draw_cmos_inv()
    draw_cmos_nand2()

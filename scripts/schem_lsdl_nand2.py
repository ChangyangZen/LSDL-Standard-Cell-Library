#!/usr/bin/env python3
"""schem_lsdl_nand2.py — transistor-level schematic of the LSDL NAND2 (12 FETs).
Functional columns L->R: precharge+eval | predriver | keeper/cut-fb | output driver.
Gates are labelled with their driving net (labelled-net style) to keep it readable;
source/drain wiring is drawn explicitly within each column + the rails."""
import sys
import schemdraw
import schemdraw.elements as elm

out = sys.argv[1] if len(sys.argv) > 1 else "/soe/czeng14/projects/brainstorm-domino-tmp/lsdl_nand2_schem.png"
VP, VG = 11.0, 0.0  # rail y

with schemdraw.Drawing(file=out, show=False) as d:
    d.config(fontsize=10.5)
    # rails
    d += elm.Line().at((0, VP)).right().length(17).color('red')
    d += elm.Label().at((-0.7, VP)).label('VPWR')
    d += elm.Line().at((0, VG)).right().length(17).color('blue')
    d += elm.Label().at((-0.7, VG)).label('VGND')

    def vdd(x):  d.add(elm.Line().at((x, VP)).to((x, VP)))  # noop placeholder

    # ---------- Column A: precharge + 2-NMOS eval tree + foot ----------
    xA = 2.5
    d += (pre := elm.PFet().at((xA, VP)).anchor('source').label('XPRE', 'left', ofst=.2))
    d += elm.Label().at(pre.gate).label('Clk', 'left')
    d += elm.Line().at(pre.drain).to((xA, 8.3))
    d += elm.Dot().at((xA, 8.3)); d += elm.Label().at((xA+.25, 8.5)).label('dyn', 'right', color='green')
    d += (na := elm.NFet().at((xA, 8.3)).anchor('drain').label('XNA', 'right', ofst=.2))
    d += elm.Label().at(na.gate).label('A1', 'left')
    d += elm.Dot(open=True).at(na.source); d += elm.Label().at(na.source).label('nint', 'right')
    d += (nb := elm.NFet().at(na.source).anchor('drain').label('XNB', 'right', ofst=.2))
    d += elm.Label().at(nb.gate).label('A2', 'left')
    d += elm.Dot(open=True).at(nb.source); d += elm.Label().at(nb.source).label('foot_top', 'right')
    d += (ft := elm.NFet().at(nb.source).anchor('drain').label('XFOOT', 'right', ofst=.2))
    d += elm.Label().at(ft.gate).label('Clk', 'left')
    d += elm.Line().at(ft.source).to((xA, VG))

    # ---------- Column B: predriver (dyn -> out_b) ----------
    xB = 7.0
    d += (pdp := elm.PFet().at((xB, VP)).anchor('source').label('XPDRVP', 'left', ofst=.2))
    d += elm.Label().at(pdp.gate).label('dyn', 'left', color='green')
    d += elm.Line().at(pdp.drain).to((xB, 7.5))
    d += elm.Dot().at((xB, 7.5)); d += elm.Label().at((xB+.25, 7.7)).label('out_b', 'right', color='purple')
    d += (pdn := elm.NFet().at((xB, 7.5)).anchor('drain').label('XPDRVN', 'right', ofst=.2))
    d += elm.Label().at(pdn.gate).label('dyn', 'left', color='green')
    d += elm.Dot(open=True).at(pdn.source); d += elm.Label().at(pdn.source).label('hdr_src', 'right')
    d += (hdr := elm.NFet().at(pdn.source).anchor('drain').label('XHDR', 'right', ofst=.2))
    d += elm.Label().at(hdr.gate).label('Clk', 'left')
    d += elm.Line().at(hdr.source).to((xB, VG))

    # ---------- Column C: keeper + cut-feedback ----------
    xC = 11.2
    d += (fbp := elm.PFet().at((xC, VP)).anchor('source').label('XFBP', 'left', ofst=.2))
    d += elm.Label().at(fbp.gate).label('Out', 'left', color='red')
    d += elm.Line().at(fbp.drain).to((xC, 7.8))
    d += elm.Dot(open=True).at((xC, 7.8)); d += elm.Label().at((xC+.2, 8.0)).label('cut_fb_src', 'right')
    d += (cut := elm.PFet().at((xC, 7.8)).anchor('source').label('XCUTFB', 'right', ofst=.2))
    d += elm.Label().at(cut.gate).label('Clk', 'left')
    d += elm.Label().at(cut.drain).label('out_b', 'right', color='purple')   # cut drain -> out_b (net label)
    # feedback-n: out_b -> VGND, gate Out (placed lower-left of col C)
    d += (fbn := elm.NFet().at((xC, 3.2)).anchor('drain').label('XFBN', 'right', ofst=.2))
    d += elm.Label().at(fbn.drain).label('out_b', 'right', color='purple')
    d += elm.Label().at(fbn.gate).label('Out', 'left', color='red')
    d += elm.Line().at(fbn.source).to((xC, VG))

    # ---------- Column D: output driver (out_b -> Out) ----------
    xD = 15.0
    d += (odp := elm.PFet().at((xD, VP)).anchor('source').label('XODRVP', 'left', ofst=.2))
    d += elm.Label().at(odp.gate).label('out_b', 'left', color='purple')
    d += elm.Line().at(odp.drain).to((xD, 5.5))
    d += elm.Dot().at((xD, 5.5)); d += elm.Line().at((xD, 5.5)).to((16.6, 5.5))
    d += elm.Label().at((16.7, 5.5)).label('OUT', 'right', color='red')
    d += (odn := elm.NFet().at((xD, 5.5)).anchor('drain').label('XODRVN', 'right', ofst=.2))
    d += elm.Label().at(odn.gate).label('out_b', 'left', color='purple')
    d += elm.Line().at(odn.source).to((xD, VG))

    d += elm.Label().at((8, 11.7)).label(
        'LSDL NAND2  (Belluomini Fig.1)   dyn=!(A1·A2)  ->  Out=!(A1·A2)   '
        '[precharge+eval | predriver | keeper/cut-fb | output]   12 FETs')
    d += elm.Label().at((8, -0.9)).label(
        'gates labelled with net name connect to that net  (green=dyn, purple=out_b, red=Out)',
        color='0.4')
print("wrote", out)

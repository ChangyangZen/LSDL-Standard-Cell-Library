#!/usr/bin/env python3
"""librecell_postprocess.py — add GF180 5V marker layers to a lclayout GDS.

lclayout's GF180 output writes physical + implant layers (implants are now
generated in codegen: standalone._09_post_process), but NOT the 5V marker
layers, so the official GF180 DRC treats gates as 3.3V (PL.5*_LV etc.). This
adds the two NON-electrical markers (pure rectangles, safe as a post-process):

  - DUALGATE (55/0): all poly+COMP grown by 0.4um (DV.8: dualgate encloses
    poly2 by >=0.4um). Marks the cell as 5V.
  - FET5VDEF (112/1): cell boundary (5V device definition).

Only run this AFTER PL.5 is clean at the MV (0.3um) requirement — marking the
cell 5V raises field-poly-to-COMP from 0.1um to 0.3um.

Usage: librecell_postprocess.py <in.gds> <out.gds> <topcell>
"""
from __future__ import annotations
import sys
import pya

L_COMP  = pya.LayerInfo(22, 0)
L_POLY  = pya.LayerInfo(30, 0)
L_DUALG = pya.LayerInfo(55, 0)
L_FET5V = pya.LayerInfo(112, 1)
L_BNDRY = pya.LayerInfo(63, 0)
DUALGATE_OH = 400  # nm, DV.8 dualgate encloses poly2 by >=0.4um


def region(layout, top, linfo):
    idx = layout.find_layer(linfo)
    return pya.Region() if idx is None else pya.Region(top.begin_shapes_rec(idx))


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    in_gds, out_gds, topname = sys.argv[1:4]
    ly = pya.Layout(); ly.read(in_gds)
    nm = lambda v: int(round(v / 1000.0 / ly.dbu))
    top = next((c for c in ly.each_cell() if c.name == topname), None)
    if top is None:
        sys.exit(f"top cell {topname} not found")

    # DUALGATE row convention (abutment-safe): span the cell BOUNDARY in X so
    # neighboring cells' markers abut into one continuous row band (no DV.2 seam
    # gap). Y is device-bounded (poly+COMP bbox grown 0.4um) to satisfy DV.8
    # (dualgate encloses poly2 by >=0.4um). X-enclosure of poly is provided by the
    # boundary-to-poly margin (>=0.4um for these cells).
    active = region(ly, top, L_COMP) + region(ly, top, L_POLY)
    ab = active.bbox()
    bnd = region(ly, top, L_BNDRY)
    x0, x1 = (bnd.bbox().left, bnd.bbox().right) if not bnd.is_empty() else (ab.left, ab.right)
    dg_box = pya.Box(x0, ab.bottom - nm(DUALGATE_OH), x1, ab.top + nm(DUALGATE_OH))
    top.shapes(ly.layer(L_DUALG)).insert(pya.Region(dg_box))
    dualgate = pya.Region(dg_box)
    top.shapes(ly.layer(L_FET5V)).insert(pya.Region(top.bbox()))

    # Row-contract well bands (abutment-safe): rectangularize NWELL/LVPWELL to
    # clean boundary-width bands so abutted wells form continuous bands with no
    # seam notch (lclayout's per-FET well boxes leave a jagged top edge -> NW.2a
    # at the abutment overhang). NWELL = its bbox; LVPWELL = its bbox in x, from
    # its bottom up to the NWELL bottom (no overlap).
    L_NWELL=pya.LayerInfo(21,0); L_LVPW=pya.LayerInfo(204,0)
    nw=region(ly,top,L_NWELL)
    if not nw.is_empty():
        nb=nw.bbox()
        xb0,xb1=(x0,x1)
        ti=ly.layer(L_NWELL); top.shapes(ti).clear()
        top.shapes(ti).insert(pya.Box(xb0,nb.bottom,xb1,nb.top))
        lv=region(ly,top,L_LVPW)
        if not lv.is_empty():
            lb=lv.bbox(); li=ly.layer(L_LVPW); top.shapes(li).clear()
            top.shapes(li).insert(pya.Box(xb0,lb.bottom,xb1,nb.bottom))

    ly.write(out_gds)
    print(f"wrote {out_gds}: +DUALGATE({dualgate.size()}) +FET5VDEF(1)")


if __name__ == "__main__":
    main()

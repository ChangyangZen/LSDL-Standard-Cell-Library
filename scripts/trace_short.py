#!/usr/bin/env python3
"""trace_short.py — locate router-created net shorts in a (shorted) cell GDS.

lclayout annotates each net with text labels on the metal carrying it. A SHORT
shows up as a single metal polygon that contains labels of TWO different intended
nets. This walks met1/met2/poly polygons, collects the distinct net-label strings
whose label point lies inside each polygon, and reports any polygon carrying >1
net name — that polygon IS the bridge. Reports layer + bbox + the net pair.

Usage: trace_short.py <gds> <topcell>
"""
from __future__ import annotations
import sys
import pya

LAYERS = [('met1', 34, 0), ('met2', 36, 0), ('poly', 30, 0),
          ('via1', 35, 0), ('licon', 33, 0)]


def main():
    gds, top = sys.argv[1], sys.argv[2]
    ly = pya.Layout(); ly.read(gds); dbu = ly.dbu
    cell = next(c for c in ly.each_cell() if c.name.lower() == top.lower())

    # gather all text labels (net markers) with positions, per layer index
    labels = []  # (name, x_dbu, y_dbu, layer_idx)
    for li in range(ly.layers()):
        for s in cell.shapes(li).each():
            if s.is_text():
                labels.append((s.text.string, s.text.x, s.text.y, li))

    print(f"net labels present: {sorted({n for n,_,_,_ in labels})}")
    found = False
    for name, num, dt in LAYERS:
        idx = ly.find_layer(pya.LayerInfo(num, dt))
        if idx is None:
            continue
        # merge polygons on this layer so each connected piece is one polygon
        reg = pya.Region(cell.shapes(idx)); reg.merge()
        for poly in reg.each():
            preg = pya.Region(poly)
            box = poly.bbox()
            names = set()
            for lname, lx, ly_, _ in labels:
                if not box.contains(pya.Point(lx, ly_)):
                    continue
                # proper point-in-polygon: the merged polygon must actually overlap
                # a 1-dbu box at the label point (not just its bounding box).
                if not (preg & pya.Region(pya.Box(lx-1, ly_-1, lx+1, ly_+1))).is_empty():
                    names.add(lname)
            if len(names) > 1:
                found = True
                b = box
                print(f"SHORT on {name} ({num}/{dt}): nets {sorted(names)}  "
                      f"bbox=({b.left*dbu:.3f},{b.bottom*dbu:.3f})..({b.right*dbu:.3f},{b.top*dbu:.3f}) "
                      f"[{(b.right-b.left)*dbu:.2f}x{(b.top-b.bottom)*dbu:.2f}um]")
    if not found:
        print("no single-polygon multi-net bridge found on metal/poly "
              "(short may be through a via stack or diffusion — trace further).")


if __name__ == '__main__':
    main()

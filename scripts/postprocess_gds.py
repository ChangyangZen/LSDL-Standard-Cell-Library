#!/usr/bin/env python3
"""postprocess_gds.py — add GF180MCU 5V cell markers that Magic does
not auto-generate (or generates fragmented):

  - DUALGATE (55/0)  — single rectangle covering the entire cell
                       with 0.28 um overhang on all sides. The
                       Magic tech derives DUALGATE per-FET; for
                       wide cells the fragments don't merge, so
                       DV.8 (dualgate enclose poly2) fires. Adding
                       one big rect makes the boolean union span
                       the whole cell.
  - FET5VDEF (112/1) — single rectangle at the exact cell boundary,
                       marking it as a 5V cell.

Usage:
    postprocess_gds.py <input.gds> <output.gds>
"""

from __future__ import annotations
import sys

import pya


def add_markers(in_path: str, out_path: str):
    ly = pya.Layout()
    ly.read(in_path)
    # ly.each_top_cell() yields integer cell indices; convert to Cell.
    top_cells = [ly.cell(i) for i in ly.each_top_cell()]
    if not top_cells:
        sys.exit('no top cell')
    # Pick the largest (= the real cell, not sub-FETs).
    top = max(top_cells, key=lambda c: c.bbox().area())

    bb = top.bbox()
    dbu = ly.dbu  # database unit in microns (typically 0.001)

    # Cell extent in microns.
    x0 = bb.left   * dbu
    y0 = bb.bottom * dbu
    x1 = bb.right  * dbu
    y1 = bb.top    * dbu

    # DUALGATE: cell extent + 0.28 um overhang on each side (matches stock).
    oh = 0.28
    dg_idx = ly.layer(pya.LayerInfo(55, 0))
    top.shapes(dg_idx).insert(pya.Box(
        round((x0 - oh) / dbu), round((y0 - oh) / dbu),
        round((x1 + oh) / dbu), round((y1 + oh) / dbu)))

    # FET5VDEF: exactly at cell boundary (matches stock).
    f5_idx = ly.layer(pya.LayerInfo(112, 1))
    top.shapes(f5_idx).insert(pya.Box(
        round(x0 / dbu), round(y0 / dbu),
        round(x1 / dbu), round(y1 / dbu)))

    ly.write(out_path)
    print(f'wrote {out_path}: added DUALGATE ({x0-oh:.2f},{y0-oh:.2f})..'
          f'({x1+oh:.2f},{y1+oh:.2f}) and FET5VDEF ({x0:.2f},{y0:.2f})..'
          f'({x1:.2f},{y1:.2f})')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__.strip())
    add_markers(sys.argv[1], sys.argv[2])

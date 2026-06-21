#!/usr/bin/env python3
"""mk_ports_gds.py — produce a port-clean copy of a cell GDS for LVS/port work.

lclayout annotates EVERY net with many text labels on every layer (e.g. DYN x48),
so Magic's `port makeall` would promote all of them. This strips ALL text and
inserts exactly one I/O port label per pin on metal1 (34/0), at a position
AUTO-DETECTED from the net's existing metal1 labels. `port makeall` then yields a
clean `.subckt <cell> <pins...>`.

Usage:
  mk_ports_gds.py <in.gds> <out.gds> <topcell> --pins A1,A2,Clk,Out,VPWR,VGND
  mk_ports_gds.py <in.gds> <out.gds> <topcell>        # default = inverter pins
  mk_ports_gds.py ... --pins NAME@x,y;NAME2@x2,y2     # explicit positions (override)
"""
from __future__ import annotations
import sys
import pya

M1 = pya.LayerInfo(34, 0)
DEFAULT_PINS = ['A', 'Clk', 'Out', 'VPWR', 'VGND']


def detect_positions(ly, cell, names):
    """For each requested pin name, find a representative metal1 label position
    (case-insensitive). Returns {name:(x_dbu,y_dbu)}; raises if any missing."""
    m1 = ly.find_layer(M1)
    found = {}  # upper-name -> (x,y) of first metal1 text seen
    if m1 is not None:
        for s in cell.shapes(m1).each():
            if s.is_text():
                u = s.text.string.upper()
                found.setdefault(u, (s.text.x, s.text.y))
    pos = {}
    missing = []
    for n in names:
        key = n.upper()
        if key in found:
            pos[n] = found[key]
        else:
            missing.append(n)
    if missing:
        raise SystemExit(f"no metal1 label found for pins: {missing} "
                         f"(have: {sorted(found)})")
    return pos


def main():
    args = sys.argv[1:]
    in_gds, out_gds, top = args[0], args[1], args[2]
    names = DEFAULT_PINS
    explicit = {}
    rest = args[3:]
    i = 0
    while i < len(rest):
        if rest[i] == '--pins':
            names = rest[i + 1].split(','); i += 2
        elif '@' in rest[i]:
            n, xy = rest[i].split('@'); x, y = xy.split(','); explicit[n] = (float(x), float(y)); i += 1
        else:
            i += 1

    ly = pya.Layout(); ly.read(in_gds)
    nm = lambda v: int(round(v / ly.dbu))
    cell = next(c for c in ly.each_cell() if c.name == top)

    # auto-detect positions for pins without an explicit override
    auto_names = [n for n in names if n not in explicit]
    pos = detect_positions(ly, cell, auto_names) if auto_names else {}
    for n, (x, y) in explicit.items():
        pos[n] = (nm(x), nm(y))

    # strip ALL text shapes on every layer
    removed = 0
    for li in range(ly.layers()):
        sh = cell.shapes(li)
        for s in [s for s in sh.each() if s.is_text()]:
            sh.erase(s); removed += 1

    # insert exactly one I/O label per pin on metal1
    m1 = ly.layer(M1)
    for n in names:
        x, y = pos[n]
        cell.shapes(m1).insert(pya.Text(n, pya.Trans(int(x), int(y))))

    ly.write(out_gds)
    print(f"stripped {removed} texts; wrote {out_gds} with pins {names}")


if __name__ == '__main__':
    main()

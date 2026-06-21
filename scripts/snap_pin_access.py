#!/usr/bin/env python3
"""snap_pin_access.py — make signal pins reachable on the LibreLane PnR grid.

lclayout places met2 signal-pin pads on its own grid (gate pitch / 2 = 0.84um,
offset 0), which is NOT the LibreLane met2 routing grid (vertical tracks at
x = 0.28 + 0.56*k). Pins that don't land on a track get NO access point in
TritonRoute. This adds an ON-NET met2 access pad centered on the nearest met2
track, unioned with the original pad so it stays electrically connected and the
underlying via1 stays covered. Internal routing is untouched. Power pins
(VPWR/VGND) are NOT snapped — they're rails, accessed by the PDN.

Outputs: snapped GDS + a pin_map.json {name:{layer,rect[x1,y1,x2,y2]_um}} that
fix_lef_pins.py uses so the LEF PIN rect == the real GDS access pad.

The pin-pad geometry is taken from the lclayout LEF (authoritative), not from the
GDS labels — lclayout writes hundreds of net-annotation labels, so "nearest GDS
label" is unreliable; the LEF has exactly one met2 PORT rect per signal pin.

Usage:
  snap_pin_access.py <in.gds> <out.gds> <topcell> <pin_map.json> <cell.lef>
      --signals A1,A2,Clk,Out [--m2-offset 0.28 --m2-pitch 0.56 --via-half 0.28]
"""
from __future__ import annotations
import json, re, sys
import pya

M2 = pya.LayerInfo(36, 0)


def candidate_tracks(cx, off, pitch):
    """The two nearest tracks to cx, nearest first."""
    k = (cx - off) / pitch
    import math
    lo = off + math.floor(k) * pitch
    hi = off + math.ceil(k) * pitch
    cands = sorted({round(lo, 6), round(hi, 6)}, key=lambda x: abs(x - cx))
    return cands


def lef_met2_rects(lef, macro, signals):
    """{pinname: (x1,y1,x2,y2)} of the met2 PORT rect, for the given signal names."""
    txt = open(lef).read()
    m = re.search(rf'MACRO\s+{re.escape(macro)}\b(.*?)END\s+{re.escape(macro)}\b', txt, re.S | re.I) \
        or re.search(r'MACRO\s+(\S+)\b(.*?)END\s+\1\b', txt, re.S | re.I)
    body = m.group(1) if m.lastindex == 1 else m.group(2)
    up = {s.upper(): s for s in signals}
    out = {}
    for pm in re.finditer(r'PIN\s+(\S+)\b(.*?)END\s+\1\b', body, re.S | re.I):
        nm = pm.group(1)
        if nm.upper() not in up:
            continue
        cur = None
        for ln in pm.group(2).splitlines():
            lm = re.search(r'LAYER\s+(\S+)', ln, re.I)
            if lm: cur = lm.group(1).lower()
            rm = re.search(r'RECT\s+([\d.\-]+)\s+([\d.\-]+)\s+([\d.\-]+)\s+([\d.\-]+)', ln, re.I)
            if rm and cur == 'met2':
                out[up[nm.upper()]] = tuple(float(rm.group(i)) for i in range(1, 5))
    return out


def main():
    a = sys.argv[1:]
    in_gds, out_gds, top, pinmap_path, lef = a[0], a[1], a[2], a[3], a[4]
    signals, off, pitch, vhalf = [], 0.28, 0.56, 0.28
    i = 5
    while i < len(a):
        if a[i] == '--signals': signals = a[i+1].split(','); i += 2
        elif a[i] == '--m2-offset': off = float(a[i+1]); i += 2
        elif a[i] == '--m2-pitch': pitch = float(a[i+1]); i += 2
        elif a[i] == '--via-half': vhalf = float(a[i+1]); i += 2
        else: i += 1

    ly = pya.Layout(); ly.read(in_gds); dbu = ly.dbu
    nm = lambda v: int(round(v / dbu))
    cell = next(c for c in ly.each_cell() if c.name == top)
    m2 = ly.layer(M2)

    pads = lef_met2_rects(lef, top, signals)
    pin_map = {}
    for name in signals:
        if name not in pads:
            sys.exit(f"snap: no met2 PORT rect for signal pin {name} in LEF")
        x1, y1, x2, y2 = pads[name]
        cx = (x1 + x2) / 2
        # met2 NOT belonging to this pin (everything not touching the original pad)
        all_m2 = pya.Region(cell.shapes(m2)); all_m2.merge()
        orig = pya.Region(pya.Box(nm(x1), nm(y1), nm(x2), nm(y2)))
        other = all_m2 - all_m2.interacting(orig)
        m2sp = nm(0.28)  # M2.2a min spacing
        # pick the nearest track whose access pad clears M2 spacing to other nets;
        # fall back to nearest if none clears (flagged).
        chosen, clean = None, False
        for xt in candidate_tracks(cx, off, pitch):
            nx1, nx2 = min(x1, xt - vhalf), max(x2, xt + vhalf)
            box = pya.Box(nm(nx1), nm(y1), nm(nx2), nm(y2))
            if (pya.Region(box).sized(m2sp) & other).is_empty():
                chosen, clean = xt, True; break
        if chosen is None:
            chosen = candidate_tracks(cx, off, pitch)[0]
        xt = chosen
        nx1, nx2 = min(x1, xt - vhalf), max(x2, xt + vhalf)
        cell.shapes(m2).insert(pya.Box(nm(nx1), nm(y1), nm(nx2), nm(y2)))
        if not clean:
            print(f"  WARN {name}: no M2-clean track; used nearest {xt:.2f}")
        pin_map[name] = {'layer': 'met2',
                         'rect': [round(nx1,3), round(y1,3), round(nx2,3), round(y2,3)],
                         'track': round(xt, 3)}
        print(f"  {name}: pad x[{x1:.2f},{x2:.2f}] -> track {xt:.2f} -> "
              f"access x[{nx1:.2f},{nx2:.2f}] (w={nx2-nx1:.2f})")

    ly.write(out_gds)
    json.dump(pin_map, open(pinmap_path, 'w'), indent=2)
    print(f"wrote {out_gds} + {pinmap_path}")


if __name__ == '__main__':
    main()

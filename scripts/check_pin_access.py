#!/usr/bin/env python3
"""check_pin_access.py — pin-access gate against the LibreLane/OpenROAD track grid.

A signal pin is routable only if a routing track of its layer passes through it,
so the detailed router (OpenROAD/TritonRoute) can place an access point. Metal2
routes VERTICAL (X-tracks), Metal1/Metal3 HORIZONTAL (Y-tracks), per the GF180
tech LEF + tracks.info. lclayout places pins on its OWN grid, which need not match
the PnR grid — this gate catches off-grid pins before they reach LibreLane.

Usage: check_pin_access.py <cell.lef> <tracks.info> <topcell>
Exit 0 = PASS (every signal pin on-grid), 1 = FAIL.
"""
from __future__ import annotations
import re, sys

LEF2TECH = {'met1': 'Metal1', 'met2': 'Metal2', 'met3': 'Metal3',
            'met4': 'Metal4', 'met5': 'Metal5'}
# routing direction per tech layer (from gf180 tech LEF): which track axis carries
# the routing wire. VERTICAL -> X tracks; HORIZONTAL -> Y tracks.
ROUTE_AXIS = {'Metal1': 'Y', 'Metal2': 'X', 'Metal3': 'Y', 'Metal4': 'X', 'Metal5': 'Y'}
EPS = 1e-6


def parse_tracks(path):
    """{layer: {'X': (offset,pitch), 'Y': (offset,pitch)}}"""
    t = {}
    for ln in open(path):
        p = ln.split()
        if len(p) == 4:
            lyr, axis, off, pitch = p[0], p[1], float(p[2]), float(p[3])
            t.setdefault(lyr, {})[axis] = (off, pitch)
    return t


def parse_pins(lef, macro):
    txt = open(lef).read()
    m = re.search(rf'MACRO\s+{re.escape(macro)}\b(.*?)END\s+{re.escape(macro)}\b', txt, re.S | re.I) \
        or re.search(r'MACRO\s+(\S+)\b(.*?)END\s+\1\b', txt, re.S | re.I)
    body = m.group(1) if m.lastindex == 1 else m.group(2)
    pins = {}
    for pm in re.finditer(r'PIN\s+(\S+)\b(.*?)END\s+\1\b', body, re.S | re.I):
        name, pb = pm.group(1), pm.group(2)
        use = (re.search(r'USE\s+(\S+)', pb, re.I) or [None, ''])[1]
        ports, cur = [], None
        for ln in pb.splitlines():
            lm = re.search(r'LAYER\s+(\S+)', ln, re.I)
            if lm: cur = lm.group(1)
            rm = re.search(r'RECT\s+([\d.\-]+)\s+([\d.\-]+)\s+([\d.\-]+)\s+([\d.\-]+)', ln, re.I)
            if rm and cur:
                ports.append((cur, tuple(float(rm.group(i)) for i in range(1, 5))))
        pins[name] = {'use': use.upper(), 'ports': ports}
    return pins


def track_in(lo, hi, off, pitch):
    """Is there a track (off + n*pitch) within [lo,hi]? Return the track or None."""
    import math
    n0 = math.ceil((lo - off) / pitch - EPS)
    x = off + n0 * pitch
    return x if x <= hi + EPS else None


def main():
    lef, tracks_info, top = sys.argv[1], sys.argv[2], sys.argv[3]
    tracks = parse_tracks(tracks_info)
    pins = parse_pins(lef, top)
    fails, lines = [], []
    for name, info in pins.items():
        if info['use'] in ('POWER', 'GROUND'):
            continue  # rails accessed by PDN straps, not signal tracks
        # a pin is accessible if ANY of its ports has a routing track through it
        ok = False; detail = []
        for lyr, (x1, y1, x2, y2) in info['ports']:
            tech = LEF2TECH.get(lyr.lower())
            if tech not in ROUTE_AXIS or tech not in tracks:
                continue
            axis = ROUTE_AXIS[tech]
            off, pitch = tracks[tech][axis]
            lo, hi = (x1, x2) if axis == 'X' else (y1, y2)
            tk = track_in(lo, hi, off, pitch)
            detail.append(f"{lyr}/{axis}@{tk if tk is not None else 'none'}")
            if tk is not None:
                ok = True
        lines.append(f"  {name:5} use={info['use']:7} {'OK ' if ok else 'NO-ACCESS'} [{', '.join(detail)}]")
        if not ok:
            fails.append(name)
    print(f"pin-access {top}:")
    print('\n'.join(lines))
    if fails:
        print(f"FAIL: no on-grid access point for signal pins: {fails}"); sys.exit(1)
    print("PASS")


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""audit_lef.py — LEF-vs-GDS sanity audit for a generated standard cell.

Checks (the W1-A1 collateral gate):
  1. MACRO SIZE matches the GDS boundary (63/0) bbox.
  2. Every PIN's PORT RECT lies on real metal of that layer in the GDS
     (rect is covered by the layer's geometry).
  3. DIRECTION/USE per pin are consistent with name (inputs INPUT/SIGNAL,
     Out* OUTPUT/SIGNAL, VPWR POWER, VGND GROUND).
  4. VPWR and VGND PINs are present.

Usage: audit_lef.py <lef> <gds> <topcell>
Exit 0 = PASS, 1 = FAIL.
"""
from __future__ import annotations
import re, sys
import pya

# LEF layer name -> GDS (layer,datatype)
LEF2GDS = {'met1': (34, 0), 'met2': (36, 0), 'met3': (42, 0),
           'poly2': (30, 0), 'polycont': (33, 0)}
BNDRY = (63, 0)
TOL = 0.02  # um


def classify(name):
    u = name.upper()
    if u in ('VPWR', 'VDD', 'VCC'): return ('INOUT', 'POWER')
    if u in ('VGND', 'VSS', 'GND'): return ('INOUT', 'GROUND')
    if u.startswith('OUT') or u in ('Y', 'Z', 'ZN', 'Q', 'QN'): return ('OUTPUT', 'SIGNAL')
    return ('INPUT', 'SIGNAL')


def parse_lef(path, macro):
    """Return (size_w, size_h, {pin:{'dir','use','ports':[(layer,(x1,y1,x2,y2))]}})."""
    txt = open(path).read()
    # isolate the MACRO block
    m = re.search(rf'MACRO\s+{re.escape(macro)}\b(.*?)END\s+{re.escape(macro)}\b',
                  txt, re.S | re.I)
    if not m:
        # macro name case may differ; grab first MACRO block
        m = re.search(r'MACRO\s+(\S+)\b(.*?)END\s+\1\b', txt, re.S | re.I)
        body = m.group(2)
    else:
        body = m.group(1)
    sm = re.search(r'SIZE\s+([\d.]+)\s+BY\s+([\d.]+)', body, re.I)
    size = (float(sm.group(1)), float(sm.group(2))) if sm else (None, None)
    pins = {}
    for pm in re.finditer(r'PIN\s+(\S+)\b(.*?)END\s+\1\b', body, re.S | re.I):
        name, pb = pm.group(1), pm.group(2)
        d = re.search(r'DIRECTION\s+(\S+)', pb, re.I)
        u = re.search(r'USE\s+(\S+)', pb, re.I)
        ports = []
        cur = None
        for ln in pb.splitlines():
            lm = re.search(r'LAYER\s+(\S+)', ln, re.I)
            if lm: cur = lm.group(1)
            rm = re.search(r'RECT\s+([\d.\-]+)\s+([\d.\-]+)\s+([\d.\-]+)\s+([\d.\-]+)', ln, re.I)
            if rm and cur:
                ports.append((cur, tuple(float(rm.group(i)) for i in range(1, 5))))
        pins[name] = {'dir': d.group(1) if d else None,
                      'use': u.group(1) if u else None, 'ports': ports}
    return size[0], size[1], pins


def main():
    lef, gds, top = sys.argv[1], sys.argv[2], sys.argv[3]
    ly = pya.Layout(); ly.read(gds)
    cell = next((c for c in ly.each_cell() if c.name.upper() == top.upper()), ly.top_cell())
    dbu = ly.dbu

    def region(gl):
        idx = ly.find_layer(pya.LayerInfo(*gl))
        return pya.Region() if idx is None else pya.Region(cell.begin_shapes_rec(idx))

    w, h, pins = parse_lef(lef, top)
    fails = []

    # 1. SIZE vs boundary
    bnd = region(BNDRY).bbox()
    bw, bh = (bnd.right - bnd.left) * dbu, (bnd.top - bnd.bottom) * dbu
    if w is None or abs(w - bw) > TOL or abs(h - bh) > TOL:
        fails.append(f"SIZE {w}x{h} != boundary {bw:.2f}x{bh:.2f}")

    # 4. power pins present
    upper = {p.upper() for p in pins}
    for req in ('VPWR', 'VGND'):
        if req not in upper:
            fails.append(f"missing power PIN {req}")

    # 2+3. each pin: ports covered by real metal, dir/use correct
    for name, info in pins.items():
        exp_dir, exp_use = classify(name)
        if info['dir'] and info['dir'].upper() != exp_dir:
            fails.append(f"{name}: DIRECTION {info['dir']} != {exp_dir}")
        if info['use'] and info['use'].upper() != exp_use:
            fails.append(f"{name}: USE {info['use']} != {exp_use}")
        if not info['ports']:
            fails.append(f"{name}: no PORT rect"); continue
        for lyr, (x1, y1, x2, y2) in info['ports']:
            gl = LEF2GDS.get(lyr.lower())
            if gl is None:
                fails.append(f"{name}: unknown LEF layer {lyr}"); continue
            rect = pya.Region(pya.Box(int(round(x1/dbu)), int(round(y1/dbu)),
                                      int(round(x2/dbu)), int(round(y2/dbu))))
            # erode by 1 dbu so sub-grid edge coincidence isn't a false positive;
            # this still catches a pin meaningfully off-metal (wrong layer/place).
            rect = rect.sized(-1)
            uncovered = rect - region(gl)
            if uncovered.area() * dbu * dbu > 0.001:
                fails.append(f"{name}: PORT on {lyr} not fully on metal "
                             f"(uncovered {uncovered.area()*dbu*dbu:.4f} um^2 @ {x1},{y1})")

    print(f"LEF audit {top}: SIZE {w}x{h} (gds {bw:.2f}x{bh:.2f}); "
          f"{len(pins)} pins {sorted(pins)}")
    if fails:
        print("FAIL:"); [print("  -", f) for f in fails]; sys.exit(1)
    print("PASS")


if __name__ == '__main__':
    main()

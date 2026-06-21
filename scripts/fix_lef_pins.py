#!/usr/bin/env python3
"""fix_lef_pins.py — set correct DIRECTION/USE per pin in a lclayout LEF, and
(optionally) replace signal-pin PORT rects with the snapped pin-access pads so
the LEF matches the real GDS metal.

lclayout writes every PIN as DIRECTION INOUT and signal/power USE loosely. PnR
needs proper directions. With --pin-map (from snap_pin_access.py), each signal
pin's met2 RECT is replaced by the snapped access pad — GDS and LEF must agree
or the router targets a phantom access point.

Usage: fix_lef_pins.py <in.lef> <out.lef> [pin_map.json]
"""
from __future__ import annotations
import sys, re, json

# Explicit pin specs (upper-name -> (DIRECTION, USE)). Names not listed here fall
# back to classify(): VPWR/VGND power/ground, Out* output, everything else input.
SPEC = {
    'OUT':  ('OUTPUT', 'SIGNAL'),
    'VPWR': ('INOUT',  'POWER'),
    'VGND': ('INOUT',  'GROUND'),
}

def classify(name):
    u = name.upper()
    if u in SPEC:
        return SPEC[u]
    if u in ('VPWR', 'VDD', 'VCC'):
        return ('INOUT', 'POWER')
    if u in ('VGND', 'VSS', 'GND'):
        return ('INOUT', 'GROUND')
    if u.startswith('OUT') or u in ('Y', 'Z', 'ZN', 'Q', 'QN'):
        return ('OUTPUT', 'SIGNAL')
    return ('INPUT', 'SIGNAL')   # A, A1, A2, Clk, B, S, ... are inputs


def main():
    src, dst = sys.argv[1], sys.argv[2]
    # pin_map keyed case-insensitively: upper-name -> {'layer','rect'}
    pin_map = {}
    if len(sys.argv) > 3:
        for k, v in json.load(open(sys.argv[3])).items():
            pin_map[k.upper()] = v
    lines = open(src).read().splitlines()
    out = []
    cur = None      # current PIN (upper)
    cur_layer = None
    for ln in lines:
        m = re.match(r'\s*PIN\s+(\S+)', ln)
        if m:
            cur = m.group(1).upper(); cur_layer = None
        elif re.match(r'\s*END\s+\S+', ln) and cur and ln.strip().split()[1].upper() == cur:
            cur = None; cur_layer = None
        if cur is not None:
            d, u = classify(cur)
            if re.match(r'\s*DIRECTION\s', ln):
                ind = ln[:len(ln)-len(ln.lstrip())]
                out.append(f'{ind}DIRECTION {d} ;'); continue
            if re.match(r'\s*USE\s', ln):
                ind = ln[:len(ln)-len(ln.lstrip())]
                out.append(f'{ind}USE {u} ;'); continue
            lm = re.match(r'(\s*)LAYER\s+(\S+)', ln)
            if lm:
                cur_layer = lm.group(2)
            # replace the snapped signal pin's met2 RECT with the access-pad rect
            rm = re.match(r'(\s*)RECT\s', ln)
            if rm and cur in pin_map and cur_layer == pin_map[cur]['layer']:
                ind = rm.group(1); x1, y1, x2, y2 = pin_map[cur]['rect']
                out.append(f'{ind}RECT {x1:.8f} {y1:.8f} {x2:.8f} {y2:.8f} ;'); continue
        out.append(ln)
    open(dst, 'w').write('\n'.join(out) + '\n')
    print(f"wrote {dst} with corrected DIRECTION/USE"
          + (f" and snapped rects for {sorted(pin_map)}" if pin_map else ""))


if __name__ == '__main__':
    main()

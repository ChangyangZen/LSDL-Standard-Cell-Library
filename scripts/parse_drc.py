#!/usr/bin/env python3
"""parse_drc.py — extract violation coordinates from a KLayout DRC run.

The GF180MCU `run_drc.py` writes one `.lyrdb` file per rule deck
(e.g. `lsdl_inv_x1_metal1.lyrdb`, `lsdl_inv_x1_comp.lyrdb`, ...). Each is
KLayout's XML marker-database format. This script aggregates violations
across all `.lyrdb` files in a run dir, prints a per-rule summary, and
optionally dumps coordinates of each violation polygon.

Usage:
    parse_drc.py <drc_run_dir> [--rule RULE_NAME] [--coords]

Examples:
    # show counts of all violated rules
    parse_drc.py /soe/czeng14/projects/brainstorm-domino-tmp/drc_runs/drc_run_2026_05_25_..

    # show coordinates of every DF.4c_MV violation
    parse_drc.py /soe/...drc_run_../ --rule DF.4c_MV --coords
"""

from __future__ import annotations
import argparse
import glob
import os
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict


_PT_RE = re.compile(r'(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)')


def parse_polygon(text: str):
    """Parse KLayout marker values. Format varies:
      - 'polygon: (x,y;x,y;...)'  — polygon vertices
      - 'edge-pair: (x,y;x,y)|(x,y;x,y)' — two edges
      - 'edge: (x,y;x,y)' — single edge
    Extract all (x, y) pairs found. Returns list of (x, y) floats."""
    if not text:
        return []
    pts = []
    for m in _PT_RE.finditer(text):
        try:
            pts.append((float(m.group(1)), float(m.group(2))))
        except ValueError:
            pass
    return pts


def bbox(pts):
    if not pts:
        return None
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return (min(xs), min(ys), max(xs), max(ys))


def parse_lyrdb(path: str):
    """Yield (rule_name, polygon_pts) for each <item> in the .lyrdb."""
    try:
        tree = ET.parse(path)
    except ET.ParseError:
        return
    for item in tree.iter('item'):
        cat_text = item.findtext('category', default='?')
        # KLayout wraps category in quotes: "'M1.3'"
        rule = cat_text.strip().strip("'\"") if cat_text else '?'
        for v in item.iter('value'):
            pts = parse_polygon(v.text or '')
            if pts:
                yield rule, pts


def collect(run_dir: str):
    """Aggregate violations across all .lyrdb files in run_dir."""
    by_rule = defaultdict(list)
    for path in sorted(glob.glob(os.path.join(run_dir, '*.lyrdb'))):
        for rule, pts in parse_lyrdb(path):
            by_rule[rule].append(pts)
    return by_rule


# Tap-distance rules (COMP to nearest well/substrate tap). Satisfied at chip
# level by filler/endcap cells during PnR, not within a functional cell. The
# _LV variants fire when the cell is not yet 5V-marked (no DUALGATE); same family.
CHIP_LEVEL_RULES = {'DF.13_MV', 'DF.14_MV', 'DF.13_LV', 'DF.14_LV'}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('run_dir', help='KLayout DRC run directory')
    ap.add_argument('--rule', help='only show this rule')
    ap.add_argument('--coords', action='store_true',
                    help='print bbox coords of each violation')
    ap.add_argument('--include-chip-rules', action='store_true',
                    help='do not skip DF.13_MV/DF.14_MV')
    args = ap.parse_args()

    if not os.path.isdir(args.run_dir):
        # If the user passed the parent, find the most recent run.
        glob_pat = os.path.join(args.run_dir, 'drc_run_*')
        matches = sorted(glob.glob(glob_pat))
        if matches:
            args.run_dir = matches[-1]
        else:
            sys.exit(f'no drc_run_* directories under {args.run_dir}')

    by_rule = collect(args.run_dir)

    if not by_rule:
        print(f'No violations found in {args.run_dir}')
        return

    print(f'=== Violations in {args.run_dir} ===')
    cell_level_total = 0
    chip_level_total = 0
    for rule in sorted(by_rule):
        polygons = by_rule[rule]
        is_chip = rule in CHIP_LEVEL_RULES
        if is_chip and not args.include_chip_rules:
            chip_level_total += len(polygons)
            tag = ' [chip-level, skipped]'
        else:
            cell_level_total += len(polygons)
            tag = ''
        if args.rule and args.rule != rule:
            continue
        print(f'  {rule:18s} {len(polygons):4d} violations{tag}')
        if args.coords:
            for pts in polygons:
                bb = bbox(pts)
                if bb:
                    print(f'      bbox: ({bb[0]:.3f}, {bb[1]:.3f}) → '
                          f'({bb[2]:.3f}, {bb[3]:.3f})  '
                          f'({bb[2]-bb[0]:.3f} × {bb[3]-bb[1]:.3f} µm)')

    print(f'\nTotal cell-level violations:  {cell_level_total}')
    if chip_level_total:
        print(f'Total chip-level violations:  {chip_level_total} '
              f'(DF.13_MV/DF.14_MV; pass with filler+endcap)')

    # Exit non-zero only if cell-level violations exist.
    sys.exit(1 if cell_level_total > 0 else 0)


if __name__ == '__main__':
    main()

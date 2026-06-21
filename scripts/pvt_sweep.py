#!/usr/bin/env python3
"""pvt_sweep.py — sweep an LSDL cell testbench across PVT corners.

Generates 45 PVT variants per cell (5 corners × 3 temps × 3 VDDs), runs
each in the IIC-OSIC-TOOLS container, parses .meas output, applies the
cell's pass criteria, and prints a results table.

Usage:
    pvt_sweep.py <cell_name>          # e.g. lsdl_inv_x1
    pvt_sweep.py --all                # all 9 Wave 1 cells

Per-PVT testbench files land in lsdl_lib/testbench/_gen/<cell>/ so the
container can see them via the existing /mada/users/czeng14/projects/brainstorm/domino/lsdl_lib mount. Logs go to
/soe/czeng14/projects/brainstorm-domino-tmp/pvt_sweep/.
"""

from __future__ import annotations
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path('/mada/users/czeng14/projects/brainstorm/domino')
LSDL_LIB = PROJECT_ROOT / 'lsdl_lib'
TB_GEN_DIR = LSDL_LIB / 'testbench' / '_gen'
TMP_DIR = Path('/soe/czeng14/projects/brainstorm-domino-tmp/pvt_sweep')
PVT_DIR = LSDL_LIB / 'pvt'   # durable JSON summaries (version-controlled)
WRAPPER = LSDL_LIB / 'scripts' / 'run_in_container.sh'

CORNERS = ['typical', 'ss', 'ff', 'sf', 'fs']
TEMPS_C = [-40, 25, 125]
VDDS_V = [4.75, 5.0, 5.25]

# Pass criteria per cell. 'max': measurement must be <= bound.
# 'min': measurement must be >= bound.
PASS_CRITERIA = {
    'lsdl_inv_x1': {
        'tpd_eval_lh':       {'max': 2.0e-9},   # < 2 ns at slowest corner
        'v_dyn_low_min':     {'max': 0.5},      # dyn fully discharges
        'v_out_final':       {'min': 4.0},      # latched-high after A=0 cycle
    },
    'lsdl_nand2_x1': {
        'tpd_eval_hl':       {'max': 2.0e-9},
        'v_dyn_low_min':     {'max': 0.5},      # full discharge cycle 2
        'v_dyn_share_min':   {'min': 3.5},      # charge-sharing dyn floor
        'v_out_cyc3_min':    {'max': 1.0},      # Out stays low under share
        'v_out_cyc5_final':  {'max': 0.5},      # Out=0 under A1=A2=1
    },
    # ── Wave 1 BASIC cells ─────────────────────────────────────────────────
    'lsdl_nand3_x1': {
        'tpd_eval_hl':       {'max': 2.0e-9},   # < 2 ns (3-series, slower than nand2)
        'v_dyn_low_min':     {'max': 0.5},
        'v_dyn_share_min':   {'min': 3.5},      # nint1/nint2 charge-share floor
        'v_out_cyc3_min':    {'max': 1.0},
        'v_out_cyc5_final':  {'max': 0.5},
    },
    'lsdl_nand4_x1': {
        'tpd_eval_hl':       {'max': 2.0e-9},   # deepest series stack
        'v_dyn_low_min':     {'max': 0.5},
        'v_dyn_share_min':   {'min': 3.5},
        'v_out_cyc3_min':    {'max': 1.0},
        'v_out_cyc5_final':  {'max': 0.5},
    },
    # NOR cells: parallel n-tree, no charge-share stress, use weakest-path check
    'lsdl_nor2_x1': {
        'tpd_eval_hl':       {'max': 2.0e-9},
        'v_dyn_low_min':     {'max': 0.5},
        'v_dyn_single_min':  {'max': 0.5},      # single-input path must also discharge
        'v_out_b_glitch':    {'max': 0.5},      # out_b glitch < 10% VDD
        'v_out_cyc4_hi':     {'min': 4.0},      # Out recovers high
    },
    'lsdl_nor3_x1': {
        'tpd_eval_hl':       {'max': 2.0e-9},
        'v_dyn_low_min':     {'max': 0.5},
        'v_dyn_single_min':  {'max': 0.5},
        'v_out_b_glitch':    {'max': 0.5},
        'v_out_cyc4_hi':     {'min': 4.0},
    },
    'lsdl_nor4_x1': {
        'tpd_eval_hl':       {'max': 2.0e-9},
        'v_dyn_low_min':     {'max': 0.5},
        'v_dyn_single_min':  {'max': 0.5},
        'v_out_b_glitch':    {'max': 0.5},
        'v_out_cyc4_hi':     {'min': 4.0},
    },
    # AOI cells: series+parallel, charge-share on series arm internal nodes
    'lsdl_aoi21_x1': {
        'tpd_eval_hl':          {'max': 2.0e-9},
        'v_dyn_low_min':        {'max': 0.5},
        'v_dyn_share_min':      {'min': 3.5},   # series arm-A nint charge-share
        'v_dyn_armb_min':       {'max': 0.5},   # B arm must discharge
        'v_out_cyc3_settled':   {'min': 4.0},   # Out stable during charge-share
    },
    'lsdl_aoi22_x1': {
        'tpd_eval_hl':          {'max': 2.0e-9},
        'v_dyn_low_min':        {'max': 0.5},
        'v_dyn_share_min':      {'min': 3.5},   # arm-A partial charge-share
        'v_dyn_armb_min':       {'max': 0.5},   # arm-B discharge
        'v_out_cyc3_settled':   {'min': 4.0},
    },
}

MEAS_RE = re.compile(r'^\s*([a-zA-Z_]\w*)\s*=\s*([-+\d.eE]+)', re.MULTILINE)


def gen_tb(template: str, vdd: float, corner: str, temp: int) -> str:
    """Substitute corner, VDD, and temperature into a testbench template."""
    t = re.sub(
        r'(\.lib\s+\S*sm141064\.ngspice\s+)\w+',
        rf'\g<1>{corner}', t := template)
    t = re.sub(
        r'(Vvdd\s+VPWR\s+0\s+)[-+\d.eE]+',
        rf'\g<1>{vdd}', t)
    t = re.sub(
        r'(\.lib\s+\S*sm141064\.ngspice\s+\w+\n)',
        rf'\g<1>.options TEMP={temp}\n', t, count=1)
    # Strip the bulky .print to keep log files small.
    t = re.sub(r'^\.print\s+tran.*$', '* (.print stripped for sweep)',
               t, count=1, flags=re.MULTILINE)
    return t


def parse_meas(log: str) -> dict[str, float]:
    """Pull `name = value` entries from ngspice .meas output."""
    out: dict[str, float] = {}
    for m in MEAS_RE.finditer(log):
        name, val = m.group(1), m.group(2)
        if name in ('Note', 'Reference', 'Index'):
            continue
        try:
            out[name] = float(val)
        except ValueError:
            pass
    return out


def evaluate(cell: str, meas: dict[str, float]):
    criteria = PASS_CRITERIA.get(cell, {})
    passed = True
    rows = []
    for name, bounds in criteria.items():
        v = meas.get(name)
        ok = True
        note = ''
        if v is None:
            ok, note = False, 'MISSING'
        elif 'max' in bounds and v > bounds['max']:
            ok, note = False, f'> {bounds["max"]:.3g}'
        elif 'min' in bounds and v < bounds['min']:
            ok, note = False, f'< {bounds["min"]:.3g}'
        if not ok:
            passed = False
        rows.append((name, v, ok, note))
    return passed, rows


def run_one(cell: str, corner: str, temp: int, vdd: float, tb_text: str):
    tag = f'{cell}_{corner}_t{temp}_v{str(vdd).replace(".", "p")}'
    out_dir = TB_GEN_DIR / cell
    out_dir.mkdir(parents=True, exist_ok=True)
    tb_path = out_dir / f'{tag}.sp'
    tb_path.write_text(tb_text)
    # Path as seen inside the container.
    container_tb = f'/mada/users/czeng14/projects/brainstorm/domino/lsdl_lib/testbench/_gen/{cell}/{tag}.sp'
    log_path = TMP_DIR / f'{tag}.log'
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [str(WRAPPER), f'ngspice -b {container_tb}'],
        capture_output=True, text=True, cwd=PROJECT_ROOT,
    )
    log_path.write_text(proc.stdout + '\n--- STDERR ---\n' + proc.stderr)
    return proc.stdout + proc.stderr


def sweep(cell: str):
    tb_src = LSDL_LIB / 'testbench' / f'tb_{cell}.sp'
    if not tb_src.exists():
        sys.exit(f'no testbench found at {tb_src}')
    template = tb_src.read_text()

    print(f'\n=== PVT sweep: {cell} ===')
    print(f'{"corner":<8} {"T(C)":>5} {"VDD":>5}  result   '
          f'failing measurements')
    print('-' * 70)

    results = []
    all_pass = True
    for corner in CORNERS:
        for temp in TEMPS_C:
            for vdd in VDDS_V:
                tb = gen_tb(template, vdd, corner, temp)
                log = run_one(cell, corner, temp, vdd, tb)
                meas = parse_meas(log)
                passed, rows = evaluate(cell, meas)
                if not passed:
                    all_pass = False
                fail_str = ', '.join(
                    f'{n}={v if v is not None else "?"} ({note})'
                    for n, v, ok, note in rows if not ok)
                print(f'{corner:<8} {temp:>5} {vdd:>5.2f}  '
                      f'{"PASS" if passed else "FAIL"}     {fail_str}')
                results.append({
                    'corner': corner, 'temp_c': temp, 'vdd_v': vdd,
                    'pass': passed, 'meas': meas,
                    'failing': [n for n, _, ok, _ in rows if not ok],
                })

    summary = {
        'cell': cell,
        'overall_pass': all_pass,
        'n_pvt': len(results),
        'n_pass': sum(1 for r in results if r['pass']),
        'results': results,
    }
    # JSON summary is a durable characterization artifact -> repo, not tmp.
    json_out = PVT_DIR / f'{cell}_pvt.json'
    PVT_DIR.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(summary, indent=2))
    print(f'\n{summary["n_pass"]}/{summary["n_pvt"]} PVT points passed')
    print(f'JSON: {json_out}')
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cell', nargs='?', help='cell name (e.g. lsdl_inv_x1)')
    ap.add_argument('--all', action='store_true',
                    help='sweep both Wave 0 cells')
    args = ap.parse_args()

    if args.all:
        for cell in sorted(PASS_CRITERIA):
            sweep(cell)
    elif args.cell:
        sweep(args.cell)
    else:
        ap.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()

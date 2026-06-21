#!/usr/bin/env python3
"""gen_verilog_wrapper.py — generate Verilog blackbox for each LSDL cell.

Reads the cell descriptor YAML and emits a Verilog module with the correct
port order (CLK, A*, OUT, VPWR, VGND). No logic body — synthesis uses this
as a structural blackbox; timing is provided by the Liberty file.

Usage:
  gen_verilog_wrapper.py descriptor/lsdl_nand2_x1.yaml
  gen_verilog_wrapper.py --all
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
import yaml

LSDL_LIB = Path(__file__).resolve().parents[1]
DESC_DIR  = LSDL_LIB / 'descriptor'


def emit_verilog(desc: dict) -> str:
    name     = desc['name']
    function = desc['function']
    pins     = desc['pins']

    # canonical port order: CLK, data inputs (alphabetical), OUT, VPWR, VGND
    clk_pins  = [p['name'] for p in pins if p.get('is_clock')]
    data_pins = sorted(p['name'] for p in pins
                       if p['direction'] == 'input' and not p.get('is_clock'))
    out_pins  = [p['name'] for p in pins if p['direction'] == 'output']
    pwr_pins  = [p['name'] for p in pins if p['direction'] in ('power', 'ground')]

    all_ports = clk_pins + data_pins + out_pins + pwr_pins
    port_list = ', '.join(all_ports)

    lines = []
    lines.append(f'/* {name} — OUT = {function}')
    lines.append(f' * GF180MCU 5V LSDL, X1 drive strength.')
    lines.append(f' * Positive-edge sequential: samples inputs on CLK rising.')
    lines.append(f' * Blackbox: timing from lsdl_fd_sc_9t5v0__tt_5v_25c.lib. */')
    lines.append(f'`timescale 1ns/1ps')
    lines.append(f'module {name} ({port_list});')

    for p in pins:
        pn   = p['name']
        dirn = p['direction']
        if dirn == 'input':
            lines.append(f'  input  {pn};')
        elif dirn == 'output':
            lines.append(f'  output {pn};')
        else:   # power / ground
            lines.append(f'  inout  {pn};')

    lines.append(f'endmodule')
    return '\n'.join(lines) + '\n'


def process_cell(desc_path: Path) -> None:
    with open(desc_path) as f:
        desc = yaml.safe_load(f)
    name = desc['name']

    arts   = desc.get('artifacts', {})
    v_rel  = arts.get('verilog_out', f'../cells/lsdl_basic/{name}.v')
    out    = (desc_path.parent / v_rel).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    text = emit_verilog(desc)
    with open(out, 'w') as f:
        f.write(text)
    print(f'wrote {out}')


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('descriptors', nargs='*', type=Path)
    ap.add_argument('--all', action='store_true')
    args = ap.parse_args()

    paths: list[Path] = list(args.descriptors)
    if args.all:
        paths = sorted(DESC_DIR.glob('*.yaml'))
    if not paths:
        ap.print_usage(); sys.exit(1)

    for p in paths:
        process_cell(p)


if __name__ == '__main__':
    main()

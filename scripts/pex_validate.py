#!/usr/bin/env python3
"""pex_validate.py — PEX timing/glitch gate (W1-A3).

Re-runs a cell's existing testbench on the PARASITIC-EXTRACTED netlist (Magic
caps-only extraction) to confirm eval delay and the paper glitch<10%VDD rule
still hold once layout capacitance is included.

Steps (run by the caller via the container):
  1. pex_extract.tcl produced a FLAT caps netlist <pex.spice> with named top-level
     nodes (A, Clk, Out, VPWR, VGND, out_b, dyn, ...) + ~dozens of C devices.
  2. This script: (a) ties tapless bulk to rails (VSUBS->VGND, nwell node->VPWR);
     (b) rewrites the cell's tb_<cell>.sp into a PEX testbench that includes the
     flat netlist instead of the schematic subckt and probes nodes directly
     (v(Xinst.node) -> v(node), drop the X-instantiation + schematic .include).
  3. Caller runs ngspice on the PEX testbench and checks the .meas pass criteria.

Usage:
  pex_validate.py fix-bulk  <pex.spice>                 # tie bulk to rails in place
  pex_validate.py mk-tb     <tb_in.sp> <pex.spice> <cell> <tb_out.sp>
"""
from __future__ import annotations
import re, sys


def fix_bulk(pex):
    lines = open(pex).read().splitlines()
    # collect the pfet bulk token (4th net field) — the nwell node, e.g. w_0_444#
    nwell = set()
    for ln in lines:
        p = ln.split()
        if p and p[0].lower().startswith('x') and len(p) >= 6 and 'pfet' in ln.lower():
            nwell.add(p[4])
    out = []
    for ln in lines:
        t = ln
        # substrate -> VGND (NMOS body), nwell node(s) -> VPWR (PMOS body)
        t = re.sub(r'\bVSUBS\b', 'VGND', t)
        for nw in nwell:
            if nw not in ('VPWR', 'VGND'):
                t = re.sub(r'(?<!\w)' + re.escape(nw) + r'(?!\w)', 'VPWR', t)
        out.append(t)
    open(pex, 'w').write('\n'.join(out) + '\n')
    print(f"fix-bulk: VSUBS->VGND, nwell {sorted(nwell)}->VPWR")


def subckt_pins(pex, cell):
    txt = open(pex).read()
    m = re.search(rf'^\.subckt\s+{re.escape(cell)}\s+(.*)$', txt, re.I | re.M)
    if not m:
        sys.exit(f"mk-tb: no .subckt {cell} in {pex}")
    return m.group(1).split()


def mk_tb(tb_in, pex, cell, tb_out):
    """Rewrite the schematic testbench to drive the PEX-extracted subckt.

    The PEX subckt exposes the probe nodes (dyn, out_b, ...) as EXTRA pins (via
    mk_ports + port makeall), so we instantiate it with each pin wired to a
    top-level node of the same name. The original meas v(Xinst.out_b) then becomes
    v(out_b) on the now-exposed top node.
    """
    pins = subckt_pins(pex, cell)        # e.g. [A, Clk, Out, VPWR, VGND, dyn, out_b]
    src = open(tb_in).read()
    inst = None
    out = []
    for ln in src.splitlines():
        if re.search(rf'\.include\s+.*{re.escape(cell)}\.spice', ln, re.I):
            out.append(f'.include {pex}'); continue
        m = re.match(rf'\s*(X\w+)\s+.*\b{re.escape(cell)}\b', ln, re.I)
        if m:
            inst = m.group(1)
            conn = ' '.join(pins)        # pin name -> top node of same name
            out.append(f'{inst} {conn} {cell}'); continue   # no inline comment (ngspice)
        out.append(ln)
    txt = '\n'.join(out)
    if inst:
        txt = re.sub(rf'\b{re.escape(inst)}\.', '', txt)   # v(Xinv.out_b) -> v(out_b)
    open(tb_out, 'w').write(txt + '\n')
    print(f"mk-tb: wrote {tb_out} ; PEX subckt pins = {pins}")


if __name__ == '__main__':
    if sys.argv[1] == 'fix-bulk':
        fix_bulk(sys.argv[2])
    elif sys.argv[1] == 'mk-tb':
        mk_tb(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
    else:
        sys.exit(__doc__)

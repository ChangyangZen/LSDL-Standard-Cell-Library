#!/usr/bin/env bash
# pex_gate.sh <cell> <io_pins_csv> <probe_pins_csv> — PEX timing/glitch gate.
# Needs: signoff_<cell> done (so sc_<cell>/mk.gds exists) and testbench
# lsdl_lib/testbench/tb_<cell>.sp. Caps-extracts the cell (named internals via
# probe pins), ties bulk, rewrites the tb onto the extracted netlist, runs ngspice,
# prints the .meas table + a schematic-vs-PEX delta on tpd. Probe pins must be
# metal-labeled nets (NOT metal-less diffusion stack-mid nodes like nint*).
set -uo pipefail
CELL="${1:?usage: pex_gate.sh <cell> <io_csv> <probe_csv>}"
IO="$2"; PROBE="$3"
ROOT=/mada/users/czeng14/projects/brainstorm/domino
D=$ROOT/lsdl_lib/librecell; S=$ROOT/lsdl_lib/scripts; V=$D/venv/bin/python3
PDK=/soe/czeng14/software/pdk/gf180mcuD
TB=$ROOT/lsdl_lib/testbench/tb_$CELL.sp
W=/soe/czeng14/projects/brainstorm-domino-tmp/sc_$CELL
MK=$W/mk.gds
RC(){ "$ROOT/lsdl_lib/scripts/run_in_container.sh" "$@"; }
[ -f "$MK" ] || { echo "FAIL: $MK missing (run signoff_cell.sh $CELL first)"; exit 1; }
[ -f "$TB" ] || { echo "FAIL: testbench $TB missing"; exit 1; }
ALLP="$IO,$PROBE"
echo "== PEX gate $CELL  io=[$IO] probes=[$PROBE] =="
RC "$V $S/mk_ports_gds.py $MK $W/pex_pc.gds $CELL --pins $ALLP" >/dev/null 2>&1
RC "cd $W && PEX_CAPS=1 GDS=$W/pex_pc.gds CELL=$CELL OUT=$W/pex.spice WORK=$W magic -dnull -noconsole -rcfile $PDK/libs.tech/magic/gf180mcuD.magicrc $S/declare_magic_ports.tcl >/dev/null 2>&1; echo done" >/dev/null 2>&1
echo "  extracted: $(grep -i "^\.subckt $CELL" $W/pex.spice | head -1 | cut -c1-90)"
echo "  caps: $(grep -cE '^C' $W/pex.spice)"
RC "$V $S/pex_validate.py fix-bulk $W/pex.spice" >/dev/null 2>&1
RC "$V $S/pex_validate.py mk-tb $TB $W/pex.spice $CELL $W/tb_pex.sp" >/dev/null 2>&1
echo "  --- PEX meas (parasitic caps) ---"
RC "cd $W && ngspice -b $W/tb_pex.sp 2>&1 | grep -iE 'tpd|v_dyn|v_out|glitch|share|failed'" 2>&1 | sed 's/^/    /' | tail -10
echo "  --- schematic ref ---"
RC "cd $W && ngspice -b $TB 2>&1 | grep -iE 'tpd|v_dyn_share|v_out_cyc5|v_out_final'" 2>&1 | sed 's/^/    /' | tail -4

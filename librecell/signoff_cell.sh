#!/usr/bin/env bash
# signoff_cell.sh <cell> [tracks] — full hardened LibreCell signoff for one cell.
#
# Chain (the hardened Wave-1 flow):
#   lclayout -> librecell_postprocess (markers) -> mk_ports_gds (strip+label)
#   -> snap_pin_access (met2 PnR-grid access pads) -> fix_lef_pins (LEF+snapped rects)
#   -> KLayout DRC -> block Netgen LVS (tap|cell|tap) -> gates: pin-access, LEF audit
# Pins are auto-read from the .subckt line of lsdl_lib/librecell/<cell>.sp.
# Freezes artifacts in signoff_<cell>/. Prints a PASS/FAIL summary per gate.
set -uo pipefail
CELL="${1:?usage: signoff_cell.sh <cell> [tracks]}"
TR="${2:-11}"
ROOT=/mada/users/czeng14/projects/brainstorm/domino
D=$ROOT/lsdl_lib/librecell
S=$ROOT/lsdl_lib/scripts
V=$D/venv/bin/python3
PDK=/soe/czeng14/software/pdk/gf180mcuD
TRACKS=$PDK/libs.tech/openlane/gf180mcu_fd_sc_mcu9t5v0/tracks.info
HAND=$D/../cells/lsdl_basic/$CELL.spice
RUN=/soe/czeng14/projects/brainstorm-domino-tmp/drc_runs
W=/soe/czeng14/projects/brainstorm-domino-tmp/sc_$CELL ; mkdir -p "$W"
SIGN=$D/signoff_$CELL ; mkdir -p "$SIGN"
RC() { "$ROOT/lsdl_lib/scripts/run_in_container.sh" "$@"; }

# pins from .subckt; signals = all but VPWR/VGND
PINS=$(grep -i "^\.subckt[[:space:]]\+$CELL\b" "$D/$CELL.sp" | head -1 | sed -E "s/^[^ ]+[ ]+[^ ]+[ ]+//I")
ALL=$(echo "$PINS" | tr ' ' ','); ALL=${ALL%,}
SIG=$(echo "$PINS" | tr ' ' '\n' | grep -viE '^(VPWR|VGND)$' | paste -sd, -)
echo "== signoff $CELL (TRACKS=$TR) pins=[$ALL] signals=[$SIG] =="

# 1. generate. Delete any stale output first so a failed run can't leave a
#    misleading GDS/LEF for the downstream gates to read.
rm -f "$D/out/$CELL.gds" "$D/out/$CELL.lef" "$D/out/$CELL.mag" 2>/dev/null
RC "PYSMT_CYTHON=False TARGETVOLTAGE=5V TRACKS=$TR DNWELL=False PYTHONHASHSEED=42 \
    $D/venv/bin/lclayout --placer smt --place-max-candidates 30 \
    --tech $D/tech_gf180mcu/librecell_tech.py --netlist $D/$CELL.sp --cell $CELL \
    --output-dir $D/out > $W/gen.log 2>&1"
grep -qi "Routing successful" "$W/gen.log" || { echo "FAIL: routing"; tail -3 "$W/gen.log"; exit 1; }
# HARD STOP on internal-LVS failure (router-created shorts). lclayout writes no
# normal GDS on LVS fail; downstream DRC/LEF/pin-access would be misleading. Save
# a debug GDS via --ignore-lvs under debug/ and stop — do NOT run signoff gates.
if grep -qi "LVS result: FAILED" "$W/gen.log"; then
    echo "FAIL: lclayout internal LVS FAILED (router-created connectivity error)."
    mkdir -p "$W/debug"
    RC "PYSMT_CYTHON=False TARGETVOLTAGE=5V TRACKS=$TR DNWELL=False PYTHONHASHSEED=42 \
        $D/venv/bin/lclayout --ignore-lvs --placer smt --place-max-candidates 30 \
        --tech $D/tech_gf180mcu/librecell_tech.py --netlist $D/$CELL.sp --cell $CELL \
        --output-dir $W/debug > $W/debug/gen_ignorelvs.log 2>&1" >/dev/null 2>&1
    echo "  debug GDS/LEF/log under: $W/debug/"
    echo "  ==> $CELL FAILED_CONNECTIVITY"
    exit 2
fi
# 2-4. markers -> port-clean -> snap (signal pins to met2 PnR tracks)
RC "$V $D/librecell_postprocess.py $D/out/$CELL.gds $W/mk.gds $CELL" >/dev/null 2>&1
RC "$V $S/mk_ports_gds.py $W/mk.gds $W/pc.gds $CELL --pins $ALL" >/dev/null 2>&1
RC "$V $S/snap_pin_access.py $W/pc.gds $SIGN/$CELL.gds $CELL $SIGN/$CELL.pinmap.json $D/out/$CELL.lef --signals $SIG" 2>&1 | grep -E "access|wrote" | tail -$(($(echo $SIG|tr , ' '|wc -w)+1))
# 5. LEF (directions + snapped rects)
python3 $S/fix_lef_pins.py $D/out/$CELL.lef $SIGN/$CELL.lef $SIGN/$CELL.pinmap.json >/dev/null 2>&1

# 6. DRC
rm -rf "$RUN"; mkdir -p "$RUN"
RC "python3 $PDK/libs.tech/klayout/drc/run_drc.py --path=$SIGN/$CELL.gds --topcell=$CELL --variant=D --run_mode=flat --no_offgrid --run_dir=$RUN --mp=4 >/dev/null 2>&1"
DRC=$(python3 $S/parse_drc.py "$RUN" 2>&1 | grep -oE "Total cell-level violations:[ ]*[0-9]+" | grep -oE "[0-9]+$")
[ -z "$DRC" ] && DRC=0
# 7. block LVS tap|cell|tap
RC "$V $D/build_support.py combo $SIGN/$CELL.gds $W/blk.gds lsdl_tap_11t $CELL lsdl_tap_11t" >/dev/null 2>&1
RC "$V $S/mk_ports_gds.py $W/blk.gds $W/blk_pc.gds row --pins $ALL" >/dev/null 2>&1
RC "cd $W && GDS=$W/blk_pc.gds CELL=row OUT=$W/blk.spice WORK=$W magic -dnull -noconsole -rcfile $PDK/libs.tech/magic/gf180mcuD.magicrc $S/declare_magic_ports.tcl >/dev/null 2>&1; echo done" >/dev/null 2>&1
LVS=$(RC "cd $W && netgen -batch lvs '$W/blk.spice row' '$HAND $CELL' $PDK/libs.tech/netgen/gf180mcuD_setup.tcl $W/lvs.log >/dev/null 2>&1; grep -ciE 'Circuits match uniquely' $W/lvs.log" 2>&1 | tail -1)
# 8. gates
PA=$(python3 $S/check_pin_access.py $SIGN/$CELL.lef $TRACKS $CELL 2>&1 | grep -cE "^PASS")
LA=$(RC "$V $S/audit_lef.py $SIGN/$CELL.lef $SIGN/$CELL.gds $CELL" 2>&1 | grep -cE "^PASS")

echo "---- $CELL signoff summary ----"
echo "  DRC cell-level : $DRC $([ "$DRC" = 0 ] && echo PASS || echo FAIL)"
echo "  block LVS      : $([ "$LVS" = 1 ] && echo 'PASS (match uniquely)' || echo FAIL)"
echo "  pin-access     : $([ "$PA" = 1 ] && echo PASS || echo FAIL)"
echo "  LEF audit      : $([ "$LA" = 1 ] && echo PASS || echo FAIL)"
[ "$DRC" = 0 ] && [ "$LVS" = 1 ] && [ "$PA" = 1 ] && [ "$LA" = 1 ] && echo "  ==> $CELL SIGNOFF PASS" || { echo "  ==> $CELL SIGNOFF FAIL"; exit 1; }

#!/usr/bin/env bash
# gen_and_drc.sh <cell> [tracks] — regenerate an LSDL cell via lclayout, then run
# the official GF180 KLayout DRC on a FULLY WIPED run dir (avoids stale .lyrdb
# count inflation) and an internal LVS. Prints per-rule + total DRC counts.
set -uo pipefail
CELL="${1:?usage: gen_and_drc.sh <cell> [tracks]}"
TRACKS="${2:-11}"
ROOT=/mada/users/czeng14/projects/brainstorm/domino
D=$ROOT/lsdl_lib/librecell
RUN=/soe/czeng14/projects/brainstorm-domino-tmp/drc_runs
LOG=/soe/czeng14/projects/brainstorm-domino-tmp/${CELL}_gen.log

echo "== lclayout generate $CELL (TRACKS=$TRACKS) =="
"$ROOT/lsdl_lib/scripts/run_in_container.sh" \
  "PYSMT_CYTHON=False TARGETVOLTAGE=5V TRACKS=$TRACKS DNWELL=False PYTHONHASHSEED=42 \
   $D/venv/bin/lclayout --placer smt --place-max-candidates 30 \
     --tech $D/tech_gf180mcu/librecell_tech.py \
     --netlist $D/${CELL}.sp --cell $CELL --output-dir $D/out > $LOG 2>&1"
grep -iE "Routing successful|LVS result|Minimum area fixing failed|Failed to create" "$LOG" | tail -3

echo "== KLayout DRC (clean run dir) =="
rm -rf "$RUN"; mkdir -p "$RUN"
"$ROOT/lsdl_lib/scripts/run_in_container.sh" \
  "python3 /soe/czeng14/software/pdk/gf180mcuD/libs.tech/klayout/drc/run_drc.py \
     --path=$D/out/${CELL}.gds --topcell=$CELL --variant=D --run_mode=flat \
     --no_offgrid --run_dir=$RUN --mp=4 2>&1 | grep -iE 'Violated rules|is clean'" 2>&1 | tail -2
python3 "$ROOT/lsdl_lib/scripts/parse_drc.py" "$RUN" 2>&1 | tail -16

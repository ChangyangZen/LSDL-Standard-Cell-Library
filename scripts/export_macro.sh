#!/usr/bin/env bash
# export_macro.sh — export a hardened macro's 4 views into the wafer.space
# template's ip/<macro>/ tree. domino stays source-of-truth: GDS+LEF are copied
# from the block's pnr/ dir, and the blackbox .v + interface .lib are
# regenerated from the macro spec JSON via gen_macro_views.py.
#
# Usage:
#   export_macro.sh <macro> <pnr_dir> <spec.json> <template_root>
# e.g.
#   export_macro.sh adder_tester \
#     lsdl_lib/blocks/adder/pnr \
#     lsdl_lib/blocks/adder/pnr/macro_adder_tester.json \
#     ~/projects/lsdl_tapeout_wafer.space/gf180mcu-project-template

set -euo pipefail

MACRO="$1"
PNR="$2"
SPEC="$3"
TPL="$4"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"   # lsdl_lib/
SCRIPTS="${ROOT}/scripts"
IPDIR="${TPL}/ip/${MACRO}"

for v in gds lef vh lib; do mkdir -p "${IPDIR}/${v}"; done

# GDS + LEF from the hardened block (must exist).
cp -v "${PNR}/${MACRO}.gds" "${IPDIR}/gds/${MACRO}.gds"
cp -v "${PNR}/${MACRO}.lef" "${IPDIR}/lef/${MACRO}.lef"

# Blackbox .v + interface .lib regenerated from the spec.
python3 "${SCRIPTS}/gen_macro_views.py" "${SPEC}" "${IPDIR}/_tmp"
mv -v "${IPDIR}/_tmp/${MACRO}.v"                    "${IPDIR}/vh/${MACRO}.v"
mv -v "${IPDIR}/_tmp/${MACRO}__tt_025C_5v00.lib"    "${IPDIR}/lib/${MACRO}__tt_025C_5v00.lib"
rmdir "${IPDIR}/_tmp"

echo "exported ${MACRO} -> ${IPDIR}"
ls -R "${IPDIR}"

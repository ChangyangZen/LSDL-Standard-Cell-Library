#!/usr/bin/env bash
# run_in_container.sh — run a command inside the IIC-OSIC-TOOLS container
# with project + PDK mounted at their host paths (no /work or /pdk aliases).
#
# Usage:
#   ./scripts/run_in_container.sh ngspice -b /mada/.../testbench/foo.sp
#   ./scripts/run_in_container.sh magic -d XR -T gf180mcuD foo.tcl
#
# Mount strategy: bind-mount the project tree and PDK using their full
# host paths so the same path works inside and outside the container.

set -euo pipefail

IMAGE="${IMAGE:-hpretl/iic-osic-tools:latest}"
LSDL_LIB_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PDK_ROOT="${PDK_ROOT:-/soe/czeng14/software/pdk}"
CONT_HOME="${CONT_HOME:-/soe/czeng14/projects/brainstorm-domino-tmp/container-home}"
PROJ_TMP="${PROJ_TMP:-/soe/czeng14/projects/brainstorm-domino-tmp}"

if [[ $# -eq 0 ]]; then
  echo "usage: $0 <command...> (runs in IIC-OSIC-TOOLS container)"
  exit 1
fi

# IIC-OSIC-TOOLS tool binaries live under /foss/tools/<name>/[bin/].
FOSS_BIN='/foss/tools/ngspice/bin:/foss/tools/magic/bin:/foss/tools/netgen/bin:/foss/tools/klayout:/foss/tools/yosys/bin:/foss/tools/openroad/bin:/foss/tools/iverilog/bin'

exec docker run --rm -i \
  --user "$(id -u):$(id -g)" \
  --entrypoint /bin/bash \
  -v "${LSDL_LIB_ROOT}":"${LSDL_LIB_ROOT}" \
  -v "${PDK_ROOT}":"${PDK_ROOT}":ro \
  -v "${CONT_HOME}":"${CONT_HOME}" \
  -v "${PROJ_TMP}":"${PROJ_TMP}" \
  -w "${LSDL_LIB_ROOT}" \
  -e HOME="${CONT_HOME}" \
  -e PDK_ROOT="${PDK_ROOT}" \
  -e PDK=gf180mcuD \
  -e PATH="${FOSS_BIN}:/usr/local/bin:/usr/bin:/bin" \
  "${IMAGE}" \
  -c "$*"

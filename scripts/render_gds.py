#!/usr/bin/env python3
"""render_gds.py — render a GDS file to a PNG via KLayout's headless API.

Usage:
    render_gds.py <gds_file> <png_file> [width] [height]

Defaults to 2048x1536. Loads the GF180MCU layer properties (.lyp) so
layer colors match the upstream convention.

Designed to be invoked inside the IIC-OSIC-TOOLS container via the
wrapper script:

    ./lsdl_lib/scripts/run_in_container.sh \\
        'python3 /mada/users/czeng14/projects/brainstorm/domino/lsdl_lib/scripts/render_gds.py \\
            /mada/users/czeng14/projects/brainstorm/domino/lsdl_lib/cells/lsdl_basic/lsdl_inv_x1.gds \\
            /mada/users/czeng14/projects/brainstorm/domino/lsdl_lib/cells/lsdl_basic/lsdl_inv_x1.png'
"""

from __future__ import annotations
import os
import sys

import pya  # KLayout Python API


GF180_LYP = "/soe/czeng14/software/pdk/gf180mcuD/libs.tech/klayout/tech/gf180mcu.lyp"


def render(gds_path: str, png_path: str, width: int, height: int) -> None:
    if not os.path.exists(gds_path):
        sys.exit(f"GDS not found: {gds_path}")

    # Headless LayoutView.
    view = pya.LayoutView()
    view.load_layout(gds_path, 0)

    if os.path.exists(GF180_LYP):
        view.load_layer_props(GF180_LYP)
    else:
        print(f"warning: layer props not found at {GF180_LYP}; using defaults",
              file=sys.stderr)

    # Fit the layout to the view.
    view.max_hier()
    view.zoom_fit()

    view.save_image(png_path, width, height)
    print(f"rendered {gds_path} -> {png_path} ({width}x{height})")


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__.strip())
    gds_path = sys.argv[1]
    png_path = sys.argv[2]
    width = int(sys.argv[3]) if len(sys.argv) > 3 else 1900
    height = int(sys.argv[4]) if len(sys.argv) > 4 else 1400
    render(gds_path, png_path, width, height)


if __name__ == "__main__":
    main()

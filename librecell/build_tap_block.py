#!/usr/bin/env python3
"""build_tap_block.py — build an 11T LSDL tap cell and a tap+inverter+tap block,
to validate the filler-based well-tie convention (Option 1) via block LVS.

Tap cell matches the LSDL 11T row template (from signoff_lsdl_inv_x1):
  boundary 13.44x6.16 won't apply (tap is narrow); height 6.16um;
  nwell y[2.22,6.42] full-width; lvpwell y[0,2.22]; VPWR rail y[5.47,6.4];
  VGND rail y[-0.24,0.69]; all spanning the tap width so wells/rails merge on abut.
It adds: N+ tap (COMP+NPLUS+contacts+M1) tying nwell->VPWR, and P+ tap
(COMP+PPLUS+contacts+M1) tying substrate/pwell->VGND.

Outputs: tap GDS + block GDS (tap | lsdl_inv_x1 | tap), flattened.

Usage: build_tap_block.py <inv_gds> <out_dir>
"""
from __future__ import annotations
import sys
import pya

# Layers
NWELL=(21,0); COMP=(22,0); PPLUS=(31,0); NPLUS=(32,0); MCON=(33,0)
M1=(34,0); DUALG=(55,0); BNDRY=(63,0); FET5V=(112,1); LVPWELL=(204,0)

# Row template (um) from signoff inverter
H=6.16
NWELL_Y=(2.22,6.42); LVPW_Y=(0.0,2.22)
VPWR_Y=(5.47,6.40); VGND_Y=(-0.24,0.69)
TAPW=1.68  # 3 tracks


def main():
    inv_gds, outdir = sys.argv[1], sys.argv[2]
    ly = pya.Layout(); ly.dbu = 0.005
    def nm(v): return int(round(v/ly.dbu))
    def box(cell, layer, x0,y0,x1,y1):
        cell.shapes(ly.layer(pya.LayerInfo(*layer))).insert(
            pya.Box(nm(x0),nm(y0),nm(x1),nm(y1)))

    tap = ly.create_cell("lsdl_tap_11t")
    W=TAPW
    # wells + rails spanning the tap width with 0.12um overhang on each side so
    # abutment always overlaps & merges the neighbor's wells/rails.
    OH=0.12
    box(tap,NWELL,-OH,NWELL_Y[0],W+OH,NWELL_Y[1])
    box(tap,LVPWELL,-OH,LVPW_Y[0],W+OH,LVPW_Y[1])
    box(tap,M1,-OH,VPWR_Y[0],W+OH,VPWR_Y[1])      # VPWR rail
    box(tap,M1,-OH,VGND_Y[0],W+OH,VGND_Y[1])      # VGND rail
    box(tap,BNDRY,0,0,W,H)
    box(tap,DUALG,-0.1,-0.28,W+0.1,H+0.28)
    box(tap,FET5V,0,0,W,H)
    # N+ tap in nwell -> VPWR
    box(tap,COMP, 0.50,4.70,1.18,5.50)
    box(tap,NPLUS,0.34,4.54,1.34,5.66)       # >=0.16 enclose COMP
    box(tap,MCON, 0.73,4.96,0.95,5.18)       # single 0.22 contact (avoids CO.2a)
    box(tap,M1,   0.50,4.90,1.18,6.40)       # M1 over contact up into VPWR rail
    # P+ tap in substrate -> VGND
    box(tap,COMP, 0.50,0.66,1.18,1.46)
    box(tap,PPLUS,0.34,0.50,1.34,1.62)
    box(tap,MCON, 0.73,0.98,0.95,1.20)       # single 0.22 contact
    box(tap,M1,   0.50,-0.24,1.18,1.20)      # M1 over contact down into VGND rail

    # Block: tap | inv | tap
    blk = ly.create_cell("lsdl_inv_block")
    inv_ly = pya.Layout(); inv_ly.read(inv_gds)
    inv_top = next(c for c in inv_ly.each_cell() if c.name=="lsdl_inv_x1")
    inv_in_blk = ly.create_cell("lsdl_inv_x1")
    ly.cell(inv_in_blk.cell_index()).copy_tree(inv_top)  # import inverter
    # Abut at the BOUNDARY (63/0) pitch, not bbox (which includes dualgate overhang).
    bidx = inv_ly.find_layer(pya.LayerInfo(*BNDRY))
    invW = pya.Region(inv_top.begin_shapes_rec(bidx)).bbox().right*inv_ly.dbu  # 13.44

    blk.insert(pya.CellInstArray(tap.cell_index(), pya.Trans(pya.Trans.R0, 0, 0)))
    blk.insert(pya.CellInstArray(inv_in_blk.cell_index(), pya.Trans(pya.Trans.R0, nm(TAPW), 0)))
    blk.insert(pya.CellInstArray(tap.cell_index(), pya.Trans(pya.Trans.R0, nm(TAPW+invW), 0)))
    blk.flatten(-1, True)

    ly.write(f"{outdir}/lsdl_tap_11t.gds")
    # write block-only layout
    bly = pya.Layout(); bly.dbu=0.005
    bt = bly.create_cell("lsdl_inv_block")
    bt.copy_tree(blk)
    bly.write(f"{outdir}/lsdl_inv_block.gds")
    print(f"tap width {TAPW}um, inverter width {invW:.2f}um, block width {TAPW*2+invW:.2f}um")
    print(f"wrote {outdir}/lsdl_tap_11t.gds and lsdl_inv_block.gds")


if __name__=="__main__":
    main()

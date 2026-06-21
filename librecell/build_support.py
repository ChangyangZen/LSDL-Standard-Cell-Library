#!/usr/bin/env python3
"""build_support.py — 11T LSDL physical-support cells + seam-combo generator.

Row contract (shared constants, taken from the signed-off lsdl_inv_x1; DO NOT
recompute per cell): height 6.16um; NWELL y[2.22,6.42]; LVPWELL y[0,2.22];
VPWR rail y[5.47,6.40]; VGND rail y[-0.24,0.69]; DUALGATE/FET5VDEF span the cell
boundary in X and the full row in Y (abutment-safe). Wells/rails span [0,W] with
NO overhang and cells tile at the exact boundary pitch, so abutted layers form
continuous row bands.

Cells: lsdl_tap_11t (W=1.68, N+ nwell->VPWR, P+ sub->VGND), lsdl_endcap_11t
(W=1.12), lsdl_fill_11t_{1,2,4} (W=0.56/1.12/2.24). lsdl_inv_x1 stays tapless.

Usage:
  build_support.py cells <out_dir>                 # write each support cell GDS
  build_support.py combo <inv_gds> <out_gds> <names...>   # abut+flatten a row
"""
from __future__ import annotations
import sys
import pya

NWELL=(21,0); COMP=(22,0); PPLUS=(31,0); NPLUS=(32,0); MCON=(33,0)
M1=(34,0); DUALG=(55,0); BNDRY=(63,0); FET5V=(112,1); LVPWELL=(204,0)

H=6.16
NWELL_Y=(2.22,6.42); LVPW_Y=(0.0,2.22)
VPWR_Y=(5.47,6.40); VGND_Y=(-0.24,0.69)
DG_Y=(-0.28,6.44)            # DUALGATE/row vertical extent (matches inverter)
WIDTHS={'lsdl_tap_11t':1.68,'lsdl_endcap_11t':1.12,
        'lsdl_fill_11t_1':0.56,'lsdl_fill_11t_2':1.12,'lsdl_fill_11t_4':2.24,
        'lsdl_antenna_11t':1.68}
# I-pin diffusion area (um^2) of the antenna diode -> LEF ANTENNADIFFAREA.
ANTENNA_DIFF_AREA = (1.18-0.50)*(1.46-0.66)   # 0.68 x 0.80 = 0.544

def _nm(ly,v): return int(round(v/ly.dbu))

def _box(ly,cell,layer,x0,y0,x1,y1):
    cell.shapes(ly.layer(pya.LayerInfo(*layer))).insert(
        pya.Box(_nm(ly,x0),_nm(ly,y0),_nm(ly,x1),_nm(ly,y1)))

def build_cell(ly,name):
    W=WIDTHS[name]
    c=ly.create_cell(name)
    # row bands (span [0,W] exactly; abut at boundary -> continuous)
    _box(ly,c,NWELL,0,NWELL_Y[0],W,NWELL_Y[1])
    _box(ly,c,LVPWELL,0,LVPW_Y[0],W,LVPW_Y[1])
    _box(ly,c,M1,0,VPWR_Y[0],W,VPWR_Y[1])     # VPWR rail
    _box(ly,c,M1,0,VGND_Y[0],W,VGND_Y[1])     # VGND rail
    _box(ly,c,BNDRY,0,0,W,H)
    _box(ly,c,DUALG,0,DG_Y[0],W,DG_Y[1])      # boundary-width dualgate (row band)
    _box(ly,c,FET5V,0,0,W,H)
    if name=='lsdl_tap_11t':
        # N+ tap in nwell -> VPWR
        _box(ly,c,COMP, 0.50,4.70,1.18,5.50)
        _box(ly,c,NPLUS,0.34,4.54,1.34,5.66)
        _box(ly,c,MCON, 0.73,4.96,0.95,5.18)
        _box(ly,c,M1,   0.50,4.90,1.18,6.40)
        # P+ tap in substrate/pwell -> VGND
        _box(ly,c,COMP, 0.50,0.66,1.18,1.46)
        _box(ly,c,PPLUS,0.34,0.50,1.34,1.62)
        _box(ly,c,MCON, 0.73,0.98,0.95,1.20)
        _box(ly,c,M1,   0.50,-0.24,1.18,1.20)
    elif name=='lsdl_antenna_11t':
        # Antenna diode (CORE ANTENNACELL): N+ diode in the p-well tied to the
        # I pin (cathode), anode = p-well -> VGND via row taps. repair_antennas
        # inserts these on long gate nets so etch charge bleeds through the diode
        # instead of stressing the gate oxide. Geometry mirrors the proven tap
        # cell: upper N+ nwell tap -> VPWR (well bias); lower N+ swapped from the
        # tap's P+ (same DRC-clean boxes), M1 reduced to an isolated I pin.
        # Upper N+ tap in nwell -> VPWR (biases local nwell; copied from tap)
        _box(ly,c,COMP, 0.50,4.70,1.18,5.50)
        _box(ly,c,NPLUS,0.34,4.54,1.34,5.66)
        _box(ly,c,MCON, 0.73,4.96,0.95,5.18)
        _box(ly,c,M1,   0.50,4.90,1.18,6.40)
        # Lower N+ diode in p-well -> I pin (NPLUS where the tap had PPLUS)
        _box(ly,c,COMP, 0.50,0.66,1.18,1.46)
        _box(ly,c,NPLUS,0.34,0.50,1.34,1.62)
        _box(ly,c,MCON, 0.73,0.98,0.95,1.20)
        _box(ly,c,M1,   0.50,0.94,1.18,1.46)      # I pin (clears VGND rail top 0.69)
    return c

def cmd_cells(outdir):
    for name in WIDTHS:
        ly=pya.Layout(); ly.dbu=0.005
        build_cell(ly,name)
        ly.write(f"{outdir}/{name}.gds")
        print('wrote',name,'W=',WIDTHS[name])

def cmd_combo(logic_gds,out_gds,names):
    ly=pya.Layout(); ly.dbu=0.005
    # import the logic cell (any name) from logic_gds; its boundary sets the width
    lg=pya.Layout(); lg.read(logic_gds)
    lg_top=lg.top_cell()
    lname=lg_top.name
    bidx=lg.find_layer(pya.LayerInfo(*BNDRY))
    lW=pya.Region(lg_top.begin_shapes_rec(bidx)).bbox().right*lg.dbu
    cells={}
    lc=ly.create_cell(lname); lc.copy_tree(lg_top); cells[lname]=(lc,lW)
    for n in set(names)-{lname}:
        cells[n]=(build_cell(ly,n),WIDTHS[n])
    blk=ly.create_cell('row')
    x=0.0
    for n in names:
        c,w=cells[n]
        blk.insert(pya.CellInstArray(c.cell_index(),pya.Trans(pya.Trans.R0,_nm(ly,x),0)))
        x+=w
    blk.flatten(-1,True)
    out=pya.Layout(); out.dbu=0.005
    ot=out.create_cell('row'); ot.copy_tree(blk); out.write(out_gds)
    print('combo',' | '.join(names),'-> width',round(x,2),'um')

if __name__=='__main__':
    if sys.argv[1]=='cells': cmd_cells(sys.argv[2])
    elif sys.argv[1]=='combo': cmd_combo(sys.argv[2],sys.argv[3],sys.argv[4:])

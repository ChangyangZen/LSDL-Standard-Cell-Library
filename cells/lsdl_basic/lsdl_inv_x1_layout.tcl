# lsdl_inv_x1_layout.tcl — REBUILD with top-cell diffusion painting
# (per advice: subcell approach hit a structural limit; this version
# draws diffs, poly, contacts, and M1 as primitive rectangles at the
# top cell level so adjacent same-net FETs share their diff regions
# physically rather than needing M1 bridges through dense per-FET
# gate-contact patches).
#
# Architecture: each row is ONE active strip (mvpdiff or mvndiff) with
# multiple poly stripes crossing it. The space between two adjacent
# poly stripes IS a shared S/D region (one contact, one M1 cap, one
# net). No subcells.

cd /mada/users/czeng14/projects/brainstorm/domino/lsdl_lib/cells/lsdl_basic
units internal

set IU_PER_UM 200
proc um2iu {um} {
    global IU_PER_UM
    return [expr {int($um * $IU_PER_UM)}]
}

proc paint_box {layer x0 y0 x1 y1} {
    box values [um2iu $x0] [um2iu $y0] [um2iu $x1] [um2iu $y1]
    paint $layer
}

# Discard any stale subcells from prior approach. cellname delete on
# the failed-approach subcells; if they're not loaded, this is a no-op.
foreach old {pfet_W1p0_L0p5_nf1 pfet_W0p5_L0p5_nf1 pfet_W0p75_L0p5_nf2
             pfet_W0p75_L0p5_nf4 nfet_W0p4_L0p6_nf1 nfet_W0p5_L0p6_nf1
             nfet_W0p4_L0p6_nf2 nfet_W0p45_L0p6_nf2} {
    catch {cellname delete $old}
}

# Build top cell.
load lsdl_inv_x1 -force

# ==============================================================
# Cell-level geometry parameters.
# Derived in README.md "Geometry / Sizing Derivation".
# ==============================================================
set CELL_Y0    0.0
set CELL_Y1    5.04
set RAIL_H     0.23     ;# M1.1 minimum

set Y_VGND_TOP $RAIL_H              ;# 0.23
set Y_VPWR_BOT [expr {$CELL_Y1 - $RAIL_H}]  ;# 4.81

# Channel centerlines
set Y_NMOS_CH  1.20
set Y_PMOS_CH  3.60

# Well boundary
set Y_WELL     2.30  ;# n-well bottom; must be ≥0.6 above NMOS top (1.65)

# nwell/pwell overhang past cell boundary for abutment
set NWELL_TOP_OH 5.50
set PWELL_BOT_OH -0.46
set WELL_X_OH    0.55

# Poly stripe vertical extent: must extend beyond active by >=0.18 µm
# (DF.6_MV requires diff to extend 0.4 beyond poly; that's the same
# constraint but inverted view: poly extends beyond gate by 0.18+ for
# polycontact landing).
# Poly stripe Y: from below active to above active, used to gate the
# FET. Active (mvpdiff/mvndiff) is centered on cy_p / cy_n with extent
# ±W/2. Poly extends beyond active by `poly_ext` on top and bottom.
set POLY_EXT 0.40
set POLY_W   0.50    ;# PMOS L=0.5; for NMOS use L=0.6 separately

# Diffusion extent in Y: ±W/2 around channel centerline (W per FET).
# Contact placement: contacts go in the diff middle, between two poly
# stripes. Contact M1 cap = contact size + 0.005 µm margin per side
# (Magic auto-grow).

# ==============================================================
# PMOS ROW (top, in n-well)
# ==============================================================
# Order chosen for max diff sharing:
#   [dyn|XPRE|VPWR|XPDRVP_g1|out_b|XPDRVP_g2|VPWR|XPDRVP_g3|out_b|
#    XPDRVP_g4|VPWR|XODRVP_g1|Out|XODRVP_g2|VPWR|XFBP|cut_fb_src|
#    XCUTFB|out_b]
#
# Width of each FET's segment in the row is (poly_W + contact_W +
# spacing margins). With poly_W=0.5 and contact_W=0.36, pitch
# between adjacent poly stripes is ~ poly_W + diff_extension*2 + cap_W
# Approximate: poly_pitch_min = 1.02 (matches Magic _draw output we
# observed earlier).
# DF.6_MV requires diff to extend 0.4 µm past poly on each side.
# Inter-poly gap must be ≥ 2×0.4 = 0.8 µm. With poly width 0.5,
# pitch must be ≥ 0.5 + 0.8 = 1.30 µm.
set POLY_PITCH_P 1.30

# Active strip extent in X: starts at first diff edge, ends at last.
# 9 PMOS poly stripes (XPRE, 4×XPDRVP, 2×XODRVP, XFBP, XCUTFB).
# Approximate: poly_pitch * (9 - 1) + 2*(diff edge extension)
# = 1.02 * 8 + 2 * 0.31 = 8.16 + 0.62 = 8.78 µm wide.

# Poly stripe X positions (centers of each gate stripe).
# PMOS device boundaries (each "device" can be multi-finger merged):
#   XPRE (1 stripe), XPDRVP (4 stripes), XODRVP (2 stripes),
#   XFBP (1 stripe), XCUTFB (1 stripe) = 9 stripes total.
# Boundary type between adjacent stripes determines which S/D net.
# X positions (left-to-right, starting at x=1.0):
set PMOS_X_BASE 1.0
set PXS [list]
for {set i 0} {$i < 9} {incr i} {
    lappend PXS [expr {$PMOS_X_BASE + $i * $POLY_PITCH_P}]
}
# PXS = {1.0, 2.02, 3.04, 4.06, 5.08, 6.10, 7.12, 8.14, 9.16}

# Define PMOS device widths (per finger) and the role of each stripe.
# Order: XPRE, XPDRVP×4, XODRVP×2, XFBP, XCUTFB.
set PMOS_W_FINGER 0.75   ;# Default for XPDRVP/XODRVP
set PMOS_W_XPRE   1.0
set PMOS_W_XFBP   0.5
set PMOS_W_XCUTFB 0.5
# Use max width for the active strip's Y extent so all FETs share the
# same diff region. (Smaller-W FETs will have extra diff overhang —
# allowed, doesn't violate anything.)
set PMOS_W_MAX [expr {max($PMOS_W_FINGER, $PMOS_W_XPRE, $PMOS_W_XFBP, $PMOS_W_XCUTFB)}]
;# = 1.0 µm

# PMOS active strip extent.
set PMOS_DIFF_Y0 [expr {$Y_PMOS_CH - $PMOS_W_MAX / 2.0}]   ;# 3.10
set PMOS_DIFF_Y1 [expr {$Y_PMOS_CH + $PMOS_W_MAX / 2.0}]   ;# 4.10
# Active strip extends 0.31 µm past leftmost/rightmost poly (DF.6).
# DF.6_MV: diffusion must extend ≥0.4 µm past poly (S/D overhang).
set PMOS_DIFF_X0 [expr {[lindex $PXS 0]  - $POLY_W / 2.0 - 0.40}]
set PMOS_DIFF_X1 [expr {[lindex $PXS end] + $POLY_W / 2.0 + 0.40}]
puts "PMOS active strip: x=[expr $PMOS_DIFF_X0]..[expr $PMOS_DIFF_X1] y=$PMOS_DIFF_Y0..$PMOS_DIFF_Y1"

paint_box mvpdiff $PMOS_DIFF_X0 $PMOS_DIFF_Y0 $PMOS_DIFF_X1 $PMOS_DIFF_Y1

# Paint poly stripes (one per FET gate). Stripe extends:
#   x: gate_center ± POLY_W/2
#   y: PMOS_DIFF_Y0 - POLY_EXT  ..  PMOS_DIFF_Y1 + POLY_EXT
foreach gx $PXS {
    paint_box polysilicon \
        [expr {$gx - $POLY_W/2.0}] [expr {$PMOS_DIFF_Y0 - $POLY_EXT}] \
        [expr {$gx + $POLY_W/2.0}] [expr {$PMOS_DIFF_Y1 + $POLY_EXT}]
}

# NOTE: Magic auto-derives the mvpmos FET region from mvpdiff +
# polysilicon overlap. Do NOT explicitly paint mvpmos — it would
# convert the entire diff strip into FET region, losing the diff
# S/D regions between poly stripes.

# ==============================================================
# NMOS ROW (bottom, in p-well)
# ==============================================================
# Order: [dyn|XNTREE|foot_top|XFOOT|VGND|XHDR|hdr_src|XPDRVN|out_b|
#         XFBN|VGND|XODRVN|Out]
# 6 NMOS poly stripes.
set NMOS_X_BASE 1.0
set POLY_PITCH_N 1.40  ;# NMOS L=0.6: 0.6 + 2*0.4 = 1.4
set NXS [list]
for {set i 0} {$i < 6} {incr i} {
    lappend NXS [expr {$NMOS_X_BASE + $i * $POLY_PITCH_N}]
}
# NXS = {1.0, 2.12, 3.24, 4.36, 5.48, 6.60}

set NMOS_W_MAX 0.9    ;# XODRVN is widest at W=0.9 (single device)
set NMOS_W_DEFAULT 0.8

set NMOS_DIFF_Y0 [expr {$Y_NMOS_CH - $NMOS_W_MAX / 2.0}]   ;# 0.75
set NMOS_DIFF_Y1 [expr {$Y_NMOS_CH + $NMOS_W_MAX / 2.0}]   ;# 1.65
set NMOS_POLY_W 0.61   ;# 0.6 + 0.01 margin to avoid floating-point edge case
set NMOS_DIFF_X0 [expr {[lindex $NXS 0]  - $NMOS_POLY_W / 2.0 - 0.40}]
set NMOS_DIFF_X1 [expr {[lindex $NXS end] + $NMOS_POLY_W / 2.0 + 0.40}]
puts "NMOS active strip: x=[expr $NMOS_DIFF_X0]..[expr $NMOS_DIFF_X1] y=$NMOS_DIFF_Y0..$NMOS_DIFF_Y1"

paint_box mvndiff $NMOS_DIFF_X0 $NMOS_DIFF_Y0 $NMOS_DIFF_X1 $NMOS_DIFF_Y1

foreach gx $NXS {
    paint_box polysilicon \
        [expr {$gx - $NMOS_POLY_W/2.0}] [expr {$NMOS_DIFF_Y0 - $POLY_EXT}] \
        [expr {$gx + $NMOS_POLY_W/2.0}] [expr {$NMOS_DIFF_Y1 + $POLY_EXT}]
}

# NOTE: same as PMOS — don't paint mvnmos; Magic derives it from
# mvndiff + polysilicon overlap.

# ==============================================================
# Wells
# ==============================================================
puts "==== Wells ..."
set CELL_X0 0.0
# PMOS strip spans x = 1.0 - 0.25 - 0.4 .. 1.0 + 8*1.30 + 0.25 + 0.4 = 0.35 .. 12.05
# NMOS strip spans x = 1.0 - 0.30 - 0.4 .. 1.0 + 5*1.40 + 0.30 + 0.4 = 0.30 .. 8.70
# Cell width must cover the wider row + margin.
set CELL_X1 12.5
paint_box nwell [expr {$CELL_X0 - $WELL_X_OH}] $Y_WELL \
                [expr {$CELL_X1 + $WELL_X_OH}] $NWELL_TOP_OH
paint_box pwell [expr {$CELL_X0 - $WELL_X_OH}] $PWELL_BOT_OH \
                [expr {$CELL_X1 + $WELL_X_OH}] $Y_WELL

# ==============================================================
# Power rails
# ==============================================================
puts "==== Power rails ..."
paint_box metal1 $CELL_X0 $Y_VPWR_BOT $CELL_X1 $CELL_Y1
paint_box metal1 $CELL_X0 $CELL_Y0    $CELL_X1 $Y_VGND_TOP

# ==============================================================
# (R5-R8 routing — not yet implemented)
# ==============================================================
puts "==== Routing R5-R8 deferred ..."

# Save and report.
save lsdl_inv_x1
gds write lsdl_inv_x1.gds
puts "==== GDS written"

drc check
drc catchup
puts "==== Magic DRC count: [drc list count total]"

quit -noprompt

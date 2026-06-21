# declare_magic_ports.tcl — L7: promote the cell's existing I/O labels to Magic
# ports so ext2spice emits a proper `.subckt <cell> <pins>` list and Netgen LVS
# reports clean port matching (not "match uniquely with port errors").
#
# The labels already exist in the GDS (written by lclayout). We do NOT add new
# labels (that duplicates them -> "specify a unique port"). `port makeall`
# converts every existing label into a port; a second pass sets class/use by name.
#
# Env: GDS (input gds), CELL (top cell), OUT (extracted .spice), WORK (cwd).

set GDS  $env(GDS)
set CELL $env(CELL)
set OUT  $env(OUT)
set WORK $env(WORK)

cd $WORK
drc off
crashbackups stop
gds read $GDS
load $CELL
select top cell

# The input GDS here has been pre-cleaned (mk_ports_gds.py) to carry EXACTLY the
# 5 I/O labels on metal1 and nothing else, so makeall yields exactly 5 ports.
if {[catch {port makeall} e]} { puts "port makeall: $e" }

# Set class/use per pin (by name). Harmless if a name is absent.
foreach {name cls use} {
    A    input  signal
    Clk  input  signal
    CLK  input  signal
    Out  output signal
    OUT  output signal
    VPWR inout  power
    VGND inout  ground
} {
    catch {port $name class $cls}
    catch {port $name use $use}
}

save $CELL
extract all
ext2spice lvs
# PEX_CAPS=1 -> include parasitic caps (cthresh 0); no resistance => named nets
# survive as subckt internal nodes/pins. Default (unset) = clean LVS netlist.
if {[info exists env(PEX_CAPS)] && $env(PEX_CAPS) == 1} {
    ext2spice cthresh 0
}
ext2spice -o $OUT
puts "PORTS_DONE -> $OUT"
quit -noprompt

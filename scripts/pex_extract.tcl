# pex_extract.tcl — caps-only parasitic extraction, FLAT (named top-level nodes).
# No resistance extraction -> nets are NOT split, so internal labels (out_b, dyn,
# foot_top, ...) survive as node names that the testbench can probe. `subcircuit
# top off` emits the cell flat (global node names) instead of wrapping a pin-less
# .subckt. Env: GDS, CELL, OUT, WORK.
set GDS $env(GDS); set CELL $env(CELL); set OUT $env(OUT); set WORK $env(WORK)
cd $WORK
drc off
crashbackups stop
gds read $GDS
load $CELL
select top cell
extract all
ext2spice lvs
ext2spice cthresh 0
ext2spice subcircuit top off
ext2spice -o $OUT
puts "PEX_DONE -> $OUT"
quit -noprompt

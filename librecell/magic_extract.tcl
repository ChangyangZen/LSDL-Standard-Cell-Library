# magic_extract.tcl — read a GDS with the GF180 Magic tech and extract LVS SPICE.
# Usage (inside container):
#   magic -dnull -noconsole -rcfile <gf180mcuD.magicrc> -T gf180mcuD magic_extract.tcl
# Reads $GDS, extracts $CELL, writes $OUT (ext2spice lvs).

set GDS  $env(GDS)
set CELL $env(CELL)
set OUT  $env(OUT)
set WORK $env(WORK)

cd $WORK
crashbackups stop
drc off
gds read $GDS
load $CELL
select top cell

extract no all
extract do local
extract unique
extract all

ext2spice lvs
ext2spice format ngspice
ext2spice -o $OUT
puts "EXTRACT_DONE -> $OUT"
quit -noprompt

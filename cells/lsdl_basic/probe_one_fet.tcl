# probe_one_fet.tcl — instantiate one nfet_06v0 by calling the PDK's
# _draw proc directly, bypassing magic::gencell (which needs a Tk focus).

cd /mada/users/czeng14/projects/brainstorm/domino/lsdl_lib/cells/lsdl_basic

cellname create probe_one_fet
load probe_one_fet -force

# Set units to microns and place box at origin.
snap user
box values 0 0 0 0

# Apply defaults, then override w/l.
set parameters [gf180mcu::nfet_06v0_defaults]
set parameters [dict merge $parameters [dict create w 0.8 l 0.6]]
puts "==== parameters: $parameters"

# Paint the device directly.
if {[catch {gf180mcu::nfet_06v0_draw $parameters} err]} {
    puts stderr "draw error: $err"
} else {
    puts "==== draw succeeded"
}

select top cell
puts "==== Bounding box after draw:"
box
expand
save probe_one_fet

drc check
drc catchup
puts "==== DRC errors: [drc list count total]"
puts "==== DRC list:"
foreach reason [drc listall why] { puts "  - $reason" }

extract no all
extract all
puts "==== Files in CWD:"
foreach f [lsort [glob -nocomplain *.mag *.ext]] { puts "  $f" }

quit -noprompt

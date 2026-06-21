# probe_nf2.tcl — see what nf=2 produces in the FET subcell

cd /mada/users/czeng14/projects/brainstorm/domino/lsdl_lib/cells/lsdl_basic
units internal

load nfet_W0p4_L0p6_nf2 -force
box values 0 0 0 0
set parameters [gf180mcu::nfet_06v0_defaults]
set parameters [dict merge $parameters [dict create \
    w 0.4 l 0.6 nf 2 guard 0 glc 0 grc 0]]
if {[catch {gf180mcu::nfet_06v0_draw $parameters} err]} {
    puts stderr "draw err: $err"
}
save nfet_W0p4_L0p6_nf2

load nfet_W0p45_L0p6_nf2 -force
box values 0 0 0 0
set parameters [gf180mcu::nfet_06v0_defaults]
set parameters [dict merge $parameters [dict create \
    w 0.45 l 0.6 nf 2 guard 0 glc 0 grc 0]]
gf180mcu::nfet_06v0_draw $parameters
save nfet_W0p45_L0p6_nf2

quit -noprompt

cellname create test_fet
pushstack test_fet
box values 0 0 0 0
set params [gf180mcu::nfet_06v0_defaults]
set params [dict merge $params [dict create w 0.8 l 0.6 guard 0 glc 0 grc 0]]
gf180mcu::nfet_06v0_draw $params
puts "==== After draw, before findbox:"
puts [box]
puts "==== findbox of all paint:"
findbox 1 ;# 1 = include subcells
puts [box]
popstack
puts "==== ----- another approach -----"
load test_fet -force
findbox 1
puts "loaded test_fet, findbox gave: [box]"
quit -noprompt

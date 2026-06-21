cellname create test_top
load test_top -force

# Try setpoint to position before _draw.
units internal

# 1 um = 200 internal units
box values 200 800 200 800  ;# 1 um, 4 um position
set params [gf180mcu::pfet_06v0_defaults]
set params [dict merge $params [dict create w 1.0 l 0.5 guard 0 glc 0 grc 0]]
puts "==== First FET at box (1,4)"
gf180mcu::pfet_06v0_draw $params

box values 540 800 540 800  ;# 2.7 um, 4 um
puts "==== Second FET at box (2.7,4)"
gf180mcu::pfet_06v0_draw $params

box values 880 800 880 800
puts "==== Third FET at box (4.4,4)"
gf180mcu::pfet_06v0_draw $params

save test_top
gds write test_top.gds
quit -noprompt

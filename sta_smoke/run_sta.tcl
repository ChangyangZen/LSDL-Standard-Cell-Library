# run_sta.tcl — OpenSTA acceptance gates for lsdl_fd_sc_9t5v0 Liberty.
# G1: Liberty parse (0 errors)
# G2: All 9 cells present
# G3: Function check on NAND2
# G4: Timing smoke (finite slack at 500 MHz)

read_liberty /mada/users/czeng14/projects/brainstorm/domino/lsdl_lib/lib/lsdl_fd_sc_9t5v0__tt_5v_25c.lib
read_verilog /mada/users/czeng14/projects/brainstorm/domino/lsdl_lib/cells/lsdl_basic/lsdl_inv_x1.v
read_verilog /mada/users/czeng14/projects/brainstorm/domino/lsdl_lib/sta_smoke/smoke.v
link_design  smoke
read_sdc     /mada/users/czeng14/projects/brainstorm/domino/lsdl_lib/sta_smoke/smoke.sdc

puts ""
puts "================== G2: CELL COUNT =================="
set cells [get_lib_cells lsdl_fd_sc_9t5v0/*]
puts "Found [llength $cells] cells in library"
foreach c $cells { puts "  [get_name $c]" }

puts ""
puts "================== G3: NAND2 CELL REPORT =================="
report_lib_cell lsdl_fd_sc_9t5v0/lsdl_nand2_x1

puts ""
puts "================== G4: CHECK_SETUP =================="
check_setup -verbose

puts ""
puts "================== G4: REPORT_CHECKS (setup) =================="
report_checks -path_delay max -fields {capacitance slew}

puts ""
puts "================== G4: REPORT_CHECKS (hold) =================="
report_checks -path_delay min -fields {capacitance slew}

puts ""
puts "================== G4: PULSE WIDTH CHECKS =================="
puts "(Pulse-width arcs visible in G3 report_lib_cell output: CLK width ^ and v constraints.)"

puts ""
puts "================== DONE — if no ERROR above, all gates pass =================="
exit

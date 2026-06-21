load /mada/users/czeng14/projects/brainstorm/domino/lsdl_lib/cells/lsdl_basic/lsdl_inv_x1
drc check
drc catchup
puts "==== count: [drc list count total]"
puts "==== unique rule strings:"
set seen {}
foreach r [drc listall why] {
    if {[lsearch $seen $r] < 0} {
        lappend seen $r
        puts "  RULE: $r"
    }
}
quit -noprompt

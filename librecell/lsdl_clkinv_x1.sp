* lsdl_clkinv_x1 — static CMOS clock inverter for CTS inside the LSDL macros.
* The clock is NOT LSDL logic: a plain inverter on the 11T site so it abuts the
* LSDL rows. Used by run_pnr.tcl clock_tree_synthesis to buffer c1/c2 (~8500-sink
* flat clock -> balanced tree: fixes slew/skew + collapses antenna).
* Device line: M<name> D G S B model w l.  Model n* => NMOS, else PMOS.
* l matches tech (NMOS 0.6u / PMOS 0.5u). Upsized 2:1 for clock drive.
.subckt lsdl_clkinv_x1 A Y VPWR VGND
MP Y A VPWR VPWR pmos w=2.0u l=0.5u
MN Y A VGND VGND nmos w=1.0u l=0.6u
.ends lsdl_clkinv_x1

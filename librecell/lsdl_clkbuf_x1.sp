* lsdl_clkbuf_x1 — static CMOS NON-INVERTING clock BUFFER (2 inverter stages) for
* CTS inside the LSDL macros. OpenROAD clock_tree_synthesis needs a buffer
* (function "A"), not an inverter, for -buf_list / -root_buf. 11T site.
* M<name> D G S B model w l ; model n* => NMOS else PMOS ; l matches tech.
.subckt lsdl_clkbuf_x1 A Z VPWR VGND
* stage 1: A -> n1
MP1 n1 A VPWR VPWR pmos w=1.0u l=0.5u
MN1 n1 A VGND VGND nmos w=0.5u l=0.6u
* stage 2: n1 -> Z (upsized for drive)
MP2 Z n1 VPWR VPWR pmos w=2.0u l=0.5u
MN2 Z n1 VGND VGND nmos w=1.0u l=0.6u
.ends lsdl_clkbuf_x1

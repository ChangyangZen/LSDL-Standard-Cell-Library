* tb_lsdl_eval_decomp.sp — decompose LSDL NAND2 eval: Clk -> dyn -> out_b -> Out.
* dyn = !(A1.A2) is the SAME node-polarity as the CMOS NAND2 output ZN, so
* (Clk-edge -> dyn) is the direct analog of the CMOS (input -> ZN) logic delay.
.include /soe/czeng14/software/pdk/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /soe/czeng14/software/pdk/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical
.include /mada/users/czeng14/projects/brainstorm/domino/lsdl_lib/cells/lsdl_basic/lsdl_nand2_x1.spice
Vvdd VPWR 0 5
Vgnd VGND 0 0
Vclk Clk 0 PULSE(0 5 5n 100p 100p 9.9n 20n)
Va1 A1 0 PWL(0 0 20n 0 20.1n 5 60n 5 60.1n 0 80n 0 80.1n 5)
Va2 A2 0 PWL(0 0 20n 0 20.1n 5 40n 5 40.1n 0 60n 0 60.1n 5)
Xnand A1 A2 Clk Out VPWR VGND lsdl_nand2_x1
Cload Out 0 5f
.ic v(Xnand.dyn)=5
.ic v(Xnand.nint)=0
.control
tran 20p 110n uic
* cyc2 eval edge = 2nd Clk rise (25 ns), A1=A2=1 -> dyn discharges
* (1) raw n-tree NAND eval: Clk-edge -> dyn falls   <-- compare to CMOS input->ZN
meas tran t_clk_dyn  TRIG v(Clk) VAL=2.5 RISE=2 TARG v(Xnand.dyn)  VAL=2.5 FALL=1
* (2) + predriver: Clk-edge -> out_b rises (out_b = A1.A2)
meas tran t_clk_outb TRIG v(Clk) VAL=2.5 RISE=2 TARG v(Xnand.out_b) VAL=2.5 RISE=1
* (3) + output driver: Clk-edge -> Out falls (full clk-to-out)
meas tran t_clk_out  TRIG v(Clk) VAL=2.5 RISE=2 TARG v(Out)         VAL=2.5 FALL=1
.endc
.end

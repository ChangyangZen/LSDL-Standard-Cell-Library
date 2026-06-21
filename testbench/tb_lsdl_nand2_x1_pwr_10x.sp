* tb_lsdl_nand2_x1_pwr_10x.sp — LSDL NAND2 at 500 MHz (10x faster clock).
.include /soe/czeng14/software/pdk/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /soe/czeng14/software/pdk/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical
.include /mada/users/czeng14/projects/brainstorm/domino/lsdl_lib/cells/lsdl_basic/lsdl_nand2_x1.spice
Vvdd VPWR 0 5
Vgnd VGND 0 0
Vclk Clk 0 PULSE(0 5 0.5n 10p 10p 0.99n 2n)
Va1 A1 0 PWL(0 0 2n 0 2.01n 5 6n 5 6.01n 0 8n 0 8.01n 5)
Va2 A2 0 PWL(0 0 2n 0 2.01n 5 4n 5 4.01n 0 6n 0 6.01n 5)
Xnand A1 A2 Clk Out VPWR VGND lsdl_nand2_x1
Cload Out 0 5f
.ic v(Xnand.dyn)=5
.ic v(Xnand.nint)=0
.control
tran 2p 11n uic
meas tran tpd_eval_hl TRIG v(Clk) VAL=2.5 RISE=2 TARG v(Out) VAL=2.5 FALL=1
let isup = -i(Vvdd)
meas tran i_avg AVG isup from=2n to=10n
meas tran p_avg AVG (5*isup) from=2n to=10n
wrdata /soe/czeng14/projects/brainstorm-domino-tmp/lsdl_10x.dat v(Clk) v(A1) v(A2) v(Xnand.dyn) v(Xnand.out_b) v(Out) isup
.endc
.end

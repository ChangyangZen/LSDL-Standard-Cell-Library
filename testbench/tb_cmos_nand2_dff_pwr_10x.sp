* tb_cmos_nand2_dff_pwr_10x.sp — static CMOS NAND2->DFF at 500 MHz (10x faster).
.include /soe/czeng14/software/pdk/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /soe/czeng14/software/pdk/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical
.include /soe/czeng14/software/pdk/gf180mcuD/libs.ref/gf180mcu_fd_sc_mcu9t5v0/spice/gf180mcu_fd_sc_mcu9t5v0.spice
Vvdd VPWR 0 5
Vgnd VGND 0 0
Vclk CLK 0 PULSE(0 5 0.5n 10p 10p 0.99n 2n)
Va1 A1 0 PWL(0 0 0.6n 0 0.61n 5)
Va2 A2 0 PWL(0 0 0.6n 0 0.61n 5 2.6n 5 2.61n 0 4.6n 0 4.61n 5 6.6n 5 6.61n 0 8.6n 0 8.61n 5)
Xnand A1 A2 ZN  VPWR VPWR VGND VGND gf180mcu_fd_sc_mcu9t5v0__nand2_1
Xdff  ZN CLK Q  VPWR VPWR VGND VGND gf180mcu_fd_sc_mcu9t5v0__dffq_1
Cload Q 0 5f
.control
tran 2p 11n
meas tran t_nand2 TRIG v(A2) VAL=2.5 RISE=1 TARG v(ZN) VAL=2.5 FALL=1
meas tran tcq_fall TRIG v(CLK) VAL=2.5 RISE=2 TARG v(Q) VAL=2.5 FALL=1
let isup = -i(Vvdd)
meas tran i_avg AVG isup from=2n to=10n
meas tran p_avg AVG (5*isup) from=2n to=10n
wrdata /soe/czeng14/projects/brainstorm-domino-tmp/cmos_10x.dat v(A1) v(A2) v(ZN) v(CLK) v(Q) isup
.endc
.end

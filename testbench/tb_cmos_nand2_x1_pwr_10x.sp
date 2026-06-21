* tb_cmos_nand2_x1_pwr_10x.sp — static CMOS NAND2 (combinational) at 10x input rate.
.include /soe/czeng14/software/pdk/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /soe/czeng14/software/pdk/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical
.include /mada/users/czeng14/projects/brainstorm/domino/lsdl_lib/cells/cmos_ref/cmos_nand2_x1.spice
Vvdd VPWR 0 5
Vgnd VGND 0 0
Va1 A1 0 PWL(0 0 1n 0 1.01n 5)
Va2 A2 0 PWL(0 0 3n 0 3.01n 5 5n 5 5.01n 0 7n 0 7.01n 5 9n 5 9.01n 0)
Xnand A1 A2 Out VPWR VGND cmos_nand2_x1
Cload Out 0 5f
.control
tran 2p 11n
meas tran tpd_fall TRIG v(A2) VAL=2.5 RISE=1 TARG v(Out) VAL=2.5 FALL=1
meas tran tpd_rise TRIG v(A2) VAL=2.5 FALL=1 TARG v(Out) VAL=2.5 RISE=1
let isup = -i(Vvdd)
meas tran i_avg AVG isup from=1n to=10n
wrdata /soe/czeng14/projects/brainstorm-domino-tmp/cmos_comb_10x.dat v(A1) v(A2) v(Out) isup
.endc
.end

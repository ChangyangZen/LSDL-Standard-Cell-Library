* tb_cmos_nand2_x1_pwr.sp — static CMOS NAND2 propagation delay + power + waveforms.
* Combinational: NO clock. Out = !(A1&A2). Drive same (A1,A2) pattern as LSDL tb.
.include /soe/czeng14/software/pdk/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /soe/czeng14/software/pdk/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical
.include /mada/users/czeng14/projects/brainstorm/domino/lsdl_lib/cells/cmos_ref/cmos_nand2_x1.spice

Vvdd VPWR 0 5
Vgnd VGND 0 0
* A1 high throughout from 10n; A2 pulses so Out = !(A1&A2) toggles cleanly.
Va1 A1 0 PWL(0 0 10n 0 10.1n 5)
Va2 A2 0 PWL(0 0 30n 0 30.1n 5 50n 5 50.1n 0 70n 0 70.1n 5 90n 5 90.1n 0)
Xnand A1 A2 Out VPWR VGND cmos_nand2_x1
Cload Out 0 5f

.control
tran 20p 110n
* input->output propagation delays (A2 is the switching input here):
*  Out falls when A2 rises (both high): A2 rising edge #1 at 30.1n
meas tran tpd_fall TRIG v(A2) VAL=2.5 RISE=1 TARG v(Out) VAL=2.5 FALL=1
*  Out rises when A2 falls: A2 falling edge #1 at 50.1n
meas tran tpd_rise TRIG v(A2) VAL=2.5 FALL=1 TARG v(Out) VAL=2.5 RISE=1
let isup = -i(Vvdd)
meas tran i_avg AVG isup from=10n to=100n
meas tran i_peak MAX isup from=10n to=100n
let psup = 5*isup
meas tran p_avg AVG psup from=10n to=100n
wrdata /soe/czeng14/projects/brainstorm-domino-tmp/cmos_nand2_wave.dat v(A1) v(A2) v(Out) isup
.endc
.end

* tb_cmos_nand2_dff_pwr.sp — STATIC CMOS sequential equivalent of one LSDL NAND2:
* vendor NAND2 (combinational) -> vendor DFF (register). Same GF180 5V technology.
* Measures DFF clk-to-Q, the NAND2 logic delay (must fit in the cycle), and power.
.include /soe/czeng14/software/pdk/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /soe/czeng14/software/pdk/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical
.include /soe/czeng14/software/pdk/gf180mcuD/libs.ref/gf180mcu_fd_sc_mcu9t5v0/spice/gf180mcu_fd_sc_mcu9t5v0.spice

Vvdd VPWR 0 5
Vgnd VGND 0 0
* positive-edge DFF clock: rising edges at 5,25,45,65,85 ns (period 20 ns)
Vclk CLK 0 PULSE(0 5 5n 100p 100p 9.9n 20n)
* A1 high from 6 ns; A2 toggles each cycle (changes just after a capture edge,
* settles through NAND2 well before the next edge -> meets setup).
Va1 A1 0 PWL(0 0 6n 0 6.1n 5)
Va2 A2 0 PWL(0 0 6n 0 6.1n 5 26n 5 26.1n 0 46n 0 46.1n 5 66n 5 66.1n 0 86n 0 86.1n 5)

* vendor cells: nand2_1 (A1 A2 ZN VDD VNW VPW VSS), dffq_1 (D CLK Q VDD VNW VPW VSS)
Xnand A1 A2 ZN  VPWR VPWR VGND VGND gf180mcu_fd_sc_mcu9t5v0__nand2_1
Xdff  ZN CLK Q  VPWR VPWR VGND VGND gf180mcu_fd_sc_mcu9t5v0__dffq_1
Cload Q 0 5f

.control
tran 20p 110n
* NAND2 combinational logic delay (A2 -> ZN), the data-path delay inside the cycle
meas tran t_nand2 TRIG v(A2) VAL=2.5 RISE=1 TARG v(ZN) VAL=2.5 FALL=1
* DFF clk-to-Q: 2nd rising clk edge (25 ns) captures A2=1 -> ZN=0 -> Q falls
meas tran tcq_fall TRIG v(CLK) VAL=2.5 RISE=2 TARG v(Q) VAL=2.5 FALL=1
* 3rd rising clk edge (45 ns) captures A2=0 -> ZN=1 -> Q rises
meas tran tcq_rise TRIG v(CLK) VAL=2.5 RISE=3 TARG v(Q) VAL=2.5 RISE=1
let isup = -i(Vvdd)
meas tran i_avg AVG isup from=10n to=100n
meas tran i_peak MAX isup from=10n to=100n
let psup = 5*isup
meas tran p_avg AVG psup from=10n to=100n
wrdata /soe/czeng14/projects/brainstorm-domino-tmp/cmos_seq_wave.dat v(A1) v(A2) v(ZN) v(CLK) v(Q) isup
.endc
.end

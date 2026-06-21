* tb_lsdl_nand2_x1_pwr.sp — waveform + timing + power probe for lsdl_nand2_x1.
* Same cycle plan as tb_lsdl_nand2_x1.sp, plus supply-current measurement and a
* waveform dump (wrdata) for plotting. ngspice .control block.

.include /soe/czeng14/software/pdk/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /soe/czeng14/software/pdk/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical
.include /mada/users/czeng14/projects/brainstorm/domino/lsdl_lib/cells/lsdl_basic/lsdl_nand2_x1.spice

* supply (current measured through Vvdd), ground, clock
Vvdd  VPWR 0 5
Vgnd  VGND 0 0
Vclk  Clk  0  PULSE(0 5 5n 100p 100p 9.9n 20n)
* A1: 0,1,1,0,1 ; A2: 0,1,0,1,1  (transitions mid-precharge)
Va1  A1  0  PWL(0 0 20n 0 20.1n 5 60n 5 60.1n 0 80n 0 80.1n 5)
Va2  A2  0  PWL(0 0 20n 0 20.1n 5 40n 5 40.1n 0 60n 0 60.1n 5)

Xnand A1 A2 Clk Out VPWR VGND lsdl_nand2_x1
Cload Out 0 5f

.ic v(Xnand.dyn)=5
.ic v(Xnand.nint)=0

.control
tran 20p 110n uic
* --- timing ---
meas tran tpd_eval_hl TRIG v(Clk) VAL=2.5 RISE=2 TARG v(Out) VAL=2.5 FALL=1
* --- supply current (current delivered to cell = -i(Vvdd)) ---
let isup = -i(Vvdd)
meas tran i_avg   AVG isup from=20n to=100n
meas tran i_peak  MAX isup from=20n to=100n
* --- average power over 4 cycles (P = VDD * Iavg) ---
let psup = 5 * isup
meas tran p_avg   AVG psup from=20n to=100n
* --- energy in the full-eval cycle (cyc2, 25-45ns): integral of charge * VDD ---
meas tran q_cyc2  integ isup from=25n to=45n
* --- dump waveforms for plotting ---
wrdata /soe/czeng14/projects/brainstorm-domino-tmp/nand2_wave.dat v(Clk) v(A1) v(A2) v(Xnand.dyn) v(Xnand.out_b) v(Out) isup
.endc
.end

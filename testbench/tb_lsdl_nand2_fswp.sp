* tb_lsdl_nand2_fswp.sp — frequency sweep for LSDL NAND2.
* Period set by parameter PERIOD (ns). Duty cycle 50%.
* Measures: clk->dyn, clk->Out, whether Out reaches 2.5V in the evaluate window,
* and the timing margin remaining at end of window.
* Call with: ngspice -b ... --param PERIOD=0.7
.param PERIOD=1.0        $ default 1GHz; override from command line
.param HALF={PERIOD/2}   $ evaluate window = HALF

.include /soe/czeng14/software/pdk/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /soe/czeng14/software/pdk/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical
.include /mada/users/czeng14/projects/brainstorm/domino/lsdl_lib/cells/lsdl_basic/lsdl_nand2_x1.spice

Vvdd VPWR 0 5
Vgnd VGND 0 0
Vclk Clk 0 PULSE(0 5 {HALF} 10p 10p {HALF-0.02n} {PERIOD})
* inputs transition 10% into precharge (safe for any frequency)
Va1 A1 0 PWL(0 0 {HALF*1.1} 0 {HALF*1.1+0.01n} 5)
Va2 A2 0 PWL(0 0 {HALF*1.1} 0 {HALF*1.1+0.01n} 5)
Xnand A1 A2 Clk Out VPWR VGND lsdl_nand2_x1
Cload Out 0 5f
.ic v(Xnand.dyn)=5

.control
tran 1p {PERIOD*4} uic
* clk evaluate edge = 2nd Clk rise
meas tran t_clk_dyn  TRIG v(Clk) VAL=2.5 RISE=2 TARG v(Xnand.dyn)  VAL=2.5 FALL=1
meas tran t_clk_out  TRIG v(Clk) VAL=2.5 RISE=2 TARG v(Out)         VAL=2.5 FALL=1
* guard = evaluate_window - t_clk_out  (positive = passes, negative = fails)
let t_guard_ns = {HALF} - t_clk_out*1e9
let pct_guard  = t_guard_ns / {PERIOD} * 100
print t_clk_out t_guard_ns pct_guard
.endc
.end

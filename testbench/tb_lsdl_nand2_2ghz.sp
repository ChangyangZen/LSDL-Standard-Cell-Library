* tb_lsdl_nand2_2ghz.sp — LSDL NAND2 @ 2 GHz (period 0.5 ns, 40x original).
* Precharge window = 0.25 ns, evaluate window = 0.25 ns.
* The cell's clk-to-out is ~254 ps, so we probe all 4 internal stages to see
* which complete within the window and where the latch kicks in.
* Node roles:
*   dyn    = dynamic node = raw NAND eval result BEFORE the latch
*   out_b  = predriver output = node the KEEPER LATCH holds
*   Out    = final registered output AFTER latch (output driver)
*   isup   = supply current (shows precharge pulse every cycle)

.include /soe/czeng14/software/pdk/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /soe/czeng14/software/pdk/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical
.include /mada/users/czeng14/projects/brainstorm/domino/lsdl_lib/cells/lsdl_basic/lsdl_nand2_x1.spice

Vvdd VPWR 0 5
Vgnd VGND 0 0
* 2 GHz clock: period 0.5ns, precharge low first (0..0.25ns), eval high (0.25..0.5ns)
Vclk Clk 0 PULSE(0 5 0.25n 10p 10p 0.24n 0.5n)
* inputs transition mid-precharge (0.05ns after clk falls):
*   cyc1(0-0.5ns)  A1=0 A2=0 -> dyn stays high -> Out=1
*   cyc2(0.5-1ns)  A1=1 A2=1 -> full discharge -> Out=0  (shows timing limit)
*   cyc3(1-1.5ns)  A1=1 A2=0 -> partial (charge-share stress)
*   cyc4(1.5-2ns)  A1=1 A2=1 -> recovery
Va1 A1 0 PWL(0 0  0.3n 0  0.30n 5)
Va2 A2 0 PWL(0 0  0.3n 0  0.30n 5  0.8n 5  0.80n 0  1.3n 0  1.30n 5)

Xnand A1 A2 Clk Out VPWR VGND lsdl_nand2_x1
Cload Out 0 5f

.ic v(Xnand.dyn)=5
.ic v(Xnand.nint)=0

.control
tran 1p 2n uic

* clk -> dyn (raw logic, before latch)
meas tran t_clk_dyn  TRIG v(Clk) VAL=2.5 RISE=2 TARG v(Xnand.dyn)  VAL=2.5 FALL=1
* clk -> out_b (predriver output, node the latch holds)
meas tran t_clk_outb TRIG v(Clk) VAL=2.5 RISE=2 TARG v(Xnand.out_b) VAL=2.5 RISE=1
* clk -> Out (final output, after output driver)
meas tran t_clk_out  TRIG v(Clk) VAL=2.5 RISE=2 TARG v(Out)         VAL=2.5 FALL=1

let isup = -i(Vvdd)
meas tran i_avg AVG isup from=0.3n to=1.8n

wrdata /soe/czeng14/projects/brainstorm-domino-tmp/lsdl_2ghz.dat v(Clk) v(A1) v(A2) v(Xnand.dyn) v(Xnand.out_b) v(Out) isup
.endc
.end

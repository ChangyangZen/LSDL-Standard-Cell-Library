* tb_lsdl_inv_x1.sp — testbench for lsdl_inv_x1 against GF180MCU 5V models.
*
* Drives a sequence of (Clk, A) inputs and probes dyn, out_b, Out to verify
* paper Fig. 1 behavior on a single inverter cell:
*
*   - Phase 1 (Clk low):  precharge.  dyn -> VPWR.  Foot off => n-tree
*                         disconnected.  Latch holds previous Out via
*                         feedback devices.
*   - Phase 2 (Clk high): evaluate.  Foot on => n-tree connected.
*                         If A=1, dyn discharges to gnd; predriver pulls
*                         out_b high; output driver pulls Out low (Out = !A).
*                         If A=0, dyn stays high; out_b stays at its
*                         latched value (low through predriver n via
*                         header); Out stays high.
*
* Glitch sizing check (paper p. 278): peak glitch on out_b during the
* dyn-falling transition must be < 10% VDD = < 0.5 V at 5 V supply.

* ---------------------------------------------------------------
* PDK models — typical corner, no statistical variation.
* ---------------------------------------------------------------
* GF180MCU PDK setup: defines sw_stat_global, sw_stat_mismatch,
* fnoicor and any other required model parameters with vendor defaults.
.include /soe/czeng14/software/pdk/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /soe/czeng14/software/pdk/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical

.include /mada/users/czeng14/projects/brainstorm/domino/lsdl_lib/cells/lsdl_basic/lsdl_inv_x1.spice

* ---------------------------------------------------------------
* Supply and stimulus
* ---------------------------------------------------------------
Vvdd  VPWR 0 5
Vgnd  VGND 0 0

* Clock: precharge (low) for 10 ns, evaluate (high) for 10 ns, period 20 ns.
* 100 ps rise/fall edges.
Vclk  Clk  0  PULSE(0 5 5n 100p 100p 9.9n 20n)

* Input A: transitions during precharge phase only (Clk low: 0-5, 15-25,
*   35-45, 55-65, 75-85 ns ...).
* Cycles (each eval starts at t = 5, 25, 45, 65, 85 ns):
*   cyc1 eval@5ns  : A=0  -> dyn stays high  -> Out latched high
*   cyc2 eval@25ns : A=0  -> same
*   cyc3 eval@45ns : A=1  -> dyn falls       -> Out -> 0; latched low
*   cyc4 eval@65ns : A=1  -> same as cyc3
*   cyc5 eval@85ns : A=0  -> dyn stays high; latched-low must persist
*                            (THIS is the glitch-stress cycle: at eval
*                             start, Predriver n pulls out_b LOW from its
*                             latched-high value before dyn confirms)
Va  A  0  PWL(0 0 40n 0 40.1n 5 80n 5 80.1n 0)

* ---------------------------------------------------------------
* DUT
* ---------------------------------------------------------------
Xinv  A Clk Out VPWR VGND lsdl_inv_x1

* Load on Out: capacitor representing one fanout (rough FO4 estimate).
Cload Out 0 5f

* ---------------------------------------------------------------
* Simulation control
* ---------------------------------------------------------------
.ic v(Xinv.dyn)=5
.tran 50p 200n uic

* Measurements
* Cycle 3 (eval@45ns) is first real eval with A=1: Out should fall.
.meas tran tpd_eval_lh
+      TRIG v(Clk) VAL=2.5 RISE=3
+      TARG v(Out) VAL=2.5 FALL=1

* Cycle 5 (eval@85ns) is the GLITCH stress: previous latched state has
* Out=low (out_b=high), and now A=0 means dyn stays high through eval.
* At eval start, Header+Predriver-n briefly pull out_b LOW from its
* latched-high value. Paper rule: dip must keep out_b > 0.9*VDD = 4.5V.
.meas tran v_out_b_min_glitch  MIN v(Xinv.out_b) FROM=85n TO=95n

* dyn floor during real eval (cycle 3): should be near 0V (~ -50mV
* sim undershoot is acceptable, full discharge).
.meas tran v_dyn_low_min       MIN v(Xinv.dyn)   FROM=45n TO=55n

* Final Out value after settling — should be high (last A=0 cycle).
.meas tran v_out_final         AVG v(Out)        FROM=95n TO=100n

.print tran v(Clk) v(A) v(Xinv.dyn) v(Xinv.out_b) v(Out)
.end

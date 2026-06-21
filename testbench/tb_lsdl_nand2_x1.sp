* tb_lsdl_nand2_x1.sp — testbench for lsdl_nand2_x1 at GF180MCU 5V.
*
* Sequences (A1, A2) cleanly between cycles (inputs transition during
* precharge only) to verify Out = !(A1 & A2) and to expose charge
* sharing on the internal node `nint`.
*
* Charge-sharing stress (paper p. 278): in eval phase with A1=1, A2=0,
* the top NMOS turns on but the bottom does not. If `nint` was driven
* low in a previous cycle, dyn (precharged high) redistributes with
* nint upon eval, dropping dyn. If the drop exceeds the predriver-n
* threshold, Out glitches.
*
* Clock: 20 ns period, eval start at t = 5, 25, 45, 65, 85 ns.
* Inputs transition during precharge phase (15-25, 35-45, 55-65 ns).
*
* Cycle plan:
*   cyc1 [5..25]   A1=0 A2=0 -> dyn stays high -> Out=1
*   cyc2 [25..45]  A1=1 A2=1 -> dyn falls (full discharge) -> Out=0
*   cyc3 [45..65]  A1=1 A2=0 -> dyn stays high BUT charge-sharing with
*                               nint that was driven low in cyc2.
*                               THIS is the charge-sharing stress.
*   cyc4 [65..85]  A1=0 A2=1 -> top NMOS off, no charge-share path
*   cyc5 [85..105] A1=1 A2=1 -> verify recovery, Out=0 again

* ---------------------------------------------------------------
* PDK setup
* ---------------------------------------------------------------
.include /soe/czeng14/software/pdk/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /soe/czeng14/software/pdk/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical
.include /mada/users/czeng14/projects/brainstorm/domino/lsdl_lib/cells/lsdl_basic/lsdl_nand2_x1.spice

* ---------------------------------------------------------------
* Supply and stimulus
* ---------------------------------------------------------------
Vvdd  VPWR 0 5
Vgnd  VGND 0 0

* Clock: precharge low first half. 100 ps edges, period 20 ns.
Vclk  Clk  0  PULSE(0 5 5n 100p 100p 9.9n 20n)

* A1: 0,1,1,0,1 — transitions in mid-precharge.
Va1  A1  0  PWL(0 0 20n 0 20.1n 5 60n 5 60.1n 0 80n 0 80.1n 5)

* A2: 0,1,0,1,1 — transitions in mid-precharge.
Va2  A2  0  PWL(0 0 20n 0 20.1n 5 40n 5 40.1n 0 60n 0 60.1n 5)

* ---------------------------------------------------------------
* DUT
* ---------------------------------------------------------------
Xnand A1 A2 Clk Out VPWR VGND lsdl_nand2_x1
Cload Out 0 5f

* ---------------------------------------------------------------
* Simulation control
* ---------------------------------------------------------------
.ic v(Xnand.dyn)=5
.ic v(Xnand.nint)=0
.tran 50p 110n uic

* ---------------------------------------------------------------
* Measurements
* ---------------------------------------------------------------
* Eval delay on cycle 2 (first real discharge, A1=A2=1).
.meas tran tpd_eval_hl
+      TRIG v(Clk) VAL=2.5 RISE=2
+      TARG v(Out) VAL=2.5 FALL=1

* dyn floor during cycle 2 (full discharge expected).
.meas tran v_dyn_low_min  MIN v(Xnand.dyn)  FROM=25n TO=45n

* Charge-sharing case: cycle 3 (A1=1, A2=0). dyn should stay high
* but is being pulled down by charge redistribution with nint.
* The MIN over the eval window tells us how far dyn drops.
.meas tran v_dyn_share_min MIN v(Xnand.dyn) FROM=45n TO=65n

* If charge sharing causes Out to incorrectly transition during cyc3,
* v_out_cyc3 will dip from its expected high value.
.meas tran v_out_cyc3_min MIN v(Out) FROM=45n TO=65n

* Verify cyc5 fully recovers (A1=A2=1, expect Out -> 0).
.meas tran v_out_cyc5_final AVG v(Out) FROM=100n TO=104n

.print tran v(Clk) v(A1) v(A2) v(Xnand.dyn) v(Xnand.nint) v(Xnand.out_b) v(Out)
.end

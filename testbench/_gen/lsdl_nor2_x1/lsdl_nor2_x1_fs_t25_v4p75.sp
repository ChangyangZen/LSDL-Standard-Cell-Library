* tb_lsdl_nor2_x1.sp — testbench for lsdl_nor2_x1 at GF180MCU 5V.
* Out = !(A1+A2). 2 parallel NMOS. No internal stack node (no charge-share stress).
* Stress: single-input (weakest) and dual-input (fastest) discharge paths.
* Clock 20 ns, eval high second half; inputs switch mid-precharge.
*   cyc1 [5..25]   A=00 -> dyn high -> Out=1
*   cyc2 [25..45]  A=11 -> fast discharge (both parallel) -> Out=0  (tpd_eval_hl)
*   cyc3 [45..65]  A=10 -> single-path discharge (slower) -> Out=0
*   cyc4 [65..85]  A=00 -> recovery -> Out=1
*   cyc5 [85..105] A=01 -> single-path discharge -> Out=0
*   cyc6 [105..125] A=00 -> recovery -> Out=1
*   cyc7 [125..145] A=00 -> Out stays 1, dyn stays high -> out_b glitch window

.include /soe/czeng14/software/pdk/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /soe/czeng14/software/pdk/gf180mcuD/libs.tech/ngspice/sm141064.ngspice fs
.options TEMP=25
.include /mada/users/czeng14/projects/brainstorm/domino/lsdl_lib/cells/lsdl_basic/lsdl_nor2_x1.spice

Vvdd  VPWR 0 4.75
Vgnd  VGND 0 0
Vclk  Clk  0  PULSE(0 5 5n 100p 100p 9.9n 20n)

* A1: 0,1,1,0,0   A2: 0,1,0,0,1
Va1  A1  0  PWL(0 0 20n 0 20.1n 5 60n 5 60.1n 0)
Va2  A2  0  PWL(0 0 20n 0 20.1n 5 40n 5 40.1n 0 80n 0 80.1n 5 100n 5 100.1n 0)

Xnor A1 A2 Clk Out VPWR VGND lsdl_nor2_x1
Cload Out 0 5f

.ic v(Xnor.dyn)=5
.tran 50p 150n uic

* eval delay, cyc2 (A=11, full parallel).
.meas tran tpd_eval_hl
+      TRIG v(Clk) VAL=2.5 RISE=2
+      TARG v(Out) VAL=2.5 FALL=1
* dyn floor, cyc2 (full parallel discharge).
.meas tran v_dyn_low_min    MIN v(Xnor.dyn) FROM=25n TO=45n
* dyn floor under single-input discharge, cyc3 (weakest path; must still fully discharge).
.meas tran v_dyn_single_min MIN v(Xnor.dyn) FROM=45n TO=65n
* glitch on out_b in a stay-high evaluate cycle, cyc7 (Out already high, dyn
* stays high; paper rule: out_b bump < 10% VDD when header turns on).
.meas tran v_out_b_glitch   MAX v(Xnor.out_b) FROM=125n TO=135n
* recovery to high, cyc4.
.meas tran v_out_cyc4_hi    AVG v(Out)      FROM=80n TO=84n

* (.print stripped for sweep)
.end

* tb_lsdl_nand3_x1.sp — testbench for lsdl_nand3_x1 at GF180MCU 5V.
* Out = !(A1&A2&A3). 3-series eval stack with nint1, nint2 internal nodes.
* Clock 20 ns, eval high second half; inputs switch mid-precharge.
* Cycle plan:
*   cyc1 [5..25]   A=000 -> dyn high -> Out=1
*   cyc2 [25..45]  A=111 -> full discharge -> Out=0   (tpd_eval_hl)
*   cyc3 [45..65]  A=100 -> top only; dyn shares with nint1,nint2 (low from cyc2).
*                          WORST charge-share stress (deepest stack node pre-driven low).
*   cyc4 [65..85]  A=110 -> two on, bottom off (partial, milder)
*   cyc5 [85..105] A=111 -> recovery, Out=0

.include /soe/czeng14/software/pdk/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /soe/czeng14/software/pdk/gf180mcuD/libs.tech/ngspice/sm141064.ngspice ss
.options TEMP=125
.include /mada/users/czeng14/projects/brainstorm/domino/lsdl_lib/cells/lsdl_basic/lsdl_nand3_x1.spice

Vvdd  VPWR 0 5.25
Vgnd  VGND 0 0
Vclk  Clk  0  PULSE(0 5 5n 100p 100p 9.9n 20n)

* A1: 0,1,1,1,1   A2: 0,1,0,1,1   A3: 0,1,0,0,1
Va1  A1  0  PWL(0 0 20n 0 20.1n 5)
Va2  A2  0  PWL(0 0 20n 0 20.1n 5 40n 5 40.1n 0 60n 0 60.1n 5)
Va3  A3  0  PWL(0 0 20n 0 20.1n 5 40n 5 40.1n 0 80n 0 80.1n 5)

Xnand A1 A2 A3 Clk Out VPWR VGND lsdl_nand3_x1
Cload Out 0 5f

.ic v(Xnand.dyn)=5
.ic v(Xnand.nint1)=0
.ic v(Xnand.nint2)=0
.tran 50p 110n uic

* eval delay, cyc2 (A=111).
.meas tran tpd_eval_hl
+      TRIG v(Clk) VAL=2.5 RISE=2
+      TARG v(Out) VAL=2.5 FALL=1
* dyn full-discharge floor, cyc2.
.meas tran v_dyn_low_min   MIN v(Xnand.dyn)  FROM=25n TO=45n
* charge-share floor, cyc3 (A=100); must stay > 3.5 V.
.meas tran v_dyn_share_min MIN v(Xnand.dyn)  FROM=45n TO=65n
* Out must stay high during the charge-share cycle.
.meas tran v_out_cyc3_min  MIN v(Out)        FROM=45n TO=65n
* recovery: Out -> 0 in cyc5.
.meas tran v_out_cyc5_final AVG v(Out)        FROM=100n TO=104n

* (.print stripped for sweep)
.end

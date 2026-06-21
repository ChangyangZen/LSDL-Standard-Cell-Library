* tb_lsdl_nand4_x1.sp — testbench for lsdl_nand4_x1 at GF180MCU 5V.
* Out = !(A1&A2&A3&A4). 4-series eval stack -> deepest charge-sharing case.
* Clock 20 ns, eval at 5,25,45,65,85 ns; inputs switch mid-precharge.
* Cycle plan:
*   cyc1 [5..25]   A=0000 -> dyn high -> Out=1
*   cyc2 [25..45]  A=1111 -> full discharge -> Out=0   (tpd_eval_hl)
*   cyc3 [45..65]  A=1000 -> only top NMOS on; dyn shares with nint1..3
*                            (driven low in cyc2). WORST charge-share stress.
*   cyc4 [65..85]  A=1110 -> 3 on, bottom off (deep partial)
*   cyc5 [85..105] A=1111 -> recovery, Out=0

.include /soe/czeng14/software/pdk/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /soe/czeng14/software/pdk/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical
.options TEMP=125
.include /mada/users/czeng14/projects/brainstorm/domino/lsdl_lib/cells/lsdl_basic/lsdl_nand4_x1.spice

Vvdd  VPWR 0 5.25
Vgnd  VGND 0 0
Vclk  Clk  0  PULSE(0 5 5n 100p 100p 9.9n 20n)

* A1: 0,1,1,1,1   A2: 0,1,0,1,1   A3: 0,1,0,1,1   A4: 0,1,0,0,1
Va1  A1  0  PWL(0 0 20n 0 20.1n 5)
Va2  A2  0  PWL(0 0 20n 0 20.1n 5 40n 5 40.1n 0 60n 0 60.1n 5)
Va3  A3  0  PWL(0 0 20n 0 20.1n 5 40n 5 40.1n 0 60n 0 60.1n 5)
Va4  A4  0  PWL(0 0 20n 0 20.1n 5 40n 5 40.1n 0 80n 0 80.1n 5)

Xnand A1 A2 A3 A4 Clk Out VPWR VGND lsdl_nand4_x1
Cload Out 0 5f

.ic v(Xnand.dyn)=5
.ic v(Xnand.nint1)=0
.ic v(Xnand.nint2)=0
.ic v(Xnand.nint3)=0
.tran 50p 110n uic

* eval delay, cyc2 (A=1111).
.meas tran tpd_eval_hl
+      TRIG v(Clk) VAL=2.5 RISE=2
+      TARG v(Out) VAL=2.5 FALL=1
* dyn full-discharge floor, cyc2.
.meas tran v_dyn_low_min   MIN v(Xnand.dyn)  FROM=25n TO=45n
* charge-share floor, cyc3 (A=1000); must stay > 3.5 V.
.meas tran v_dyn_share_min MIN v(Xnand.dyn)  FROM=45n TO=65n
* Out must stay high through the charge-share cycle.
.meas tran v_out_cyc3_min  MIN v(Out)        FROM=45n TO=65n
* recovery: Out -> 0 in cyc5.
.meas tran v_out_cyc5_final AVG v(Out)        FROM=100n TO=104n

* (.print stripped for sweep)
.end

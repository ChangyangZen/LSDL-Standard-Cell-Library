* tb_lsdl_aoi21_x1.sp — testbench for lsdl_aoi21_x1 at GF180MCU 5V.
* Out = !((A1&A2)+B). Series arm A1-A2 in parallel with single B path.
* Internal node: nint (between XNA and XNB in the A1-A2 series arm).
* Charge-share stress: arm-A partial eval (A1=1,A2=0) after A1A2=11 drove nint low.
* Clock 20 ns, eval high second half; inputs switch mid-precharge.
*   cyc1 [5..25]   A=00 B=0 -> dyn high -> Out=1
*   cyc2 [25..45]  A1=1,A2=1,B=0 -> arm-A discharges -> Out=0  (tpd_eval_hl)
*   cyc3 [45..65]  A1=1,A2=0,B=0 -> arm-A partial; dyn shares w/ nint (low from cyc2).
*                                   WORST charge-share stress on nint.
*   cyc4 [65..85]  B=1 A=00 -> single B path discharges -> Out=0
*   cyc5 [85..105] A1=1,A2=1,B=1 -> both arms -> Out=0

.include /soe/czeng14/software/pdk/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /soe/czeng14/software/pdk/gf180mcuD/libs.tech/ngspice/sm141064.ngspice sf
.options TEMP=-40
.include /mada/users/czeng14/projects/brainstorm/domino/lsdl_lib/cells/lsdl_basic/lsdl_aoi21_x1.spice

Vvdd  VPWR 0 5.0
Vgnd  VGND 0 0
Vclk  Clk  0  PULSE(0 5 5n 100p 100p 9.9n 20n)

* A1: 0,1,1,0,1   A2: 0,1,0,0,1   B: 0,0,0,1,1
Va1  A1  0  PWL(0 0 20n 0 20.1n 5 60n 5 60.1n 0 80n 0 80.1n 5)
Va2  A2  0  PWL(0 0 20n 0 20.1n 5 40n 5 40.1n 0 80n 0 80.1n 5)
Vb   B   0  PWL(0 0 60n 0 60.1n 5)

Xaoi A1 A2 B Clk Out VPWR VGND lsdl_aoi21_x1
Cload Out 0 5f

.ic v(Xaoi.dyn)=5
.ic v(Xaoi.nint)=0
.tran 50p 110n uic

* eval delay, cyc2 (arm-A full discharge).
.meas tran tpd_eval_hl
+      TRIG v(Clk) VAL=2.5 RISE=2
+      TARG v(Out) VAL=2.5 FALL=1
* dyn floor, cyc2 (arm-A full discharge).
.meas tran v_dyn_low_min   MIN v(Xaoi.dyn) FROM=25n TO=45n
* charge-share floor, cyc3 (arm-A partial); must stay > 3.5 V.
.meas tran v_dyn_share_min MIN v(Xaoi.dyn) FROM=45n TO=65n
* B-arm discharge floor, cyc4 (single B path).
.meas tran v_dyn_armb_min  MIN v(Xaoi.dyn) FROM=65n TO=85n
* Out settled high during charge-share cycle (late in window).
.meas tran v_out_cyc3_settled AVG v(Out) FROM=60n TO=64n

* (.print stripped for sweep)
.end

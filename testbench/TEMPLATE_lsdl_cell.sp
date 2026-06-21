* TEMPLATE_lsdl_cell.sp — per-cell LSDL testbench skeleton (GF180MCU 5V).
*
* Fill the {{...}} placeholders per cell. Structure mirrors the two proven
* Wave-0 testbenches (tb_lsdl_inv_x1.sp, tb_lsdl_nand2_x1.sp). The same file
* serves the schematic PVT sweep (pvt_sweep.py) AND the PEX gate (pex_validate.py
* swaps the .include for the extracted netlist and de-hierarchies the probes).
*
* CONVENTIONS (do not change without updating pvt_sweep.py / pex_validate.py):
*   - Cell instance MUST be named X{{INST}} and its pins in .subckt order.
*   - Internal probes referenced as v(X{{INST}}.<net>) — pex mk-tb rewrites these.
*   - Clock: precharge low first half, eval high second half. 20 ns period.
*   - Inputs transition ONLY during precharge (…0.1n after each 20 ns boundary)
*     so eval always sees settled inputs.
*   - Cload: Cload Out 0 5f  (one X1 fanout-ish; keep uniform across the library).
*
* GLITCH / SIZING GATE (paper p.278): peak excursion on out_b during the
* contention window must stay < 0.10*VDD = 0.5 V. Charge-share floor on dyn
* must stay > 3.5 V in the worst-case partial-eval vector.

* ---------------------------------------------------------------
* PDK setup   (pex_validate.py mk-tb swaps the cell .include for the PEX netlist)
* ---------------------------------------------------------------
.include /soe/czeng14/software/pdk/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /soe/czeng14/software/pdk/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical
.include /mada/users/czeng14/projects/brainstorm/domino/lsdl_lib/cells/lsdl_basic/{{CELL}}.spice

* ---------------------------------------------------------------
* Supply + clock
* ---------------------------------------------------------------
Vvdd  VPWR 0 5
Vgnd  VGND 0 0
Vclk  Clk  0  PULSE(0 5 5n 100p 100p 9.9n 20n)

* ---------------------------------------------------------------
* Input stimulus — one PWL per input. Cycle vectors MUST include:
*   (a) all-off  (dyn stays high, Out at precharge value),
*   (b) full-eval (every series input =1 / the OR minterm) -> dyn discharges,
*   (c) WORST-CASE CHARGE-SHARE vector (partial eval: top of a series stack on,
*       a lower device off, after the internal stack node was driven low) ,
*   (d) recovery full-eval.
* Transitions at <boundary>.1n (mid-precharge).
* ---------------------------------------------------------------
{{INPUT_PWLS}}

* ---------------------------------------------------------------
* DUT
* ---------------------------------------------------------------
X{{INST}} {{PIN_ORDER}} {{CELL}}
Cload Out 0 5f

* ---------------------------------------------------------------
* Init dynamic nodes (charge-share stress): dyn precharged high, series stack
* internal node(s) pre-driven low.
* ---------------------------------------------------------------
.ic v(X{{INST}}.dyn)=5
{{IC_INTERNAL_NODES}}
.tran 50p 110n uic

* ---------------------------------------------------------------
* Measurements (names consumed by pvt_sweep.py PASS_CRITERIA)
* ---------------------------------------------------------------
* eval delay (Clk eval edge -> Out toggles). RISE/FALL index per cell polarity.
.meas tran {{TPD_MEAS}}

* dyn full-discharge floor in the full-eval cycle.
.meas tran v_dyn_low_min     MIN v(X{{INST}}.dyn) FROM={{EVAL_FROM}} TO={{EVAL_TO}}
* charge-share floor: dyn MIN in the worst partial-eval cycle (must stay > 3.5 V).
.meas tran v_dyn_share_min   MIN v(X{{INST}}.dyn) FROM={{SHARE_FROM}} TO={{SHARE_TO}}
* glitch gate: out_b peak excursion during contention (must stay < 0.5 V from rail).
.meas tran v_out_b_glitch    {{GLITCH_MEAS}}
* functional latch check: Out settled value at end of the recovery cycle.
.meas tran v_out_final       AVG v(Out) FROM={{FINAL_FROM}} TO={{FINAL_TO}}

.print tran v(Clk) {{PRINT_INPUTS}} v(X{{INST}}.dyn) v(X{{INST}}.out_b) v(Out)
.end

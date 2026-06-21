# testbench/

ngspice testbench decks for Wave 0 cells. Run via the container wrapper.

| Deck | Validates | Key measurements |
|---|---|---|
| `tb_lsdl_inv_x1.sp` | Single-NMOS evaluation, basic Fig. 1 latching | `tpd_eval_lh`, `v_out_b_glitch_max`, `v_dyn_low_min` |
| `tb_lsdl_nand2_x1.sp` | 2-NMOS stack, charge sharing on `nint` | `tpd_eval_hl`, `v_dyn_charge_share_min`, `v_out_b_glitch_max` |

## Run

From the project root:

```bash
./lsdl_lib/scripts/run_in_container.sh \
  ngspice -b testbench/tb_lsdl_inv_x1.sp
```

The wrapper mounts `lsdl_lib/` at `/mada/users/czeng14/projects/brainstorm/domino/lsdl_lib` and the GF180MCU PDK at `/soe/czeng14/software/pdk`
inside the IIC-OSIC-TOOLS container. Testbenches reference both paths
with absolute names so they work from any host location.

## Paper sizing rule gate (p. 278)

The cell **fails Wave 0** if `v_out_b_glitch_max > 0.10 * VDD = 0.5 V` in
any corner. The testbench measurement `v_out_b_glitch_max` is the
direct check. If it's above threshold:

1. Increase `XPDRVN` width (faster discharge of `out_b` when dyn pulls
   down) — primary lever.
2. Verify Header device sized to not bottleneck Predriver n.
3. Check that Cut feedback width isn't so small that it adds delay to
   the latch recovery.

## Charge-sharing check (NAND2 specifically)

`v_dyn_charge_share_min` measured during cycle 3 (A1=1, A2=0) tells you
how far dyn dropped from VPWR purely due to charge redistribution with
the previously-low `nint`. If dyn drops below the Predriver-p threshold
(~ VPWR - |Vtp|), Out glitches incorrectly. Mitigation:

1. Reduce `nint` parasitic capacitance via layout — keep top NMOS
   drain area small.
2. Reduce evaluate-window length (faster Clk falling edge after the
   eval; bounded by Liberty `min_pulse_width_high`).
3. For wider stacks, paper recommends pre-discharging internal nodes
   via a "trickle" — but at 180 nm we're betting on layout-only
   mitigation per the no-keeper/no-minder decision.

# clkgen/

On-die two-phase clock generator producing `C1` and `C2`.

- **Topology:** external clock pad → buffer → divide-by-2 → produces
  50% duty C1 and C1_bar. Each fed through a programmable delay-chain
  inserting falling-edge skew, yielding C1 and C2 with a programmable
  non-overlap gap at both rising and falling edges.
- **Programmability:** 5-bit non-overlap register from pads. Step ~10 ps
  at TT 5V 25°C; range 10–320 ps.
- **Implementation:** static CMOS using `gf180mcu_fd_sc_mcu9t5v0`.
  Not LSDL — keeps test infrastructure independent of the cell library
  under test.

Files (to be created in Wave 0):

- `two_phase_gen.v` — RTL for the generator (counter, delay-chain
  control logic).
- `two_phase_gen.sdc` — SDC constraints declaring the C1 and C2 output
  clocks for downstream LibreLane synthesis.

Wave 0 deliverable. No code yet.

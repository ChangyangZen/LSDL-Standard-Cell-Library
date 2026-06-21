/* lsdl_inv_x1 — OUT = !A
 * GF180MCU 5V LSDL, X1 drive strength.
 * Positive-edge sequential: samples inputs on CLK rising.
 * Blackbox: timing from lsdl_fd_sc_9t5v0__tt_5v_25c.lib. */
`timescale 1ns/1ps
module lsdl_inv_x1 (CLK, A, OUT, VPWR, VGND);
  input  CLK;
  input  A;
  output OUT;
  inout  VPWR;
  inout  VGND;
endmodule

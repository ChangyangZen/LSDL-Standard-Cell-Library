/* lsdl_nor4_x1 — OUT = !(A1 | A2 | A3 | A4)
 * GF180MCU 5V LSDL, X1 drive strength.
 * Positive-edge sequential: samples inputs on CLK rising.
 * Blackbox: timing from lsdl_fd_sc_9t5v0__tt_5v_25c.lib. */
`timescale 1ns/1ps
module lsdl_nor4_x1 (CLK, A1, A2, A3, A4, OUT, VPWR, VGND);
  input  CLK;
  input  A1;
  input  A2;
  input  A3;
  input  A4;
  output OUT;
  inout  VPWR;
  inout  VGND;
endmodule

// smoke.v — minimal STA smoke design for LSDL Liberty validation.
// One LSDL inverter on the C1 clock domain. Inputs/outputs are
// top-level ports so OpenSTA has external clocks/inputs to drive.

module smoke (
    input  c1,        // C1 clock — bound to lsdl_inv_x1 Clk
    input  data_in,   // primary input -> A
    output data_out   // primary output <- Out
);

    lsdl_inv_x1 u_inv (
        .A   (data_in),
        .CLK (c1),
        .OUT (data_out)
    );

endmodule

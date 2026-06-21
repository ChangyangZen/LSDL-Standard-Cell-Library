* lsdl_nand_cmplx_x1 for LibreCell — Fig.3a NAND-form complex output, two trees.
* Out = !(A+B). n* => NMOS else PMOS. l= matches tech (NMOS 0.6u / PMOS 0.5u).

.subckt lsdl_nand_cmplx_x1 A B Clk Out VPWR VGND
* tree 1 (gate A)
MPRE1  dyn1       Clk   VPWR       VPWR  pmos w=1.0u l=0.5u
MN1    dyn1       A     foot1      VGND  nmos w=0.8u l=0.6u
MFOOT1 foot1      Clk   VGND       VGND  nmos w=0.8u l=0.6u
* tree 2 (gate B)
MPRE2  dyn2       Clk   VPWR       VPWR  pmos w=1.0u l=0.5u
MN2    dyn2       B     foot2      VGND  nmos w=0.8u l=0.6u
MFOOT2 foot2      Clk   VGND       VGND  nmos w=0.8u l=0.6u
* NAND-form predriver: out_b = !(dyn1 & dyn2)
MPDRVP1 out_b     dyn1  VPWR       VPWR  pmos w=3.0u l=0.5u
MPDRVP2 out_b     dyn2  VPWR       VPWR  pmos w=3.0u l=0.5u
MPDRVN1 out_b     dyn1  midn       VGND  nmos w=0.4u l=0.6u
MPDRVN2 midn      dyn2  hdr_src    VGND  nmos w=0.4u l=0.6u
MHDR   hdr_src    Clk   VGND       VGND  nmos w=0.8u l=0.6u
* feedback + cut
MFBP   cut_fb_src Out   VPWR       VPWR  pmos w=0.5u l=0.5u
MCUTFB out_b      Clk   cut_fb_src VPWR  pmos w=0.5u l=0.5u
MFBN   out_b      Out   VGND       VGND  nmos w=0.5u l=0.6u
* output driver
MODRVP Out        out_b VPWR       VPWR  pmos w=1.5u l=0.5u
MODRVN Out        out_b VGND       VGND  nmos w=0.9u l=0.6u
.ends lsdl_nand_cmplx_x1

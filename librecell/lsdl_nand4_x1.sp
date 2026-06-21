* lsdl_nand4_x1 for LibreCell (lclayout) — primitive 4-terminal MOSFETs.
* Out = !(A1&A2&A3&A4). 4-series: dyn->A1->nint1->A2->nint2->A3->nint3->A4->foot.
* Model n* => NMOS, else PMOS. l= matches tech (NMOS 0.6u / PMOS 0.5u).

.subckt lsdl_nand4_x1 A1 A2 A3 A4 Clk Out VPWR VGND
MPRE   dyn        Clk   VPWR       VPWR  pmos w=1.0u l=0.5u
MNA    dyn        A1    nint1      VGND  nmos w=1.2u l=0.6u
MNB    nint1      A2    nint2      VGND  nmos w=1.2u l=0.6u
MNC    nint2      A3    nint3      VGND  nmos w=1.2u l=0.6u
MND    nint3      A4    foot_top   VGND  nmos w=1.2u l=0.6u
MFOOT  foot_top   Clk   VGND       VGND  nmos w=1.2u l=0.6u
MPDRVP out_b      dyn   VPWR       VPWR  pmos w=3.0u l=0.5u
MHDR   hdr_src    Clk   VGND       VGND  nmos w=0.8u l=0.6u
MPDRVN out_b      dyn   hdr_src    VGND  nmos w=0.4u l=0.6u
MFBP   cut_fb_src Out   VPWR       VPWR  pmos w=0.5u l=0.5u
MCUTFB out_b      Clk   cut_fb_src VPWR  pmos w=0.5u l=0.5u
MFBN   out_b      Out   VGND       VGND  nmos w=0.5u l=0.6u
MODRVP Out        out_b VPWR       VPWR  pmos w=1.5u l=0.5u
MODRVN Out        out_b VGND       VGND  nmos w=0.9u l=0.6u
.ends lsdl_nand4_x1

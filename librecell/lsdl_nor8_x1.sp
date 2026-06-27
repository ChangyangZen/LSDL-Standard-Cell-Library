* lsdl_nor8_x1 for LibreCell (lclayout). Out = !(A1+A2+A3+A4+A5+A6+A7+A8).
* 8 parallel NMOS dyn->foot_top (OR_TREE_8 showcase: one dynamic gate, no PMOS stack).
* Extends the proven lsdl_nor4_x1; MPRE/MFOOT upsized for the wider dynamic node.
* Model n* => NMOS, else PMOS. l= matches tech (NMOS 0.6u / PMOS 0.5u).

.subckt lsdl_nor8_x1 A1 A2 A3 A4 A5 A6 A7 A8 Clk Out VPWR VGND
MPRE   dyn        Clk   VPWR       VPWR  pmos w=1.0u l=0.5u
MNA    dyn        A1    foot_top   VGND  nmos w=0.8u l=0.6u
MNB    dyn        A2    foot_top   VGND  nmos w=0.8u l=0.6u
MNC    dyn        A3    foot_top   VGND  nmos w=0.8u l=0.6u
MND    dyn        A4    foot_top   VGND  nmos w=0.8u l=0.6u
MNE    dyn        A5    foot_top   VGND  nmos w=0.8u l=0.6u
MNF    dyn        A6    foot_top   VGND  nmos w=0.8u l=0.6u
MNG    dyn        A7    foot_top   VGND  nmos w=0.8u l=0.6u
MNH    dyn        A8    foot_top   VGND  nmos w=0.8u l=0.6u
MFOOT  foot_top   Clk   VGND       VGND  nmos w=0.8u l=0.6u
MPDRVP out_b      dyn   VPWR       VPWR  pmos w=3.0u l=0.5u
MHDR   hdr_src    Clk   VGND       VGND  nmos w=0.8u l=0.6u
MPDRVN out_b      dyn   hdr_src    VGND  nmos w=0.4u l=0.6u
MFBP   cut_fb_src Out   VPWR       VPWR  pmos w=0.5u l=0.5u
MCUTFB out_b      Clk   cut_fb_src VPWR  pmos w=0.5u l=0.5u
MFBN   out_b      Out   VGND       VGND  nmos w=0.5u l=0.6u
MODRVP Out        out_b VPWR       VPWR  pmos w=1.5u l=0.5u
MODRVN Out        out_b VGND       VGND  nmos w=0.9u l=0.6u
.ends lsdl_nor8_x1

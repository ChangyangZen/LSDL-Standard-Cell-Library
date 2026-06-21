* lsdl_aoi22_x1 for LibreCell. Out = !((A1 & A2) + (B1 & B2)). n* => NMOS else PMOS.

.subckt lsdl_aoi22_x1 A1 A2 B1 B2 Clk Out VPWR VGND
MPRE   dyn        Clk   VPWR       VPWR  pmos w=1.0u l=0.5u
MNA    dyn        A1    nintA      VGND  nmos w=0.8u l=0.6u
MNB    nintA      A2    foot_top   VGND  nmos w=0.8u l=0.6u
MNC    dyn        B1    nintB      VGND  nmos w=0.8u l=0.6u
MND    nintB      B2    foot_top   VGND  nmos w=0.8u l=0.6u
MFOOT  foot_top   Clk   VGND       VGND  nmos w=0.8u l=0.6u
MPDRVP out_b      dyn   VPWR       VPWR  pmos w=3.0u l=0.5u
MHDR   hdr_src    Clk   VGND       VGND  nmos w=0.8u l=0.6u
MPDRVN out_b      dyn   hdr_src    VGND  nmos w=0.4u l=0.6u
MFBP   cut_fb_src Out   VPWR       VPWR  pmos w=0.5u l=0.5u
MCUTFB out_b      Clk   cut_fb_src VPWR  pmos w=0.5u l=0.5u
MFBN   out_b      Out   VGND       VGND  nmos w=0.5u l=0.6u
MODRVP Out        out_b VPWR       VPWR  pmos w=1.5u l=0.5u
MODRVN Out        out_b VGND       VGND  nmos w=0.9u l=0.6u
.ends lsdl_aoi22_x1

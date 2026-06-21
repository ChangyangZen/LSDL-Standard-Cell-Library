* lsdl_nand2_x1 for LibreCell (lclayout) — primitive 4-terminal MOSFETs.
* Derived from cells/lsdl_basic/lsdl_nand2_x1.spice (Belluomini Fig.1 LSDL NAND2).
* Out = !(A1 & A2). Series-NMOS eval tree: dyn -> XNA -> nint -> XNB -> foot_top.
* Device line: M<name> D G S B model w l.  Model name n* => NMOS, else PMOS.
* l= matches the tech-drawn gate length (NMOS 0.6u / PMOS 0.5u) for LVS.

.subckt lsdl_nand2_x1 A1 A2 Clk Out VPWR VGND
* --- Precharge + 2-series-NMOS eval tree + foot ---
MPRE   dyn        Clk   VPWR       VPWR  pmos w=1.0u l=0.5u
MNA    dyn        A1    nint       VGND  nmos w=0.8u l=0.6u
MNB    nint       A2    foot_top   VGND  nmos w=0.8u l=0.6u
MFOOT  foot_top   Clk   VGND       VGND  nmos w=0.8u l=0.6u
* --- Predriver pair (dyn -> out_b) ---
MPDRVP out_b      dyn   VPWR       VPWR  pmos w=3.0u l=0.5u
MHDR   hdr_src    Clk   VGND       VGND  nmos w=0.8u l=0.6u
MPDRVN out_b      dyn   hdr_src    VGND  nmos w=0.4u l=0.6u
* --- Feedback keeper + cut feedback ---
MFBP   cut_fb_src Out   VPWR       VPWR  pmos w=0.5u l=0.5u
MCUTFB out_b      Clk   cut_fb_src VPWR  pmos w=0.5u l=0.5u
MFBN   out_b      Out   VGND       VGND  nmos w=0.5u l=0.6u
* --- Output driver pair (out_b -> Out) ---
MODRVP Out        out_b VPWR       VPWR  pmos w=1.5u l=0.5u
MODRVN Out        out_b VGND       VGND  nmos w=0.9u l=0.6u
.ends lsdl_nand2_x1

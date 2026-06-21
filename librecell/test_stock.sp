* Stock cells for LibreCell GF180MCU enablement validation (L2).
* 4-terminal MOSFETs: M<n> D G S B model w l. Model name n* => NMOS, else PMOS.

.subckt INVX1 A Y VDD VSS
M0 Y A VDD VDD pmos w=1.0u l=0.5u
M1 Y A VSS VSS nmos w=0.8u l=0.6u
.ends INVX1

.subckt NAND2X1 A B Y VDD VSS
M0 Y A VDD VDD pmos w=1.0u l=0.5u
M1 Y B VDD VDD pmos w=1.0u l=0.5u
M2 Y A n1  VSS nmos w=0.8u l=0.6u
M3 n1 B VSS VSS nmos w=0.8u l=0.6u
.ends NAND2X1

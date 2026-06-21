# FREEZE: lsdl_wave1_basic_9cells_phys_signoff_v0
date: 2026-05-29T00:37Z
scope: Wave 1 physical sign-off baseline — 9 BASIC LSDL cells + 11T support lib.
all cells: 0 cell-level DRC, block Netgen LVS 'Circuits match uniquely', pin-access PASS, LEF audit PASS.
flow: signoff_cell.sh (lclayout TRACKS=11 --placer smt -> markers -> port-clean -> met2 snap -> LEF).

## SHA256 of frozen deliverables (GDS + LEF per cell)
01f9760333154a501ba2e284bd7c41403b46c222e85fc80c28bcdeec90401250  signoff_lsdl_inv_x1/lsdl_inv_x1.gds
f3339b634199f111eb70800da82c86b0747d724dd99c6d10a3febbd536e71c88  signoff_lsdl_inv_x1/lsdl_inv_x1.lef
790642f17ff758a03c0e85c6a9f5eea050bb431b9a69798b6d62e544dfa2db3f  signoff_lsdl_nand2_x1/lsdl_nand2_x1.gds
98c08b891928abc3ab559d2afcbb6606ba9a54d7560f485fe1351973145e862d  signoff_lsdl_nand2_x1/lsdl_nand2_x1.lef
a2980cafd2023427ca30e50d2a21fd074544188c21bd4120b8212ce08315a206  signoff_lsdl_nand3_x1/lsdl_nand3_x1.gds
da4922742b8fcc0310ef7baa03beb53ac9d9cce664c855cf8f387b26a8e0cbe8  signoff_lsdl_nand3_x1/lsdl_nand3_x1.lef
69704ff0523e75b27d79cdd6f9d9475dd9cbd9393c60a2f611225da3a2f3e58c  signoff_lsdl_nand4_x1/lsdl_nand4_x1.gds
3e14861b1147d778ea92224996864061ad8ebcd06c10f346c277d9d1cad11582  signoff_lsdl_nand4_x1/lsdl_nand4_x1.lef
9fc865aa6d804760fff8b5daca721d70bf5c666c310f77381590cc058d46b0fd  signoff_lsdl_nor2_x1/lsdl_nor2_x1.gds
7988f925863cc2ba4c1f6ecaa5c5341a2adc3d42ea05bc5ff8f11f6fba169675  signoff_lsdl_nor2_x1/lsdl_nor2_x1.lef
8fbd3c6404cd4a7b3171cb0b77a5db649d7deb0ba7e5442c1624a3a3b34c9d99  signoff_lsdl_nor3_x1/lsdl_nor3_x1.gds
7fe7267879a42c0b1272c71f09a452ee834ce94585b24ce2495702ad95bbab8a  signoff_lsdl_nor3_x1/lsdl_nor3_x1.lef
ee00616c806ce9d90ac089cb22bbc00ba83706a73f6134f3791f82a8ea00ddc9  signoff_lsdl_nor4_x1/lsdl_nor4_x1.gds
1f8fbc5b85c6eeef63ff50b46df4f5a766a732fd8c0c6f3fab046b9741fc8cc6  signoff_lsdl_nor4_x1/lsdl_nor4_x1.lef
521298a828aae97fdc04fee45df2899f5023ad515dd8a919046b33b04abca21f  signoff_lsdl_aoi21_x1/lsdl_aoi21_x1.gds
f4ad849173e07f13700503189e2195971bc9b7d5b97cda371193dc3a663db18f  signoff_lsdl_aoi21_x1/lsdl_aoi21_x1.lef
9e51ad912879e8b7a8b7581cbfc45d22fba61bc289c654f6f39bf9f7f7d32a0f  signoff_lsdl_aoi22_x1/lsdl_aoi22_x1.gds
cd5fe9bdd4a3331090016268f25cd52c6a1139593b849df68433d56df9bf1c7a  signoff_lsdl_aoi22_x1/lsdl_aoi22_x1.lef

## support cells (11T tap/endcap/fill)
03cbc547378fc312c7365dea0ec8b69665d89f1da7e64cb5319e6cb1bcddc69a  signoff_support_11t/lsdl_endcap_11t.gds
bac9049840fea5aa1a994a37bef6e2248c343113fb23bfe68c08ae1d7e1951c8  signoff_support_11t/lsdl_fill_11t_1.gds
402e25367997970a65cefe2332ea18262c410fd60f353b7c00d74c558127ca07  signoff_support_11t/lsdl_fill_11t_2.gds
83b3994ff26c15e46bbd63a0a743ef457ee4deda244c9e458d8307c584a774f0  signoff_support_11t/lsdl_fill_11t_4.gds
cae5a165209a02d98805d0fe1a4b7a6a01f731b7f9c268eb3d0237e1aafaa8b8  signoff_support_11t/lsdl_tap_11t.gds

## status
signed off (9): inv, nand2, nand3, nand4, nor2, nor3, nor4, aoi21, aoi22
optional/blocked (2): nand_cmplx_x1, nand_cmplx_aoi (router met1 shorts; = nor2/aoi22 functionally; see COMPLEX_CELLS_OPTIONAL.md)
deferred: MUX2 (not yet attempted)

## NOT to change after this tag without re-freezing:
  signoff_*/*.gds, signoff_*/*.lef, signoff_support_11t/*.gds, the patched lclayout + tech_gf180mcu/.
## L5 (Liberty) and beyond build NEW collateral; they must not alter the frozen GDS/LEF pin geometry.

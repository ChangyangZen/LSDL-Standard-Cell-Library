# Complex (Fig 3a) cells — OPTIONAL / deferred

lsdl_nand_cmplx_x1 and lsdl_nand_cmplx_aoi could NOT be routed LVS-clean by lclayout
(router merges nets on met1 in the dense 16-FET/two-dyn topology; full debug in
signoff_lsdl_nand_cmplx_x1/DEBUG_REPORT.md). They are FUNCTIONALLY REDUNDANT and
mapped to already-signed-off basic cells for the tapeout:

  lsdl_nand_cmplx_x1   = !(A + B)            -> use  lsdl_nor2_x1   (clean)
  lsdl_nand_cmplx_aoi  = !((A1·A2)+(B1·B2))  -> use  lsdl_aoi22_x1  (clean)

The complex two-tree form is the paper's timing optimization, not a required Boolean
function. Revisit only if the timing advantage is needed: try a placement-file
constraint (separate dyn1/dyn2 trees; keep OUT off the CLK spine) or hand-Magic.

# FIBSEM_Maestro
## Time to FIBSEM_Maestro launch:
<table width="100%" cellspacing="0" cellpadding="0"><tbody><tr><td align="center"><img src="https://i.countdownmail.com/3mm90t.gif" style="display:inline-block!important;width:241px;" border="0" alt="countdownmail.com"/></td></tr></tbody></table> 

Software for (cryo/RT) volume-EM acquisition. It allows to acquire the big volume in constant high quality.  

Key features:
- Usage of deep learning model for segmentation of region of interest. The segmented region is used for:
  - Resolution calculation ([siFRC](https://github.com/prabhatkc/siFRC) or others)
  - Autofocusing, autostigmator, auto-lens alignment (multiple criterions and sweeping strategies)
  - Drift correction & FoV optimization (template matching, or segmented region centering)
  - Auto contrast-brightness (whole image or segmented region)
- Email attention
- Works with ThermoFisher Autoscript. Support of [OpenFIBSEM](https://github.com/DeMarcoLab/fibsem) for other vendors (Tescan, Zeiss) is planned.

Drift correction with segmentation aid
https://github.com/user-attachments/assets/eb7f36c1-24ef-4932-92d0-4ce785f9060b

FoV optimization with segmentation aid
https://github.com/user-attachments/assets/b467a4c0-bd52-49a2-8e75-68fe4fdc699f

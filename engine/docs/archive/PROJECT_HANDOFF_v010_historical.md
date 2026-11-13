# VEVOR Smart 3 — Project Technical Handoff

**Updated:** 2026-11-12  
**Status:** v0.10 code distributed; large-job USB transmission not yet physically verified.

## Purpose and status

Project handoff record for the VEVOR Smart 3 direct-USB SVG cutting workflow. Updated 2026-11-12. The current distributed cutter is v0.10; its removal of the total-job byte cap has not yet been physically verified. This document separates observed behavior from assumptions and pending tests.

## Hardware and Windows interface

Device: RENESAS SMART-3, USB VID 045B / PID 5310; instance USB\VID_045B&PID_5310\COMMUNICATIONS_DEVICES. USB printer-class interface (07/01/02), Windows usbprint driver, no Windows printer queue required. Interface GUID {28D78FAD-5A12-11D1-AE5B-0000F803A8C2}; Bulk OUT endpoint observed as 0x02 in earlier captures. Python opens the USB printer interface directly and sends HPGL-like commands.

## Confirmed calibration and manual setup

Settings: x_scale=0.74772, y_scale=3.63376, x_offset=0.0, y_offset=0.0. A 10 mm test square cut approximately 9.89 × 9.85 mm using this calibration. Load mat; manually move to displayed Y≈−115; press physical Origin (display resets to 0,0); then run job. The physical Origin operation is needed after a fresh mat load. Preserve-origin mode omits IN; in transmitted job.

## Mat, cutting, and safety

Nominal mat: 12 × 12 inches = 304.8 × 304.8 mm. The usable marked cutting region may be smaller. v0.9 changed live safety checks to evaluate physical SVG geometry against configurable mat_width_mm and mat_height_mm (defaults 304.8). Keep command-space sanity checks. A 50 mm corrected-coordinate cap in earlier releases was an artificial development guard, not a device limit. v0.10 removes a separate artificial 20,000-byte total HPGL job cap; one USB WriteFile still sends the payload, so successful transport is not proof of complete cutter execution.

## Cutting settings and commands

Current masking tape starting settings: cut_force=200 and cut_speed=100; CLI overrides --force and --speed. These are device command values, not verified grams or mm/s. Typical job prefix: SP1;FS200;VS100;. Standard ending: PU0,0;SP2;PU0,0;PG; (intended mat ejection). Minimal ending PU; keeps mat loaded. Blade depth is mechanical; test cut before production. Do not assume preview stroke width changes knife cut width.

## Operational commands

PowerShell directory: D:\3D\Vevor Python. Dry run: py smart3_cut.py mask_grid.svg --dry-run. Live: py smart3_cut.py mask_grid.svg --force 200 --speed 100 --cut --confirm-live-test I_ACCEPT_MOVEMENT. Always load mat, manually set Y≈−115 and press Origin before live job. Inspect generated .hpgl and reported physical bounds; attend the machine during experimental USB cutting.

## Blender mesh exporter

Only object named mask is exported; ignores selection/other objects. Scene metric unit scale 0.001 (1 Blender unit interpreted as 1 mm). Flattens mesh vertices to world Z=0; uses mesh edges only. Degree≠2 vertices split chains; degree-2 loops become closed paths. Validates each unique mesh edge is exported exactly once. Open paths are SVG polyline; closed paths polygon. Physical width/height are explicit mm; viewBox uses 72 units/inch (not 96) for historical ExactCut compatibility. SVG Y is flipped relative to Blender Y. The later exporter supports a 1 mm margin and optional border cutting contour; confirm desired mode before cutting.

## SVG grid generator and preview

Standalone svg_grid.py repeats cutting paths in X/Y with --repeat-x and --repeat-y and optional --gap-x/--gap-y (mm). Example: py svg_grid.py mask.svg --repeat-x 3 --repeat-y 2 --gap-x 2 --gap-y 2 --output mask_grid.svg. Fixed generator supplies thin preview stroke (0.02 mm), rounded caps/joins, and 1 mm outer margin. These are visual properties; actual centerline geometry should remain unchanged. Cutter v0.8-era parser does not support arbitrary SVG transform attributes, so grid output must bake translation into coordinates. Avoid assuming all SVG features are supported.

## Example grid diagnostics

A reported mask_grid.svg had 12 paths, physical SVG bounds X 1.000..29.064 mm and Y 1.000..19.218 mm; corrected bounds X 0.748..21.732 and Y 3.634..69.833. The earlier 50 mm corrected-Y check and later 20,000-byte job cap blocked transmission before USB; neither indicated the grid exceeded the physical mat. Exact grid geometry can change between regenerations.

## Experiments and cautions

ExactCut capture examples included setmat:1;JS12192,12192;, IN;, SP1;FS260;VS150;, PU40,40;, and PU0,0;SP2;PU0,0;PG;. Tool/ARMS offsets TB28 and TB29 were acknowledged but did not visibly solve the 32 mm top inset. A diagnostic USB command PU;PR;PU0,-80;PA;PU; unexpectedly fed mat outward ~50–60 mm while display stayed (0,0). Do not extrapolate standard HPGL motion units from that test or repeat uncontrolled motion tests. A USB write result is not a firmware-execution acknowledgement.

## Version and artifact inventory

v0.7: preserve_origin and minimal finish. v0.8: configurable force/speed and standard finish. v0.9: nominal 304.8 mm mat safety checks. v0.10: removes artificial 20,000-byte total-job cap; one USB write remains. Related archives: smart3_cut_v10_no_job_cap.zip; smart3_geometry_pipeline.zip; svg_grid_fixed_with_dependency.zip; svg_grid_fixed.py. Preserve exact working scripts, settings, example SVG, HPGL output and capture files with the project.

## Open items and next validation

(1) Physically test v0.10 with the new mask_grid.svg; verify the entire job cuts and mat ejects. (2) Determine true USB job-size and buffering behavior; chunking/flow control may be necessary. (3) Confirm physical usable mat dimensions and top-left margin after manual origin. (4) Inspect actual corners on tape; preview styling cannot repair mesh topology or drag-knife offset. (5) Consider test-cut presets by masking-tape type and blade depth. (6) Keep rollback copies of last physically verified cutter version.

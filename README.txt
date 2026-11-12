VEVOR SMART 3 CUTTER — v0.15 experimental geometry compensation
=============================================================

MAIN PROJECT README (maintained from previous releases).

FILES
  smart3_cut.py             SVG-to-HPGL and guarded Windows USB sender
  loop_closure.py           Straight-run seam selection and symmetric multi-segment overlap
  blade_offset.py           EXPERIMENTAL drag-knife holder trajectory model
  settings.txt              Provisional axis calibration, force/speed and mat settings
  smart3_calibrate.py       Axis calibration regression tool
  smart3_usb_probe.py       USBPRINT open-only probe
  blender_mask_to_svg.py   Blender outline exporter
  svg_grid.py               SVG grid generator
  calibration_loops.svg     5, 7.5, 10, 15 mm loop sheet
  calibration_corners.svg   Mirrored corner-angle test sheet
  *_legacy.svg             Previous small-feature test patterns
  test_*.py                Offline automated geometry and CLI tests
  BLADE_GEOMETRY_README.txt Current v0.15 usage, limitations and safety
  CLOSURE_MODES_README.txt v0.13 historical notes (first-edge overlap is superseded)
  CALIBRATION_*.txt, LOOP_CLOSURE_README.txt historical calibration notes

CURRENT CALIBRATION (provisional)
  x_scale = 0.74906512; y_scale = 3.59950979
  x_offset = 0.0; y_offset = 0.0
  Force 200, speed 100 are device command values; not verified physical units.

QUICK START (PowerShell in project directory)
  py -m unittest discover -v
  py smart3_cut.py calibration_loops.svg --dry-run --loop-start auto-straight --loop-overlap-mm 1.0 --output loops_10.hpgl
  py smart3_cut.py calibration_corners.svg --dry-run --blade-offset-mm 0.2 --output corners_offset_02.hpgl

Do not run an offset-compensated physical cut without inspecting the generated
HPGL and understanding that blade-holder pivots can cut outside the nominal SVG.
Blade offset is an unknown mechanical parameter: 0.2 mm above is an example,
NOT a measured or recommended calibrated value.

For guarded physical cutting, the existing --cut --confirm-live-test I_ACCEPT_MOVEMENT
mechanism remains. Secure material, load mat, set displayed Y near -115 and press
physical Origin, inspect bounds and supervise cutter. A successful USB WriteFile
does NOT establish device execution. No USB handshake or buffer-size proof exists.

SAFETY / LIMITATIONS
  Default blade offset 0.0 (disabled); default overlap 0.0 (disabled).
  Closed contours use symmetric overlap: total N mm is split N/2 before and N/2 after the nominal seam, following the original contour across corners and curves. The physical blade-down start shifts backward; the nominal seam stays fixed. Overlap must be less than the perimeter.
  Requested overlap is limited by CLI to 5 mm. It is applied before offset.
  --blade-offset-mm 0..2 mm (experimental); --blade-arc-step-deg 1..45.
  At corners the holder pivots about the theoretical blade-tip vertex.
  These holder motions are not strictly on the nominal SVG path and can
  produce unwanted blade marks, especially at the first engagement.
  Keep-inside / keep-outside remain intent metadata only: NO off-contour
  lead-ins or region/collision planning are implemented.
  --lead-in-mm > 0 is rejected. No physical v0.15 cuts have been validated.
  Physical mat bounds 304.8 x 304.8 mm, warn at >=90% of either axis.
  The check uses planned holder-path samples, not the actual blade-tip track.
  SVG transforms unsupported; flatten first. For SVG <path> install svgpathtools.

V0.15 RECOMMENDED OFFLINE TEST:
  py smart3_cut.py calibration_loops.svg --dry-run --loop-start auto-straight --loop-overlap-mm 2.0 --blade-offset-mm 0 --output loops_symmetric_20.hpgl
  py -m unittest discover -v

WARNING: v0.15 changes the meaning of --loop-overlap-mm from forward-only to symmetric TOTAL overlap. Review any existing commands before cutting.


v0.16 calibration addition: calibration_mirrored_l_gaps.svg, MIRRORED_L_GAP_TEST_README.txt, mirrored_l_geometry.csv, and test_mirrored_l_gaps.py. Six mirrored-L open-path approach tests (0/2 mm gaps; X/Y/45-degree diagonal). Cutting algorithm remains v0.15.


v0.17 compact horizontal travel-direction calibration: calibration_horizontal_travel_direction.svg, HORIZONTAL_TRAVEL_TEST_README.txt, horizontal_travel_geometry.csv and test_horizontal_travel.py. Four mirrored-L pairs (+X/-X x 0/2 mm gap), 115x100 mm canvas. Cutting logic unchanged. Future blade-tip tracking/overshoot idea documented but NOT implemented.

v0.18 OFFLINE BLADE-TIP ALGORITHM PROTOTYPE
==========================================
See BLADE_TIP_V018_README.txt. New: blade_tip_model.py,
smart3_blade_tip_preview.py, test_blade_tip_model.py. The existing
smart3_cut.py live-cutting path and v0.17 behavior are UNCHANGED.
This prototype does NOT generate HPGL or send USB data.

v0.19 EXPERIMENTAL COMPACT TEST (offline generator; existing cutter unchanged)
--------------------------------------------------------------------------
See V019_EXPERIMENTAL_README.txt. Run py smart3_v019_compact.py to generate
baseline and experimental SVGs. Compare on scrap vinyl, dry-run first.
This is a bounded empirical inverse-path prototype, NOT calibrated compensation.

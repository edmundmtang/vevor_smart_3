VEVOR SMART 3 CUTTER — v0.13 experimental closure modes
====================================================

MAIN PROJECT README (restored from v0.10 and updated).

FILES
  smart3_cut.py           SVG-to-HPGL generator and guarded Windows USB cutting
  loop_closure.py         Straight-run seam relocation and same-path overlap
  settings.txt            Current X/Y calibration and cutting settings
  smart3_calibrate.py     Long-line regression calibration tool
  smart3_usb_probe.py     USBPRINT enumeration/open test
  blender_mask_to_svg.py Blender edge exporter
  svg_grid.py             SVG grid generator
  calibration_loops.svg   Standard 5, 7.5, 10, 15 mm closure sheet
  calibration_corners.svg 12 corner paths (original v0.12 sheet)
  *_legacy.svg           Earlier small-size diagnostic sheets
  test_*.py              Automated offline tests
  CLOSURE_MODES_README.txt Detailed modes, safeguards, calibration procedure
  CALIBRATION_README.txt, CALIBRATION_SUITE_README.txt, LOOP_CLOSURE_README.txt
                         Historical documentation; consult closure modes README for current behavior

CURRENT CALIBRATION
  x_scale = 0.74906512; y_scale = 3.59950979 (provisional regression-based)
  x_offset = y_offset = 0.0. No correction for blade endpoint intercept.
  Force 200, speed 100 are device command values, not validated units.

QUICK START (PowerShell in this directory)
  py -m unittest discover -v
  py smart3_cut.py calibration_loops.svg --dry-run --loop-start auto-straight --loop-overlap-mm 0.4 --output loops_04.hpgl
  py smart3_cut.py calibration_loops.svg --loop-start auto-straight --loop-overlap-mm 0.4 --force 200 --speed 100 --cut --confirm-live-test I_ACCEPT_MOVEMENT

Before any live cut: secure material, load mat, manually set displayed Y around -115,
press physical Origin, verify placement, and supervise movement. Dry run first.
Live USB uses one Windows WriteFile, no execution acknowledgment, no confirmed device buffer size.
A completed USB write is NOT proof that the job executed or finished.

LIMITATIONS / SAFETY
  Default --cut-strategy no-waste. Modes keep-inside and keep-outside record
  material intent but DO NOT yet produce off-contour lead-ins. --lead-in-mm > 0
  is rejected, never silently ignored. Per-contour intent supported via JSON.
  Same-path overlap is limited to the first existing segment and skipped when
  too short. No blade-offset corner correction is implemented yet.
  The blade tip can still deviate physically from the commanded contour.
  Hard physical mat limit 304.8 mm; warning at 90% of configured mat axis.
  This checks commanded SVG geometry, not physical blade-tip excursions.
  Unsupported SVG transforms/elements fail closed; flatten paths first.
  SVG <path> requires: py -m pip install svgpathtools
  No physical testing of v0.13 has been performed.

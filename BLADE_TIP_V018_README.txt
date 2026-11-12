SMART 3 v0.18 — OFFLINE blade-tip algorithm prototype
======================================================

WHAT IS IMPLEMENTED
- Explicit straight lead-in to condition blade orientation. This is a physical
  blade-down cut, potentially outside the desired contour. Requires an opt-in
  flag even for preview. It does NOT prove the blade is oriented correctly.
- Finite-length corner transition surrogate (quadratic Bezier rounding).
  The corner region ends after the configured recovery length; beyond it the
  predicted path is EXACTLY straight. No exponential/asymptotic recovery.
- Independent constant signed normal displacement on straight runs.
- Exploratory straight-run inverse offset candidate (purple), NOT a complete
  corner inverse or a calibrated toolpath. It is not exported as cut HPGL.
- Offline SVG overlay: black dashed = intended SVG; blue = holder with
  conditioning lead; orange = predicted tip; purple dashed = inverse candidate.

CALIBRATION EVIDENCE / LIMITATIONS
- User force/speed grid: at force 175 gap 0.20 mm; recovery 1.39, 1.02,
  1.15 mm; at force 200 gap 0.18 mm; recovery 1.41, 1.41, 1.39 mm.
  Force 150 row did not cut. Force 200 speed 100 used as reference.
- Recovery ~1.40 mm is a useful reference, not a universal constant.
- The mirrored-L gap is a RELATIVE separation between two tracks. It does NOT
  identify either track's signed absolute displacement. Accordingly the
  default signed_bias_mm is ZERO. A user-supplied nonzero bias is a hypothetical
  sensitivity study, NOT a correction inferred from the measured 0.18 mm gap.
- Quadratic corner blend is a phenomenological stand-in, NOT a validated
  rigid drag-knife model. The model does not simulate physical blade pivot,
  friction, unknown initial angle, or path-history-dependent residual offsets.
- A real inverse corner compensator/overshoot optimizer is NOT implemented.
  No claim of physical cutting accuracy or improved closure is made.
- Short segments cap recovery windows to avoid overlapping transitions;
  this changes the effective recovery distance on tight geometry.
- Existing v0.14 blade_offset.py remains separate and experimental.

HOW TO RUN (PowerShell; requires Python, svgpathtools for SVG <path>)
  py -m unittest discover -v
  py smart3_blade_tip_preview.py calibration_loops.svg --conditioning-mm 0
  py smart3_blade_tip_preview.py calibration_loops.svg --allow-off-contour-conditioning
  py smart3_blade_tip_preview.py calibration_loops.svg --allow-off-contour-conditioning --signed-bias-mm 0.09

The 0.09 mm signed bias above is purely illustrative, not calibrated.
Preview output defaults to <input>_blade_tip_preview.svg. SVG uses physical mm.
The off-contour lead-in may cross other shapes or waste areas; NO collision,
material-preservation, or mat-bounds checks are performed by this preview.
The existing live cutter retains its original safety guards and forbids
nonzero --lead-in-mm. DO NOT feed the preview SVG back into smart3_cut.py as a
cutting design: it contains multiple diagnostic overlays and lead-in paths.

NEXT ALGORITHM STAGE
Develop a stateful model of orientation and history-dependent lateral bias,
then solve the inverse corner motion subject to material and mat constraints.
Use the existing measured recovery and gap values as calibration constraints;
do not request additional physical testing as a prerequisite.

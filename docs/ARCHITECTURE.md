# Architecture and model boundaries

## Data flow

`original SVG` → `smart3_cut.parse_svg` → optional `blade_tip_clean.compensate` → `smart3_cut.make_hpgl` → dry-run file or guarded Windows USBPRINT write.

In stateful mode, `blade_tip_clean.py` configures the forward predictor and bounded inverse solver in `blade_tip_stateful.py`. The inverse objective is the **original intended blade-tip contour**. The resulting points are **holder positions**, not a second SVG target to compensate again.

## The experimental model

The v0.30 configuration uses an assumed 0.20 mm blade offset, 1.39 mm orientation recovery and a signed Y-history amplitude of −0.300 mm. These values are hypotheses derived from limited physical comparisons. The turn-direction extra lateral bias, artificial apex-target extension, apex taper, intended-path-driven history and post-inverse outgoing shift are disabled in this mode. Older code and test generators remain in the repository for comparison; their existence does not mean they are active in the main cutter.

## Double-compensation hazards

- `--blade-tip-compensation` expects the **original** SVG. The cutter guards against combining it with nonzero legacy `--blade-offset-mm` or `--loop-overlap-mm`.
- `v030_clean_compensated.svg` is already a holder path. Feed it to the cutter **without** stateful or legacy compensation.
- The cutter cannot reliably detect an already-compensated SVG. File naming and operator discipline are required.
- `geometry_scaling.py` is historical and should not be used to change machine calibration. Scaling and stateful compensation are different transformations.

## Model validation boundaries

Passing unit tests verifies code properties, not physical tip placement. A successful inverse fit is meaningful only if the forward predictor matches the real blade. Always measure signed outgoing perpendicular displacement and corner-apex error independently. Avoid introducing a new correction term until its contribution can be isolated experimentally.

## Folder design

Top-level scripts are operational entry points. `calibration/legacy_generators` contains importable historical Python modules (run as `py -m calibration.legacy_generators.smart3_v029_grid` if needed). `calibration/comparisons` contains past/generated artifacts. `tests/` is discovered with `py -m unittest discover -s tests -v` from the root.

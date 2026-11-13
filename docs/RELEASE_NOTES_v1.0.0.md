# Smart3 v1.0.0 release notes

Release date: 2026-11-13

## Release summary

Smart3 v1.0.0 provides a guarded SVG-to-HPGL-to-USB workflow for the calibrated VEVOR Smart 3 cutter. The algorithm is frozen at the best-performing physical-test configuration: v0.30 stateful inverse with signed Y-history, plus the v0.32 corner modifier (0.20 mm overshoot, 0.50 mm approach, 1.50 mm quintic recovery). This is machine-specific, not a universal calibration.

## Features

- `smart3.py build`, `preview`, `check`, `cut`, and `run` for original SVG inputs.
- Build verification checks source, output, calibration, and parameters before a live cut.
- Guarded USB sending requires explicit `--confirm-live-test I_ACCEPT_MOVEMENT`. No automatic retries.
- Blender mesh-edge exporter (`tools/blender_export.py`), non-destructive, thin 0.05 mm display strokes, millimetre SVG dimensions.
- Grid-array generator (`tools/grid_array.py`), with a default 5 mm translated geometry margin, configurable row/column count and spacing.
- Regression test runner `python run_tests.py`.

## Physical validation

- A 16 mm square was physically cut using RC1.
- A Blender-exported SVG was built, previewed, and checked successfully.
- A 2×4 grid of the Blender geometry, with 5 mm gaps and 5 mm margin, built and checked as eight contours. The user reported a physical cut with clean, closed loops.
- Windows regression suite: 66 tests run, 1 skipped, 0 failures, before the final release-only changes.

## Known limitation: small rounded features

Rounded tines of a comb-like geometry approximately 1 mm wide cut more pointed than the SVG design. The cause has not been isolated: corner overshoot, curve discretization, blade mechanics, or interactions may contribute. The same eight-copy grid cut with clean, closed loops. The v1.0 release intentionally retains the tested parameters rather than adding an unverified correction.

A future investigation should compare original and compensated holder trajectories, isolate overshoot on smooth/high-curvature features, and evaluate curvature-dependent compensation with controlled physical tests. **This limitation is deferred, not fixed.**

## Other limitations and safety

- Residual corner gaps or pre-turn flaps may occur.
- SVG support is constrained; unsupported transforms and primitives may be rejected. Inspect the holder preview.
- Calibration is specific to the tested cutter. Verify origin, material, feed, and mat limits before every cut.
- A successful USB write is not proof of completed physical cutting. Never automatically resend after partial/uncertain execution.
- Generated holder-path preview SVGs are not source cut geometry; do not double-compensate them.

## Versioning

This archive identifies itself as 1.0.0. A Git tag is not included and must be created in a Git repository by the maintainer.

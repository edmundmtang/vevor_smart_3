# v1.0.0 release status

- [x] Freeze physically selected compensation parameters.
- [x] Unified build / preview / check / cut / run CLI.
- [x] Guarded live-cut authorization and build verification.
- [x] Blender exporter and thin SVG strokes.
- [x] Grid generator with translated geometry margin.
- [x] Windows regression tests (66 run, 1 skipped, 0 failures before final release-only edits).
- [x] Blender SVG and eight-contour grid validated through physical cutting with clean, closed loops.
- [x] Document small rounded-tip accuracy as a known limitation.
- [ ] Run the final 1.0.0 regression suite on the Windows cutter PC.
- [ ] Optionally create Git tag `v1.0.0` in the maintainer's repository.

## Deferred to a future release

- Investigate pointed tips on ~1 mm rounded tines without regressing loop closure.
- Further characterize small-feature accuracy and cut ordering.

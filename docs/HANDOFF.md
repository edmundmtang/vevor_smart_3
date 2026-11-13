# Engineering handoff — VEVOR Smart 3 cutter

**Baseline:** v0.30 cleaned stateful predictor/inverse, optional in `smart3_cut.py`. **Status:** experimental. Last reported physical test: v0.30, cases 4 and 6. **Next planned work:** a *holder-side*, bounded corner-reach maneuver with 0.10 and 0.20 mm trials; **not implemented** in this handoff.

## What is working

- SVG → HPGL and guarded USBPRINT transport, with dry-run and explicit live-cut gate.
- Axis calibration currently in `settings.txt`: X 0.74906512, Y 3.59950979. Do not alter to fix drag-knife tracking.
- Force 200 / speed 100 produced usable cuts on the tested vinyl; these are cutter command values, not calibrated physical units.
- v0.30 cleaned up competing turn-direction bias, altered apex targets, apex taper and intended-path-driven history. It retains a single experimental Y-history term (−0.300 mm), nominal blade offset 0.20 mm and recovery parameter 1.39 mm.

## Latest physical evidence (reported by tester)

| Revision | Case 4 | Case 6 | Interpretation |
|---|---|---|---|
| v0.29 | Outgoing segment overshot intended parallel line by about 0.35 mm | Outgoing segment overshot by about 0.25 mm; corner reach improved but slight flap | Persistent lateral bias, not merely short corner transient |
| v0.30 | Upper outgoing cut **short by about 0.10 mm** | Straight segments align; cuts fail to meet because blade rounds about 0.10 mm before apex | Steady-state alignment improved; corner fidelity remains |

The v0.30 results are **physical observations**, not simulator validation. The sign/axis conventions of some earlier measurements varied; do not infer an exact vector correction from unsigned distances alone.

## Next experiment

1. Keep the v0.30 predictor and outgoing straight-line alignment fixed.
2. Implement a corner-reach **holder maneuver**, constrained by original tip geometry, not a deformation of the intended SVG target.
3. Generate A = v0.30 reference, B = 0.10 mm reach, C = 0.20 mm reach; ensure no other settings change.
4. Dry-run, inspect corrected bounds, and cut B before considering C.
5. Measure center gap, early rounding distance, flap and signed outgoing-normal offset in cases 4 and 6.

Do not reuse `calibration/comparisons/B_apex_010` or `C_apex_020` as v0.30 variants: these are **historical v0.28** tests with a different algorithm.

## Non-goals and risks

- No global geometry scaling until tracking, corner reach and loop closure are stable.
- Do not add a separate persistent outgoing correction without first identifying overlap with existing Y-history.
- Do not mix stateful compensation and legacy offset/overlap, or compensate a precompensated SVG twice.
- No verified USB buffering guarantee or device-side execution acknowledgement.

## What a successor should do first

Run the offline suite and current dry-run commands in README.md; inspect `blade_tip_clean.py`, `blade_tip_stateful.py` and `smart3_cut.py`. Reproduce the latest compact physical test on scrap vinyl, using the same origin and blade setup, **before** changing model parameters. Keep signed, perpendicular measurements and distinguish settled straight-line offsets from corner-only rounding.

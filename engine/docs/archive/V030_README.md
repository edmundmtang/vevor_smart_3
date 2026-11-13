# Smart 3 v0.30 — clean experimental blade-tip model

## Scope and limitations

This is an **architecture cleanup and calibration baseline**, not a verified physical fix for the measured outgoing parallel offsets. Physical measurements do not yet identify a unique state law. **Default cutter behavior is unchanged.** No automatic machine movement is performed by the generator or test suite.

The new optional `--blade-tip-compensation` path uses one forward predictor and the existing bounded inverse solver. It **disables** the independent turn-direction lateral bias, altered apex target, apex taper, and intended-path-driven history. The inverse objective is the original contour; there is no post-inverse outgoing normal shift. The single Y-history term retains the experimental -0.300 mm starting value, and blade offset 0.20 mm and recovery 1.39 mm are hypotheses, not proven constants. No geometry scaling or machine calibration changes.

The legacy v0.29 generator and its tests are preserved for reference; they are not used by the new cutter option. The underlying angular-response law and inverse solver are still phenomenological and may require replacement after measurements. The v0.29 improved corner reach may regress when artificial apex targets are removed; this is intentional isolation, not a claim of better physical performance.

## Important safety and no-double-compensation rules

- Feed **original, uncompensated** SVGs to `--blade-tip-compensation`. Precompensated SVGs cannot be reliably detected; applying the new option to one will double compensate.
- The cutter rejects combining `--blade-tip-compensation` with nonzero `--blade-offset-mm` or `--loop-overlap-mm`.
- If using `v030_clean_compensated.svg`, **do not** enable any compensation flags: it already describes the HOLDER path.
- Always run `--dry-run`, inspect printed physical and corrected bounds and generated HPGL, and verify material placement before considering a live cut.
- Live cutting remains gated by `--cut --confirm-live-test I_ACCEPT_MOVEMENT` and is Windows-only. No machine calibration changes.

## Generate a compact two-case comparison

From this directory:

```powershell
py smart3_v030_grid.py
py smart3_cut.py v030_comparison/v030_original.svg --blade-tip-compensation --dry-run --output v030_comparison/v030_from_cutter.hpgl
py smart3_cut.py v030_comparison/v030_clean_compensated.svg --dry-run --output v030_comparison/v030_from_precompensated.hpgl
py -m unittest discover -q
```

These two HPGL jobs are alternate routes to a similar model-compensated holder path. **Do not cut both on the same vinyl location.** The original SVG is for the new integrated cutter option; the compensated SVG is for the legacy cutter with all compensations off. Compare with the v0.29 B/C physical result on fresh material.

## What to measure

- Case 4: signed vertical difference between settled left/right strokes; prior observed ~0.35 mm outgoing overshoot.
- Case 6: signed perpendicular distance of the settled outgoing stroke from the extrapolated intended line; prior observed ~0.25 mm overshoot.
- For both: whether the apex meets, any flap, and approximate recovery distance.

A lower simulated fitting error is **not** proof of a better physical cut. The measured signed errors are needed to calibrate or replace the single lateral state law. Do not introduce an additional persistent normal correction without checking whether the existing history law is the source.

## Commit

`Simplify stateful blade compensation pipeline`

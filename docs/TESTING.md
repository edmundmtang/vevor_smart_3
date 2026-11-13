# Test plan and reproducibility

## Offline tests

From repository root:

```powershell
py -m unittest discover -s tests -v
py smart3_v030_grid.py
py smart3_cut.py calibration/comparisons/v030_comparison/v030_original.svg --blade-tip-compensation --dry-run --output calibration/comparisons/v030_comparison/v030_dry_run.hpgl
```

Do not treat passing tests as proof of a correct blade-tip model. Historical tests are intentionally retained, including tests of older model options that are not enabled in v0.30.

## Physical comparison

Use force 200, speed 100, the established machine axis calibration, no geometry scaling, no legacy offset/overlap, same blade depth and vinyl. Start with the compact cases 4 and 6. Keep each version's geometry, software flags, dry-run log and signed measurements together in a dated folder under `calibration/comparisons/`.

For case 4 record: horizontal endpoint gap and signed Y difference of settled left/right strokes (state which is above). For case 6 record: whether the cuts meet at center, distance at which incoming line starts to round before apex, outgoing settled perpendicular offset (signed), flap and recovery length. A straightedge helps distinguish a parallel displaced line from a short-lived corner transient.

## Next trial is not implemented

The proposed v0.31 holder-side corner reach variants (0.10 mm, 0.20 mm) are a **plan**, not files in this package. Do not substitute the archived v0.28 apex-target variants as if they exercised v0.30.

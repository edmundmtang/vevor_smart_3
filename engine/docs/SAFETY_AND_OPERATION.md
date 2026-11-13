# Safety and operation (Windows)

## Before a cut

1. Confirm the correct cutter and USBPRINT connection. Use `py smart3_usb_probe.py --help` to inspect available diagnostic options.
2. Inspect `settings.txt` and use the same validated physical setup. Current nominal mat is 304.8 × 304.8 mm; usable vinyl area can be smaller.
3. Load scrap material securely, manually move to the established starting position (historically displayed Y approximately −115), then press the physical **Origin** button. Verify the actual origin on your machine.
4. Keep fingers, tools and loose material clear of carriage and moving mat.
5. Dry-run and inspect **corrected holder bounds**, HPGL and material coverage before sending any live command.

## Current compact comparison

```powershell
py smart3_v030_grid.py
py smart3_cut.py calibration/comparisons/v030_comparison/v030_original.svg --blade-tip-compensation --tip-history-mm -0.300 --dry-run --output calibration/comparisons/v030_comparison/v030_dry_run.hpgl
```

To authorize a **live** cut only after inspecting the dry-run, use the same original SVG and options, replacing `--dry-run --output ...` with:

```powershell
--cut --confirm-live-test I_ACCEPT_MOVEMENT
```

The live command is an explicit opt-in to movement; no live operation is part of the automated test suite. Use the CLI `--help` to verify supported option names before cutting.

## Important caveats

- Never run `--blade-tip-compensation` on a precompensated holder-path SVG.
- Keep legacy offset and overlap at zero when using stateful compensation.
- Unsupported SVG transforms and unsupported elements may fail closed; simplify/flatten SVGs first.
- The nominal physical mat bounds are not a guarantee of safe material clearance. Inspect the actual cutting region and origin.
- A Windows WriteFile success does not prove complete device execution. Do not automatically retry a partial/failed write: that risks duplicate cutting.

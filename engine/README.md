# VEVOR Smart 3 — direct USB SVG cutter

**Project state:** v0.30 experimental blade-tip compensation; physical cuts have **not** established a production-ready drag-knife model. This repository is a working research prototype, not a validated general-purpose cutter driver.

## First five minutes

1. Read [docs/HANDOFF.md](docs/HANDOFF.md) for the current physical observations and next experiment.
2. Read [docs/SAFETY_AND_OPERATION.md](docs/SAFETY_AND_OPERATION.md) before connecting the machine.
3. Run `py -m unittest discover -s tests -v` from the repository root.
4. Generate the compact calibration sample with `py smart3_v030_grid.py`.
5. Dry-run the original geometry using `py smart3_cut.py calibration/comparisons/v030_comparison/v030_original.svg --blade-tip-compensation --tip-history-mm -0.300 --dry-run --output calibration/comparisons/v030_comparison/v030_dry_run.hpgl`.

**Do not cut without verifying the physical origin, material, HPGL and movement bounds.** `--cut --confirm-live-test I_ACCEPT_MOVEMENT` sends live motion commands. A successful USB write does not prove that the cutter executed the entire job.

## Layout

```text
smart3_cut.py             Main SVG → HPGL converter and guarded USB sender
smart3_usb_probe.py       Windows USBPRINT probe (diagnostic)
smart3_v030_grid.py       Current compact two-case comparison generator
blade_tip_clean.py        v0.30 model configuration and inverse interface
blade_tip_stateful.py     Experimental forward model and inverse solver
blade_offset.py           Legacy compensation implementation
loop_closure.py           Legacy seam/overlap implementation
geometry_scaling.py       Historical scaling utility (not enabled in v0.30)
settings.txt              Local calibration, cut and mat settings
README.md                 This entry point
docs/                     Architecture, operation, physical evidence, handoff
calibration/comparisons/  Generated and historical physical-test variants
calibration/legacy_generators/  Older experimental grid generators
calibration/legacy_patterns/    Historical SVG/HPGL files
calibration/historical_guides/  Prior test instructions (not current workflow)
tests/                    Offline automated tests
```

The older `README.txt` is preserved under `docs/archive/README_v015.txt`. The earlier v0.30 release notes are at `docs/archive/V030_README.md`. They describe historical layouts and should not override the commands in this README.

## Current compensation rules

The default cutter does **not** enable stateful blade compensation. Use `--blade-tip-compensation` only with **original uncompensated SVG geometry**. Never pass a precompensated holder-path SVG with this flag. Nonzero `--blade-offset-mm` and `--loop-overlap-mm` cannot be combined with the stateful mode. No geometry scaling is enabled in the current comparison.

## Documentation map

- [docs/HANDOFF.md](docs/HANDOFF.md): status, measurements, unresolved problems, next steps
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): pipeline, model limitations and no-double-compensation rules
- [docs/SAFETY_AND_OPERATION.md](docs/SAFETY_AND_OPERATION.md): dry-run and live-cut procedure
- [docs/TESTING.md](docs/TESTING.md): offline tests and controlled physical tests
- [docs/EXPERIMENT_HISTORY.md](docs/EXPERIMENT_HISTORY.md): historical versions and evidence

## Requirements

Python 3 on Windows for USB transmission; offline generation/tests may work on other platforms. SVG `path` elements require the optional `svgpathtools` dependency; simple supported SVG primitives do not. The USB interface is Windows USBPRINT, not a standard serial port.

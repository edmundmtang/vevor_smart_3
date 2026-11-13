# Smart 3 — v0.32 experimental corner sweep

This is a self-contained experiment. **No `v030_baseline` or `smart3_v031_corner_sweep` directories are needed.**

- `sweep.py` — build, validate, and guarded live-send entry point
- `corner_transition_v032.py` — experimental local overshoot/recovery modifier
- `corner_sweep_target.svg` — intended blade-tip geometry, NOT a holder-path cutting file
- `engine/` — unchanged v0.30 cutter engine, calibration, documentation and regression tests
- `archive/` — prior v0.31 scripts for reference only; not used by `sweep.py`
- `tests/` — new integration and safety tests
- `corner_sweep_v032_EXPERIMENTAL.hpgl` and `.json` — generated, validated pair

## Windows PowerShell

Extract the `smart3` directory to `D:\3D\Smart3\smart3` (or another directory).

```powershell
cd D:\3D\Smart3\smart3
python .\sweep.py build
python .\sweep.py check
cd .\engine
python -m unittest discover -s .\tests -q
cd ..
python -m unittest discover -s .\tests -q
```

Only after inspecting the output and preparing the cutter, for an attended **experimental** cut:

```powershell
python .\sweep.py cut --confirm-live-test I_ACCEPT_MOVEMENT
```

The cutter is not connected or tested by this package's author. `cut` performs a deterministic fresh rebuild and refuses altered HPGL, report, calibration, or settings. It reuses the unchanged v0.30 Windows USBPRINT sender (one write, no retry or execution acknowledgment). **Never feed the generated HPGL back through SVG compensation.**

The 3x3 grid contains 16 mm squares, two separate angle-approach cuts, and those angles rotated 45 degrees. Column A is unmodified v0.30, B adds 0.10 mm, C adds 0.20 mm. Recovery is 1.5 mm with a 0.5 mm approach and quintic easing. To change the sweep:

```powershell
python .\sweep.py build --overshoot 0 0.05 0.10 --approach-mm 0.5 --recovery-mm 1.5 --easing quintic
python .\sweep.py check
```

Prepare at least 110 x 100 mm of usable vinyl cutting area, **plus additional feed/roller gripping margin required by the machine**. Verify cutter origin and travel independently. Stay at the cutter with emergency stop available.

## Engineering caveat

This is **not** a physically validated full geometric corner planner. The v0.32 module applies a bounded, localized, eased incoming-tangent displacement to the v0.30 inverse holder path. It does not explicitly insert a straight overshoot segment or enforce a tangent-continuous return, and the predictor diagnostics are hypothetical. The live path is enabled to allow a cautious physical **experiment**, not to certify that it improves apex reach or flap formation. The existing signed -0.300 mm Y-history and 1.39 mm recovery are unchanged.

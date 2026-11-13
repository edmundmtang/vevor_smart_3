# Smart3 v1.0.0 — VEVOR Smart 3 vinyl cutter

This is the **v1.0.0 release**, with the best physically tested settings found for this cutter. It preserves the machine-specific calibration and the v0.30 stateful inverse with signed Y-history, and fixes the experimentally preferred v0.32 corner modifier at **0.20 mm overshoot / 0.50 mm approach / 1.50 mm recovery / quintic easing**.

## Install

```powershell
python -m pip install -r .\requirements.txt
```

Install dependencies from `requirements.txt`. The Blender mesh exporter emits polylines/polygons and has been tested with the Smart3 parser. Other SVG path types remain subject to parser limitations.

## Commands (Windows PowerShell)

```powershell
python .\smart3.py build .\examples\square.svg
python .\smart3.py preview .\examples\square.svg
python .\smart3.py check .\examples\square.svg
python .\smart3.py cut .\examples\square.svg --confirm-live-test I_ACCEPT_MOVEMENT
```

`build` creates `square.hpgl` and `square.json` without machine movement. `preview` creates `square_holder_preview.svg`: **blue is commanded holder geometry**, gray dashed is original target geometry. Preview SVG is NOT an input to cut. `check` recomputes the job and compares HPGL, source hash, calibration, and report. `cut` only transmits a previously verified build. `run` builds, verifies and transmits in one command with the same explicit confirmation:

```powershell
python .\smart3.py run .\examples\square.svg --confirm-live-test I_ACCEPT_MOVEMENT
```

**Before any live cut:** verify cutter origin, actual usable material area, pinch-roller grip, and stop access. No USB write proves machine execution. Failed or partial writes must not be automatically retried. Never submit an already compensated holder SVG as the source.

## SVG limitations

The inherited parser supports a constrained set of untransformed SVG primitives and path commands. It rejects unsupported elements and transforms. Flatten transforms in your SVG editor and export a simple SVG with physical mm dimensions. Inspect the preview before cutting unfamiliar files.

## Grid tool

```powershell
python .\tools\grid_array.py .\examples\square.svg .\examples\grid.svg --rows 3 --cols 3 --gap-mm 5 --margin-mm 5
python .\smart3.py build .\examples\grid.svg
```

## Tests

```powershell
python .\run_tests.py
```

## Release validation and known limitations

The Windows installation passed 66 regression tests (1 skipped). A Blender-exported eight-contour 2×4 grid with 5 mm margin passed build, preview, and check, and the user reported a successful physical cut with clean, closed loops. See `docs/RELEASE_NOTES_v1.0.0.md`.

- Corner gaps and pre-turn flaps remain possible. This configuration is the best observed among the user's physical tests, not a guarantee of geometric accuracy.
- Calibration and feed/origin behavior are specific to the tested cutter.
- Blender exporter is included at `tools/blender_export.py` (see `docs/BLENDER_EXPORT.md`); a real Blender-to-grid-to-cutter test was completed.
- Small rounded tines around 1 mm wide may cut too pointed. Cause is not isolated; see release notes. This is deferred, not resolved.
- The original `engine/` directory contains historical experiments for traceability; production entry point is `smart3.py`.

## Blender mesh exporter

Open `tools/blender_export.py` inside Blender and follow `docs/BLENDER_EXPORT.md`. It exports world-XY mesh edges into millimetre SVG without modifying the source mesh.

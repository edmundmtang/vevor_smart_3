# Smart3 v1.0.0 — VEVOR Smart 3 vinyl cutter

This is the **v1.0.0 release**, with the best physically tested settings found for this cutter. It preserves the machine-specific calibration and the v0.30 stateful inverse with signed Y-history, and fixes the experimentally preferred v0.32 corner modifier at **0.20 mm overshoot / 0.50 mm approach / 1.50 mm recovery / quintic easing**.

## Install

From the repository directory, install dependencies:

```powershell
python -m pip install -r .\requirements.txt
```

The Blender mesh exporter emits polylines/polygons and has been tested with the Smart3 parser. Other SVG path types remain subject to parser limitations.

## Command-line interface

Run the production entry point from the repository directory:

```text
python .\smart3.py [-h] [--output OUTPUT] [--confirm-live-test CONFIRM_LIVE_TEST] [--cut-force CUT_FORCE] [--cut-speed CUT_SPEED] {build,check,preview,cut,run} svg
```

The action and SVG source are required positional arguments. Options may be supplied before or after the positional arguments.

| Argument | Meaning |
| --- | --- |
| `action` | One of `build`, `check`, `preview`, `cut`, or `run`. |
| `svg` | Path to an **existing, original, uncompensated** `.svg` input file. Do not use an already compensated holder preview. |
| `-h`, `--help` | Print CLI help and exit. |
| `--output PATH` | Path for the generated/verified `.hpgl` file, which **must end in `.hpgl`**. Its report is written/read at the same path with a `.json` extension. Defaults to the input SVG path with `.hpgl` extension. Used by `build`, `check`, `cut`, and `run`; **not used by `preview`**. |
| `--cut-force N`, `--force N` | Override `cut_force` from `engine/settings.txt`. Integer from **1 to 400**; hardware support across this range is unverified. |
| `--cut-speed N`, `--speed N` | Override `cut_speed` from `engine/settings.txt`. Integer from **1 to 300**. |
| `--confirm-live-test I_ACCEPT_MOVEMENT` | Mandatory exact confirmation token for `cut` and `run`. Does not bypass Windows-only live USB restrictions or other validation. |

If force/speed overrides are omitted, the program loads the corresponding settings from `engine/settings.txt`. Overrides are used for job generation and verification, and for live transmission where applicable. Keep the same overrides for a later `check` or `cut` as were used for `build`: the verifier compares the generated report and HPGL byte-for-byte against the saved files.

### Command behavior

| Action | Files read | Files written | Cutter movement |
| --- | --- | --- | --- |
| `build` | Original SVG, settings | `.hpgl` and companion `.json` | **No** |
| `preview` | Original SVG, settings | `<svg-stem>_holder_preview.svg` beside the source | **No** |
| `check` | Original SVG, settings, existing `.hpgl` and `.json` | None | **No** |
| `cut` | Original SVG, settings, existing `.hpgl` and `.json` | None | **Yes, on Windows** |
| `run` | Original SVG, settings | `.hpgl` and `.json` (then verifies and transmits) | **Yes, on Windows** |

All actions calculate compensated geometry and validate applicable settings and material bounds. `check` and `cut` require a previously built matching HPGL/report pair. `run` creates/replaces that pair, verifies it, and then sends it. The live commands require an explicit confirmation and refuse to run on non-Windows systems.

### Usage examples (Windows PowerShell)

**1. Build an offline cutting job** (no USB transmission):

```powershell
python .\smart3.py build .\examples\square.svg
```

Creates `examples\square.hpgl` and `examples\square.json`. The JSON report records the source SHA-256, HPGL SHA-256, settings, contour count, compensation parameters, and bounds.

**2. Preview the commanded holder path** (no USB transmission):

```powershell
python .\smart3.py preview .\examples\square.svg
```

Creates `examples\square_holder_preview.svg`. **Blue** is the compensated holder path; **gray dashed** is the original target. The preview is for inspection only: **never feed it back to `build`, `cut`, or `run` as the source**. `--output` does not rename this preview.

**3. Verify an existing job** (no USB transmission):

```powershell
python .\smart3.py check .\examples\square.svg
```

Recomputes the job and checks the saved report and HPGL against the current SVG, settings, calibration, and CLI overrides. If the files are missing or anything differs, verification fails; no cut is sent.

**4. Cut an already built and verified job** (live USB movement):

```powershell
python .\smart3.py cut .\examples\square.svg --confirm-live-test I_ACCEPT_MOVEMENT
```

Verifies the saved job again before transmission. It does not rebuild the saved files. Live cutting is supported **only on Windows**.

**5. Build, verify, and cut in one command** (live USB movement):

```powershell
python .\smart3.py run .\examples\square.svg --confirm-live-test I_ACCEPT_MOVEMENT
```

This creates/replaces the HPGL and report, verifies them, and sends the job. Use only when ready for immediate cutter movement.

**6. Choose a custom HPGL/report destination:**

```powershell
python .\smart3.py build .\examples\square.svg --output .\examples\custom_job.hpgl
python .\smart3.py check .\examples\square.svg --output .\examples\custom_job.hpgl
python .\smart3.py cut .\examples\square.svg --output .\examples\custom_job.hpgl --confirm-live-test I_ACCEPT_MOVEMENT
```

The matching report is `examples\custom_job.json`. The destination directory must already exist. A filename without the `.hpgl` extension is rejected.

**7. Override force and speed for an offline build:**

```powershell
python .\smart3.py build .\examples\square.svg --force 120 --speed 80
python .\smart3.py check .\examples\square.svg --force 120 --speed 80
```

The long forms `--cut-force 120 --cut-speed 80` are equivalent. These are **illustrative CLI values, not recommended cutting settings**. Choose values appropriate to the machine, blade, and material.

**8. Cut a job built with overrides:**

```powershell
python .\smart3.py cut .\examples\square.svg --force 120 --speed 80 --confirm-live-test I_ACCEPT_MOVEMENT
```

Use exactly the overrides from the build. If you built with an override but omit it during `check` or `cut`, verification will fail unless the resulting effective settings happen to match.

**9. One-step run with a custom output and overrides:**

```powershell
python .\smart3.py run .\examples\square.svg --output .\examples\custom_job.hpgl --cut-force 120 --cut-speed 80 --confirm-live-test I_ACCEPT_MOVEMENT
```

**10. Display help:**

```powershell
python .\smart3.py --help
```

### Typical safe workflow

1. Export a simple original SVG with physical millimetre dimensions.
2. Run `preview` and inspect the blue holder geometry against the gray target.
3. Run `build`, optionally specifying output, force, and speed.
4. Run `check` with the **same** output path and overrides.
5. Inspect cutter origin, material area, pinch-roller grip, and accessible stop controls.
6. On Windows, run `cut` with the same output path and overrides and the exact confirmation token, while attending the machine.

**Before any live cut:** verify cutter origin, actual usable material area, pinch-roller grip, and stop access. A successful USB write does **not** prove the machine executed the job. Failed or partial writes must **not** be automatically retried.

### Common errors and troubleshooting

| Symptom | Cause / action |
| --- | --- |
| `Expected an existing original SVG input file` | Supply an existing `.svg` source file. |
| `SVG has no cuttable contours` | Export supported geometry; verify the SVG contains usable contours. |
| `Output must have .hpgl extension` | Give `--output` a `.hpgl` filename. |
| `Missing built HPGL/report; run build first` | Run `build` with the same source and `--output` location before `check` or `cut`. |
| `Job, source, settings or parameters differ from current build; NO CUT SENT` | Check whether the SVG, settings, HPGL, JSON report, output path, or force/speed overrides changed; rebuild and recheck deliberately. |
| `Live operation requires --confirm-live-test I_ACCEPT_MOVEMENT` | Supply the exact token for `cut` or `run` only when ready for physical movement. |
| `Live USB cutting is supported on Windows only` | Use Windows for live cutting; offline actions can run without USB transmission. |
| `BLOCKED: ...` | Validation or an expected runtime error stopped the operation. Review the reported reason; don't blindly retry a partially transmitted job. |

The CLI exits with status `0` on success and `1` for handled validation/runtime errors. Invalid argparse syntax or argument choices are rejected by argparse before action execution.

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

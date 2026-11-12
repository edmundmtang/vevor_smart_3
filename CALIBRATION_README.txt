Smart 3 v0.11 calibration suite (offline pattern generation)

Place smart3_calibrate.py next to smart3_cut.py, settings.txt and smart3_usb_probe.py.
No changes to USB framing, force, speed, or existing scale settings.

Generate calibration patterns:
  py smart3_calibrate.py generate --mode axes --output calibration_axes.svg
  py smart3_calibrate.py generate --mode details --output calibration_details.svg

Dry run before cutting:
  py smart3_cut.py calibration_axes.svg --dry-run
  py smart3_cut.py calibration_details.svg --dry-run

The axes pattern contains open lines of lengths 20,40,80,120,160 mm in each
axis. Measure the physical cut length endpoint-to-endpoint, using a loupe or
microscope where possible. Avoid measuring line thickness or closed squares.
Repeat each pattern if possible. The design uses a 200 x 190 mm SVG page;
its geometry fits the nominal 304.8 mm mat but verify usable area and origin.

Fill calibration_measurements_template.csv with measured lengths, save as
measurements.csv, then run:
  py smart3_calibrate.py fit measurements.csv

Regression estimates measured = slope * target + intercept.
Suggested new scale = current scale / slope. Inspect intercept and residuals;
large nonzero intercepts can indicate backlash, blade behavior or measurement
bias. Do not automatically change settings.txt; verify with a fresh test.

The details pattern contains 1,2,3,5,10 mm squares in both directions and
circles of the same diameter. It deliberately DOES NOT overcut loops.
Observe whether the end meets the beginning, is displaced laterally, or has a
short gap. Record photos and results; blade offset is NOT assumed from 45 degrees.

Cut only after loading the mat, manually setting Y ~ -115 and pressing Origin.
Experimental live command (attend cutter and start with small jobs):
  py smart3_cut.py calibration_axes.svg --cut --confirm-live-test I_ACCEPT_MOVEMENT

Mat checks: geometry outside the configured 12 x 12 inch maximum is blocked;
reaching 90% of configured axis travel produces a warning. This is a travel
warning, not a guarantee that the nominal mat is fully usable. For smaller
usable dimensions, lower mat_width_mm and mat_height_mm in settings.txt.

No physical cutter tests have been performed for this release.

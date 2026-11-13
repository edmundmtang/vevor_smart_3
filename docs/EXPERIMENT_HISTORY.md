# Experimental history (selected physical findings)

This is a condensed map of the physical observations. See archived guides and variant files under `calibration/` for historical artifacts. Some older guides describe superseded options and folder layouts.

| Version | Observation / result |
|---|---|
| v0.16–0.17 | Mirrored-L cuts revealed a persistent horizontal gap, largely insensitive to ±X travel direction. |
| Force/speed sweep | Force 150 insufficient, 175 and 200 usable; force 200 and speeds 50–100 gave roughly 0.18 mm gap and 1.39–1.41 mm recovery in tested shapes. |
| v0.19 | Heuristic corner overshoot introduced outward flaps. |
| v0.20–0.22 | Stateful forward/inverse improved closure but corners rounded; case 4 and 6 gaps around 0.45 mm. |
| v0.23 | Abrupt Y-history offset regressed alignment and curves. |
| v0.24 | Reverted to stable predictor behavior. |
| v0.25 | Experimental dimensional scaling only in test generator; deferred pending tracking fixes. |
| v0.26 | Negative signed Y-history −0.225 improved cases 4/6 relative to positive polarity. |
| v0.27 | −0.300 mm case B appeared aligned; corner rounding still prevented case 6 meeting. |
| v0.28 | 0.20 mm apex extension made case 6 meet but introduced flap and case 4 misalignment. |
| v0.29 | Corner smoothing improved shape, but outgoing lines overshot parallel to intended contour: ~0.35 mm case 4, ~0.25 mm case 6. |
| v0.30 | Simplified model: case 4 upper outgoing short ~0.10 mm; case 6 lines aligned, but rounding starts ~0.10 mm before center and cuts do not meet. |

**Interpretation:** the current priority is localized corner fidelity while preserving settled straight-line alignment. Do not assume the older apex target modification is physically correct.

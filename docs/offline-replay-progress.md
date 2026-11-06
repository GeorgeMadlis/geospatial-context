# Offline replay progress — 2026-11-06

The operator authorized use of existing offline images and other files. This check reads the original Sentinel round-0003 directory and does not mutate it, make provider requests, or copy its raw data or imagery into this repository. It is an incremental integrity inspection, not the full requested replay or scientific validation.

Command, using the existing Sentinel environment:

```sh
/Users/server/projects/sentinel-monthly-forest-cover/.venv/bin/python scripts/replay_round0003.py /Users/server/projects/sentinel-monthly-forest-cover/reviews/road-like-ndvi-2025-2026-monthly/rounds/round-0003 > /private/tmp/geocontext-replay-local.json
```

47 checks passed: 20 GS-13 capture hashes and counts; 18 individual E01–E10 file hashes (E03 matched using original manifest paths); the GS-04/05 date discrepancy; existence and parsability of three S08 ArcGIS files; two recomputed linear measurements, power-line intersections, planning overlap and the notice approval field. Full detail, paths, observed hashes and historical timestamps are in `/private/tmp/geocontext-replay-local.json`; SHA-256 `0f57c506e35601c5d330512d834faadfb5ce6a1490b36c93b314086ed10d816d`. This temporary report is local, not a committed fixture. The three S08 checks calculate present-day hashes and counts, but no independently recorded historical hashes were established for these files; their historical integrity is therefore unverified.

The 53734 saved RGB listing contains a 2025-04-03 filename while a retained WMS metadata point for the same sheet reports 2023-06-09. Listing SHA-256 `31441c6dd9d9d7f0f61c6822e81fbcf5119f039d050b927641f38297218f1ba8`; WMS point file SHA-256 `b83260969f747a3307afb87d615fa23d3dcd3c900c012464b3668557db36c063`. A listing filename is not embedded image metadata, and the association of the WMS layer to a flight remains inferred. The parser omits date ranges and year-only names rather than assigning an invented day.

Remaining work includes real fixture licensing and distribution decisions, additional geometry comparisons and feature IDs, S08 historical-hash verification, pinned-schema execution logs, the rest of the adapters and CI replay, and an independent challenge. Unavailable or unqueried sources remain distinct from a successful empty result. Notice approval is not a felling date, and the October control areas are not established ground truth.

The original ROI-01 geometry intersects ETAK rail feature 4076351 for 143.02 m (EPSG:3301), consistent with the historical 143 m rounding. The nearest recorded road-4 carriageway-1 section is 24.23 m from ROI-02 with 0 m intersecting length (EPSG:3301), consistent with the recorded 24 m and 0 m. These are measurements against the historical ROI, not an identification of the later unlocated feature.

The additional replay returned 232.7 m of grouped 10 kV line intersections in ROI-02 (EPSG:3301), 46.0% geodesic planning-polygon overlap in ROI-01, and 808 notices with an approval-date field. The latter is an administrative decision date, not a felling date. Neither the plan overlap nor these intersections identify the later unlocated feature.

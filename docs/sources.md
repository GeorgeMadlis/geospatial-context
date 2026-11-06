# Source status and access

`geocontext/sources.yaml` lists candidate source IDs and historical endpoints, not a permission grant or current service-health result. `adapter_status.yaml` distinguishes local parsers from provider queries; `tool_catalog.yaml` separates implementation and testing from actual invocations, which appear only in a private ledger. All live access remains disabled. Review licences, redistribution, exact paths and layers before enabling it.

The historical Teeregister source uses the ArcGIS REST MapServer, including layers 1, 9 and 12; a WFS is an unverified lead. The KMA electricity WMS is distinct from the directed restrictions WFS. Notice approvals are administrative decisions, not felling dates. Geoportaal sheet filenames can disagree with WMS metadata and do not prove acquisition of a particular rendered image. A successful empty local filter applies only to the retained response and does not establish source coverage or historical absence.

# Historical curation import

`apply_counterpart_decisions.py` is the original one-time importer used in
AI Gene Review before the analysis archive moved to this repository. It is
retained verbatim as provenance for `counterpart-decisions.yaml`, not as a
supported command in this repository. It assumed a combined analysis/review
checkout and refuses to replace existing assessments.

Current decisions live in AI Gene Review's gene YAML. Use the supported
`export-evidence` command to update compact source extracts after manually
reviewing new analyses; never reapply this historical manifest over current
curation.

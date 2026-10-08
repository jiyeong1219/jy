# Model contract

No kettle network is supplied yet: material names/masses and manufacturing
inventory remain unavailable. This is an input contract, not a calculated model.

`scripts/calculate_reviewed.py` accepts a JSON object with:

- `declared_unit`: `one_manufactured_packaged_kettle`.
- `review`: each gate named in that script has `status: approved` and a substantive
  `evidence` citation/path. These are human review decisions, not computed proofs.
- `source_records`: original local files under this project and exact `sha256`.
- `method`: dataset UUID/version, source, `time_horizon_years: 100`,
  `impact_unit: kg CO2-eq`, biogenic treatment and method-version justification.
- `processes`: ordered single-reference-output normalized process records with
  `id`, `inputs` (provider ID -> reference-unit quantity per own reference unit),
  `elementary` (exact flow key -> elementary quantity per own reference unit).
  Preserve normalization amount, source exchange IDs and source-record hash as
  additional provenance fields. Document zero manufacturing demands if approved.
- `flow_keys`: ordered keys encoding database namespace, UUID, version,
  reference unit, compartment, direction and geography. No name-only matching.
- `characterization`: same keys -> numeric factors, including only explicitly
  reviewed zeros. Attach original CF records and zero/exclusion decisions to review.
- `demand`: product-row demand for one packaged kettle; no use/end-of-life demand.
- `contribution_demands`: one vector per BOM ID plus `component_manufacturing`
  and `assembly`, and any separately modeled other stages. Vectors must sum to
  `demand`. Packaging materials use their own BOM IDs, not an extra duplicate mass.

To attribute manufacturing burdens to materials, either explicitly split their
demand with a documented allocation or report manufacturing as its own group.
Never count both the top-level assembly demand and its upstream material demand
again in the contribution sum. An alternative decomposition is to use separate
foreground stage/material demand columns and their consistent total.

All inputs to A and B must already be normalized and dimensionally compatible.
For a process reference output q, divide every exchange by q. For a provider input
in unit u, convert to the provider reference unit through the documented unit-group
factor. Do not convert kg to MJ, volume or pieces without a sourced physical
conversion. Flow-property conversion factors, coproduct allocation, input/output
waste treatment and negative exchanges need explicit interpretation before export.

The matrix API supports a conservative single-output model with nonnegative
demands and elementary burdens. It rejects unresolved providers, missing CF
decisions, singular systems and signed elementary credits. Extending it to avoided
burdens or substitution is a separate reviewed modeling decision.

The current extraction commands retain native ILCD exchanges and JSON-LD records.
They do **not** automatically normalize or link a complete kettle model. Provider
review, process selection and dimensional verification remain manual until the
specific BOM and supplier network are established. Automated review gates cannot
replace evaluating the evidence.

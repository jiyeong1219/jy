> **가정 기반 추가 시나리오 (2026-10-08):** 사용자 승인에 따라 대체 재료와 제조 전력을 가정해 실제 A/B/C 계산을 실행했습니다. 결과는 **3종 온실가스 GWP100 소계 약 4.43 kg CO₂-eq/주전자**이며, 공급망·온실가스 누락 때문에 전체 공장 출하 GWP 총량이 아닙니다. [HTML 결과 보고서](results/report.html), [계산 결과·전체 가정](results/assumption-screening/results.json). 재현: `python scripts/screening_lca.py` 후 `python scripts/build_screening_report.py`. 아래의 미계산 상태는 이전 독립 기준 준비 실행의 기록입니다. 원본 다운로드가 먼저 필요하며, 추정치의 정확도나 보수성을 보장하지 않습니다.

# BC1 1 L electric kettle: cradle-to-gate LCA

**Status: data integration and matrix implementation validated; kettle GWP100 not
calculated.** The supplied 12-material BOM passes the 723 g product + 137.8 g
packaging = 860.8 g check. Actual inventories were retrieved for seven material
candidates. Five materials, foreground manufacturing inputs, supplier closure and
characterization review remain unresolved. Missing results are null, never zero.

## 1. Study identity and purpose

- Title: one manufactured and packaged BC1 1 L plastic electric kettle.
- Public alias: unknown; no personal names or emails are included.
- Intended repository: https://github.com/jiyeong1219/jy. Files are prepared locally;
  remote publication is not established.
- Run: `bc1-access-assessment-2026-10-08`; study date: 2026-10-08.
- Goal: establish a traceable factory-gate inventory and GWP100/material contribution
  analysis using TianGong and USLCI, without fabricated emission factors.
- Comparison: no competing product/scenario specified. Independent baseline preparation;
  no Git tag or completed impact baseline. Submit a final commit SHA separately after
  committing; this README does not contain its own future commit hash.

## 2. Product, declared unit and system boundary

Declared unit: **one manufactured and packaged BC1 1 L plastic kettle at the factory
gate**. Rated power, lifetime, exact stainless/PVC/nylon grades and factory location
are unknown. BOM source: user-supplied `kettle-bom.csv`, received 2026-10-08, retained
as [data/kettle-bom.source.csv](data/kettle-bom.source.csv); normalized in
[data/bom.csv](data/bom.csv). Hash is recorded in the source manifest.

Include raw-material production, component manufacturing, assembly and packaging.
Exclude consumer heating/use and product end-of-life. Production scrap/waste
treatment is a manufacturing question, not automatically a product end-of-life
exclusion. Transport to/between manufacturing stages requires a documented boundary
and routes; no distance is invented. Cut-offs are not approved. Factory geography
and assessment reference year are unknown; retrieved background datasets represent
different places and periods, not one harmonized contemporary inventory.

## 3. Foreground inventory and quantitative assumptions

| Material | Finished mass, g | Status/source |
| --- | ---: | --- |
| Stainless steel | 186 | Sourced BOM |
| Brass | 20.25 | Sourced BOM |
| Copper | 15 | Sourced BOM |
| PP | 350.25 | Sourced BOM |
| PVC | 43.5 | Sourced BOM |
| Nylon, grade unspecified | 49.5 | Sourced BOM |
| POM | 9.75 | Sourced BOM |
| PC | 6.75 | Sourced BOM |
| ABS | 30 | Sourced BOM |
| Silicone | 12 | Sourced BOM |
| LDPE packaging foil | 6.3 | Sourced BOM |
| Cardboard packaging | 131.5 | Sourced BOM |

All g quantities convert to kg by dividing by 1000. These are finished masses,
not automatically purchase masses. For a sourced yield y, purchase mass = finished
mass/y; no default yield is supplied. Losses/yields, metal forming/drawing, molding
of the unspecified grades, foil extrusion, assembly electricity and factory transport
are **unknown**. Scrap quantities/treatment and prices are also unknown; no monetary
proxy is used. See [foreground inventory](data/foreground_parameters.csv).

A retrieved USLCI PP injection-molding alternative includes **1.034 kg PP resin
and 6.444 MJ electricity per 1 kg molded part**, as well as other exchanges. Those
are source-dataset values, not measured kettle inputs or a chosen kettle process.
Adding that complete process to a separate full resin burden would double count.
The corrugated-product candidate already includes converting; stainless coil
includes rolling. Resin candidates do not establish completed component production.

## 4. Background data and matching decisions

Inspected all five requested TianGong repositories and their installation/access
guides; exact commits are in [source manifest](data/source_manifest.json).

| Repository | Verified role |
| --- | --- |
| TianGong `data` | Real historical ILCD dataset payload; 4,132 processes, 96,820 flows, 25 LCIA methods |
| TianGong `database` | Supabase schemas, migrations, governance and database operations; not a full inventory dump |
| TianGong `cli` | Search, process reads, local validation, conversions and authenticated data-release retrieval |
| TianGong `mcp` | OAuth-protected platform tool access; separate GLAD key for GLAD search |
| TianGong `docs` | Installation/query/authentication/export/OpenAPI documentation |

The `data` README retires maintenance and new GitHub releases as of 2026-06-21.
Current datasets must be exported on the platform. The archive release label is
0.2.0, qualified by exact commit and each dataset version; it is not a current
platform database version. Actual historical data is available in Git without login.

The user-provided [USLCI download guide](https://github.com/FLCAC-admin/uslci-content/blob/dev/docs/release_info/release-downloads.md)
provided downloadable **1.2025-06.0 JSON-LD (962 processes)** and **FY19.Q2.01 ILCD
(758 processes)**. The newest listed 1.2026-09.0 has no ILCD link; its JSON-LD path
points to LCA Commons. The 2021 ILCD link points to Box, blocked here. The guide
warns ILCD loses individual exchange comments, so the newer accessible JSON-LD
is preferred for USLCI candidate inspection. Do not treat the two releases as equal.

[Complete matching table](data/dataset_matching.csv) records all 12 rows, UUID,
version, geography/year, reference product/amount/unit, source, retrieval date,
hash and proxy rationale. [Search log](data/matching_search_log.json) preserves
queries, alternatives and rejected substitutions. [Inventory audit](data/candidate_inventory_audit.json)
records real retrieved exchanges, missing links and allocation evidence. Original
inventories are in ignored `data/raw/candidate_inventories/` and reproducible.

| BOM material | Retrieved candidate | Qualification |
| --- | --- | --- |
| Stainless steel | USLCI stainless 304 flat rolled coil | Grade/form/geography proxy; review pending |
| Brass | None suitable | Composition and real alloy production needed |
| Copper | TianGong cathode copper production | Raw metal candidate; fabrication/provider links unresolved |
| PP | USLCI virgin PP resin | Grade/recycled share and molding unresolved |
| PVC | USLCI suspension-grade PVC resin | Formulation proxy; additives/conversion unresolved |
| Nylon | None suitable | Grade unspecified; filament/yarn rejected as resin |
| POM | None suitable | No suitable candidate found in searched snapshots |
| PC | None suitable | Luggage consuming PC rejected as PC production |
| ABS | USLCI ABS copolymer resin | Specific grade/molding unresolved |
| Silicone | None suitable | Monomer synthesis rejected as cured silicone production |
| LDPE foil | USLCI virgin LDPE resin | Film conversion unresolved |
| Cardboard | USLCI corrugated product | Board-type proxy; converting already included |

Retrieved records are verified **as source inventory records**, not approved matches
or complete cumulative emission factors. No proxy is approved for a full kettle
calculation. Missing in these searches does not prove absent in the current platform.
USLCI monetary USEEIO bridge records cannot be treated as kg-based production LCIs.

## 5. Calculation and impact-assessment methods

Implemented NumPy/SciPy operations in [matrices.py](kettle_lca/matrices.py):

1. **A s = f**: reference-product rows, process columns. Normalize exchanges by
   reference output; positive diagonal production, negative linked provider inputs.
   Solve with sparse `scipy.sparse.linalg.spsolve`, not explicit inversion.
2. **g = B s**: exact elementary-flow rows, same process columns and normalization.
   Direction-specific emissions and resource withdrawals are separate positive burdens.
3. **h = C g**: reviewed GWP100 factors matched to exact flow UUID/version, property,
   unit, compartment/direction and geography. Missing decisions block calculation.

The supported initial model is single-output attributional, without signed credits
or system-expansion substitution. Unresolved coproduct allocation is rejected.
Dataset-specific allocation must be reviewed: for example, PP has `NO_ALLOCATION`
metadata but documents previously applied mass allocation. Metadata alone cannot
establish the system model. Scrap/recycling and biogenic uptake/storage are unresolved.

The archived TianGong climate method UUID
`6209b35f-9447-40b5-b68c-a1099e3674a0`, version `01.00.000`, explicitly identifies
GWP100/100 years and kg CO2 equivalents. Its record labels IPCC 2021 but also has
an IPCC 2013 converted-source label. Its 1,099 parsed factor entries also differ
from the `inventoryItems` metadata value 217. Neither discrepancy is silently
corrected. [Extracted unapproved method](data/gwp_method_unapproved.json) preserves
factors and marks approval false. USLCI JSON-LD archive has no bundled LCIA methods
or categories; a method/flow crosswalk cannot be assumed from matching chemical names.

Provider and CF review is not automated away. The archive audit flags 1,809 TianGong
processes and all 758 old USLCI ILCD processes with at least one flow-resolution
issue, including missing records/version inconsistencies; this does not make every
exchange unusable. See the complete counts/affected IDs in the catalog audit files.
No complete kettle supplier closure or characterized inventory has been demonstrated.

[Reviewed model contract](docs/REVIEWED_MODEL.md) describes normalized input,
provenance and review gates. The runner also checks BOM matching status, source
hashes, demand decomposition, finite solutions and contribution reconciliation.
Material demand groups share the same A/B/C; manufacturing/assembly remain separate
groups unless a justified allocation is recorded.

## 6. How to reproduce the analysis

Tested on Linux, Python 3.12.14, NumPy 2.3.5, SciPy 1.17.0; Node 24.19.0 for the
optional TianGong CLI 0.1.27. Python dependencies are pinned. No random seeds are
needed for deterministic analysis. Run from the repository root:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/workflow.py fetch
.venv/bin/python scripts/uslci.py fetch
.venv/bin/python scripts/workflow.py catalog --archive data/raw/tiangong/tiangong_lca_data
.venv/bin/python scripts/uslci.py catalog --package data/raw/uslci/uslci_fy25_q2_01_olca2_4_1_elci_lib_json_ld.zip
.venv/bin/python scripts/workflow.py catalog --database USLCI --archive data/raw/uslci/ilcd-2019/ILCD --output data/uslci_ilcd_catalog.csv
.venv/bin/python scripts/match_bom.py --tiangong-archive data/raw/tiangong/tiangong_lca_data --uslci-package data/raw/uslci/uslci_fy25_q2_01_olca2_4_1_elci_lib_json_ld.zip
.venv/bin/python scripts/workflow.py method --archive data/raw/tiangong/tiangong_lca_data --method-id 6209b35f-9447-40b5-b68c-a1099e3674a0 --output data/gwp_method_unapproved.json
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/workflow.py status
```

The last command intentionally exits **2** for the blocked study and writes
`results/status.json`. Exit 0 for unit tests does not mean the kettle calculation
passed. Read this README and open the JSON/CSV outputs in an editor; no web UI is
required. To inspect a candidate, use `workflow.py extract --help` (ILCD) or
`uslci.py extract --help` (native JSON-LD). Search via `workflow.py search --query ...
--catalog ... --output ...`; outputs are candidates, not accepted matches.

After resolving all gaps, supply the reviewed model and approved mapping:

```bash
.venv/bin/python scripts/calculate_reviewed.py --model data/reviewed-network.json --output results/independent-baseline
```

This model file is **not supplied or verified yet**. The future runner writes
`results.json`, `contributions.csv` and `matrices.npz`, and refuses to overwrite an
existing run directory. Numerical analysis cannot be reproduced until those missing
model inputs are obtained.

File map: `data/` BOM, metadata catalogs, searches, hashes, matching/audit;
`data/raw/` ignored original data and dependency archive (not an additional project
checkout); `kettle_lca/` extraction, validation and sparse solver; `scripts/` CLI
workflows; `tests/` synthetic algorithm/input tests; `results/` current status and
validation evidence; `docs/` plan, access assessment and modeling contract.

Public historical downloads require no account. For current TianGong data, use
platform Export, or install the published CLI and sign in yourself in a trusted
terminal/browser. Exact access commands and network destinations are in
[DATABASE_ACCESS.md](docs/DATABASE_ACCESS.md). No passwords/tokens belong in chat,
Git, or saved instructions. Preserve dataset-level copyright/license notices,
including DOE/NREL/Alliance notices and JRC/ELCD attribution; do not assume the
TianGong repository MIT license replaces every bundled dataset's terms.

## 7. Results, checks and interpretation

**GWP100 total: not calculated (kg CO2-eq per packaged kettle).** Material impact
breakdown/top three: not calculated. No impact figures are generated without
supported results. [Current result status](results/status.json) records exact blockers;
[validation](results/validation.json) and [test log](results/test-log.txt) separate
successful software/data checks from unrun kettle checks.

- Passed: supplied BOM count, unique rows, unit conversion, product/packaging mass
  totals; downloaded USLCI hashes/ZIP integrity; pinned TianGong commit; full process
  catalog counts; 15 synthetic solver/BOM tests.
- Failed/unresolved: suitable processes for five materials, manufacturing evidence,
  provider closure, historical ILCD reference inconsistencies and method provenance.
- Not run for kettle: matrix solve/residual, characterization coverage, impact
  contribution sum, double-counting approval. No numerical-zero interpretation.

Seven candidates represent 762.55 g of finished mass; this is **candidate mass
coverage only**, not inventory completeness, environmental coverage or an impact
estimate. Five missing materials total 98.25 g. No dominant impact material can be
identified from mass alone. Different geography/years and omitted component/assembly
burdens prevent a defensible full factory-gate claim.

## 8. Uncertainty and sensitivity

Not calculated: no completed baseline or sourced distributions. Mean, median,
P05/P95, draw count, seed and convergence: not applicable. Do not give invented
probability intervals. Once a baseline exists, prioritize nylon grade, brass alloy,
stainless grade/recycled share, factory electricity, yields, resin formulations,
cardboard type and provider/method scenarios. Treat parameter uncertainty, geographic
or method scenarios and repeated AI-run variability separately. A future P05–P95
interval is conditional on model and chosen distributions, not unconditional certainty.

## 9. Codex and human decisions

Assistant identity: Codex/GPT-6 family; exact served model/version and reasoning/UI
settings: unknown. Run date: 2026-10-08. Human supplied study boundary, official
repositories, README requirements, USLCI download guide and final BOM. Codex inspected
sources, implemented integration/matrix validation and rejected unsupported proxies.
No independent human match approval or output verification is recorded.

[Decision log](docs/DECISIONS.md) records consequential requirements and corrections
without private messages or credentials. No result from classmates was supplied.
The attached README requirement document defines reporting fields; BOM CSV supplies
input data. Neither is treated as permission to invent missing values.

## 10. Independent and revised runs

This is the first independently prepared access/modeling run; no numerical baseline,
Git tag or previous completed-run commit is available. Adding the BOM and USLCI
source corrected missing-input/access evidence; it did not revise a numerical result.
Prior/revised GWP, absolute/percentage differences and predicted effect: not
applicable. Preserve `results/independent-baseline` when a complete first model is
calculated; future revisions must use a new directory and identify one changed
decision, prior commit and both numerical results.

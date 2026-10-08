# Implementation plan and access assessment

Prepared 2026-10-08 before calculation implementation.

## 1. Establish data access

Inspect the five requested official repositories at exact commits recorded in
`data/source_manifest.json`. GitHub reads work. The assignment site, TianGong
platform/Soda4LCA node, and LCA Commons returned proxy CONNECT 403, before an
application response. That does not establish a website outage or invalid login.

The historical `data/tiangong_lca_data` checkout contains actual ILCD XML: 4,132
processes, 96,820 flows, 25 LCIA methods, 269 flow properties, and 54 unit groups.
Retrieve reproducibly through Git at the recorded commit; no platform account
is required for this public snapshot. Do not claim it is the current database.

`database` owns Supabase schema/migrations/governance, not a downloadable complete
inventory database. `cli` supplies search, exact process retrieval, local validation,
import/conversion and authenticated release downloads. `mcp` exposes platform tools
through STDIO/HTTP with OAuth; GLAD search separately requires a GLAD API key.
`docs` contains public setup, query, authentication, OpenAPI and export guides.

## 2. Confirm BOM and select datasets

Declared unit: one manufactured and packaged 1 L kettle. Required BOM: 12 materials,
860.8 g including packaging. Individual names and masses were not provided in the
conversation; the assignment site is blocked. Keep 12 explicitly missing rows,
not guessed material names or masses. Reject incomplete BOMs and totals outside
0.000001 g of 860.8 g. Convert g to kg by dividing by 1000.

Generate a complete historical process catalog with UUID, dataset version,
geography, reference year, reference product, reference amount/unit, process type,
source URL and file digest. Keyword results are candidates, never verified matches.
Review grade, manufacturing route, geography/year, reference property/unit, scope,
allocation and sources. Retain original records. An accepted proxy needs an explicit
justification and sensitivity assessment; no silent name-based provider linking.

## 3. Build the cradle-to-gate network

Include raw materials, component transformations, assembly and packaging.
Manufacturing inputs, yields/scrap and electricity must come from the assignment
or documented evidence. Do not derive them from final product mass or set them
to zero. Exclude consumer operation and product disposal. Production waste treatment
may still be needed within manufacturing; the product end-of-life exclusion does
not automatically exclude it. Transport inclusion requires an explicit scope decision.

Use one reference output per normalized process. The initial implementation rejects
multi-output/allocation-ambiguous processes. Resolve each non-elementary exchange
to an explicit provider UUID/version; resolve all background dependencies or declare
the model incomplete. Aggregated cradle-to-gate inventories must not be linked to
their upstream inputs again. Product flow UUID alone does not identify a supplier.

## 4. Implement the three operations

Rows of square A are reference products, columns are processes. Normalize each
column to one reference-output unit: A[j,j]=1; A[i,j] decreases by the provider
input per output of j, expressed in i's reference unit. Solve A s=f using SciPy
sparse factorization, never explicit inversion. Reject singular/nonfinite networks,
negative activities and residual failures for the supported attributional model.

B rows are exact elementary flow identity, dataset version, unit, direction and
compartment/location; columns match A. Output emissions and input resource
withdrawals are positive burdens in separate direction-specific rows. Any signed
credits need an explicitly extended, reviewed model. Then g=B s.

C rows are impact categories and columns exactly match B. Match characterization
by flow UUID/version, direction, unit and applicable geography, not name alone.
Normalize units using flow -> reference property -> unit group. A missing factor
is not zero: require explicit reviewed non-characterized-flow evidence or block.
Then h=C g. Do not combine a total climate category with its fossil/biogenic/LULUC
subcategories. The archived climate method labels GWP100/IPCC 2021 but also contains
an IPCC 2013 source label; resolve this discrepancy before approving C.

Build material contribution demand vectors and solve them using the same A/B/C.
Their sum must equal the total; retain assembly and other burdens as separate groups.

## 5. Validate and report

Check actual ILCD extraction, reference-chain units, BOM counts/mass, supplier
closure, allocation, CF coverage, matrix residual and contribution reconciliation.
Use synthetic networks only for algorithm unit tests, clearly labelled; never
report their outputs as kettle results. Publish numerical kettle GWP only after
all required inputs and the reviewed method are available.

Prepare a GitHub-ready project in the existing `/workspace/jy` checkout. Keep raw
database downloads ignored, preserve citations and hashes, and document commands.
Do not push/publish remotely without a user instruction to do so. Until BOM,
foreground inventory, provider links and reviewed CFs are supplied, report a
blocked analysis with null impacts, rather than a fabricated or partial total.

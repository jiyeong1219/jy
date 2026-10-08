# Curated decision log

2026-10-08, first independent preparation; no private messages or credentials.

1. User requested official TianGong/USLCI investigation before implementation, a
   12-material/860.8 g BOM and cradle-to-gate A/B/C operations without invented values.
2. Initial assignment-site request failed at the proxy. This conversation had no
   individual BOM rows, so the initial plan explicitly left them missing.
3. All five official TianGong repositories were read/pinned. Contrary to assuming
   only code was present, `data` contained real historical ILCD inventories.
4. The README requirement attachment added ten reporting sections and confirmed
   BC1/product 723 g + packaging 137.8 g, but did not supply individual material rows.
5. User supplied the official USLCI guide. Downloaded the accessible 2025 JSON-LD
   and 2019 ILCD files, retained their exact hashes, and distinguished unavailable
   newer LCA Commons/Box links. Old ILCD is not represented as current USLCI.
6. User supplied the BOM CSV. It replaced explicit missing-input rows; validation
   now passes all three mass totals. Seven real candidate inventories retrieved,
   five materials lack suitable candidates in the searched catalogs.
7. Rejected nylon yarn/ink as nylon resin, luggage as PC resin, silicone monomer as
   cured elastomer, and an economic copper bridge as physical copper production.
   Brass composition was not invented. Candidate proxies remain unapproved.
8. Parser diagnostics exposed a mistaken singular `flowPropertyInformation` path;
   corrected to the ILCD `flowPropertiesInformation` element and reran catalogs.
   Remaining missing-file/version findings are preserved, not silently repaired.
9. Source climate method has conflicting source-year labels and a completeness
   count discrepancy. Extracted it without changing factors; no approved C is built.
10. Implemented sparse matrix operations and defensive review gates; synthetic
    tests are kept separate from the uncalculated kettle study. No result from a
    different student/run was used, and no impact baseline was revised.

Initial plan: [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md). Later source/BOM
additions resolve its initial access/input gaps partly; its initial missing-BOM
assessment is historical, not the current state in README/results/status.json.

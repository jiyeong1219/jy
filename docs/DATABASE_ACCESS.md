# Verified database access and outstanding actions

Access assessment date: 2026-10-08. GitHub organization and all five requested
repository reads succeeded. Local pinned source manifests are authoritative for
this run; links below explain the retrieval route, not successful platform access.

## TianGong

1. Historical data: `python scripts/workflow.py fetch` checks out the exact `data`
   commit in `data/raw/tiangong`. The tool refuses an existing different/dirty checkout.
   No account/token is needed for public Git reads. This is actual ILCD XML, not
   merely source code. The maintained archive README directs current users elsewhere.
2. Current platform: https://lca.tiangong.earth/ . Open the desired dataset, use
   **Export**, select offered options, and save the downloaded dependency closure.
   Available current export formats were not observed here, so none is promised.
3. CLI: Node `>=24.19.0 <25`; official development uses pnpm `11.24.0`. The published
   consumer package is package-manager-neutral. Installed/tested `@tiangong-lca/cli`
   `0.1.27` from npm in this environment; local auth reports `login-required` (exit 1).

```bash
# On the user's trusted local terminal, with the browser on that same machine:
pnpm dlx --package=@tiangong-lca/cli@0.1.27 tiangong-lca auth login
pnpm dlx --package=@tiangong-lca/cli@0.1.27 tiangong-lca auth doctor-auth --json
pnpm dlx --package=@tiangong-lca/cli@0.1.27 tiangong-lca search process --input search.request.json --json
pnpm dlx --package=@tiangong-lca/cli@0.1.27 tiangong-lca process get --id ACTUAL_UUID --version ACTUAL_VERSION --json
```

`search.request.json` contains `{"query":"polyoxymethylene production"}` (change
the search text for each missing material). Placeholder UUID/version above are not
real data and must be replaced from actual search responses. `process get` may
resolve to another accessible version; verify requested and resolved versions.
Official Production includes public connection configuration; no `.env` is needed.
OAuth 2.1/S256 PKCE opens the user's browser with the registered callback
`http://127.0.0.1:49191/oauth/callback`. This cloud machine and a user's browser are
different hosts; normal local sign-in is not claimed to work across that boundary.
Do not send passwords, authorization codes, access/refresh tokens or session files.

The CLI supports `release current`, `release artifact-download --artifact-id ...
--output ...`, `release calculation-bundle --package-id ... --output ...` and
`release calculation-artifact ...`. These need actual published package/artifact
IDs and permitted access. They are documented, not executed here. Never invoke
prepare/upload/publish to retrieve data. Private release operations require an
authorized role; no service-role key is a normal consumer prerequisite.

MCP is a separate tool server, not necessary for the Python archive route. Its
README installs `@tiangong-lca/mcp-server` using pnpm; STDIO uses dotenv and configured
Supabase issuer/key. Remote HTTP requires compatible host OAuth and an admitted
public client. Only GLAD search additionally needs `GLAD_API_KEY` and
`GLAD_API_BASE_URL`. No TianGong/Supabase/GLAD variable names were found exported in
this machine; the installed CLI also confirms a missing local OAuth session.

## USLCI

Official guide provided by the user:
https://github.com/FLCAC-admin/uslci-content/blob/dev/docs/release_info/release-downloads.md

- Retrieved/hash-verified: 1.2025-06.0 JSON-LD, FY19.Q2.01 ILCD from the linked
  GitHub files. `scripts/uslci.py fetch` pins the repository commit and checks
  SHA-256, byte size and ZIP integrity. Downloads require no account here.
- Latest listed: 1.2026-09.0. JSON-LD link:
  https://www.lcacommons.gov/lca-collaboration/National_Renewable_Energy_Laboratory/USLCI_Database_Public/datasets
  (blocked by proxy). No ILCD link for that release. A `.zolca` file is a different
  openLCA database format, not directly an ILCD XML archive or a NumPy matrix.
- FY21.Q3.01 ILCD link: https://app.box.com/s/iisvem9o9l8k8198h311z8whpf0uu8cl
  (blocked by proxy). Do not claim a downloaded 2021 dataset.
- ILCD export loses exchange comments per the official guide; use native JSON-LD
  where possible. Retrieved JSON-LD retains default-provider references, formulas,
  allocation information, comments and source/license notices.
- Citation: “U.S. Life Cycle Inventory Database.” National Renewable Energy
  Laboratory, release 1.2025-06.0 (or FY19.Q2.01 for that archive), accessed
  2026-10-08, https://www.lcacommons.gov/nrel/search . Include exact source hash.

## Concrete blockers and user actions

The proxy rejected CONNECT with 403 for the assignment domain, `lca.tiangong.earth`,
`lcadata.tiangong.world`, `www.lcacommons.gov`, `www.nrel.gov` and `app.box.com`.
These are network-policy observations, not application authentication failures.
No auto-review rejection occurred; ordinary and escalated assignment requests both
received the same proxy response. Network settings were not broadened by this project.

Allow the destinations needed for your chosen retrieval route in environment
network settings. Alternatively, export permitted complete datasets in your browser
and supply the files with metadata/licenses. Required missing materials are brass,
specified nylon grade, POM, PC and cured silicone. Other seven candidates still
need grade/geography/formulation decisions and upstream closure.

Provide the assignment's manufacturing inventory (or sourced kettle-specific
conversion services, yields/scrap and assembly electricity), factory location/year,
and an approved GWP100 method with flow mappings/dependency files. The website and
README/BOM attachments currently do not provide those numerical manufacturing inputs.
An export of only final impacts would not enable the required A/B/C reconstruction.

Current-database authentication details for LCA Commons/Box could not be inspected
through the blocked sites. Do not invent their login/API procedure. Public GitHub
archive download works independently, so no token is requested for that route.

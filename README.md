# MHAO Internal Audit Management System (IAMS)

Design and code for an Internal Audit Management System on SharePoint, Power Apps, Power Automate and Power BI.

**Sanitised copy.** Email addresses are replaced by `user@example.com` and the tenant name by `YOURTENANT`. Follow [INSTALL.md](INSTALL.md): the scripts fill in your site, lists and addresses. Note: the `.msapp` binary and the user-manual PDF are the published originals and may still contain the source site address in their embedded settings; the install guide re-points them.

| Folder | Contents |
|---|---|
| `sharepoint/` | `Provision-IAMS.ps1` (PnP PowerShell provisioning of lists, libraries, groups), `iams_spec.py` (list/column spec), `build.py`, `build_import.py`, `tmpl.py` (generators) |
| `powerautomate/solutions/IAMSAllFlows` | Unpacked solution with all 24 current flows (WF0 x7, WF1, WF1a, WF2a-d, WF3, WF4, WF5, WF5b-d, WF6, WF7, WF9, GetMyRole, Child-WriteAuditLog), exported from the live environment; lists are tokens, filled in by `Prepare-FlowSolution.ps1` |
| `powerautomate/generators/` | Python that built the first solution packages (history; the exported solution above is the current version) |
| `powerautomate/flows.md` | Flow design notes |
| `powerbi/` | PBIP project (semantic model TMDL + report) and the generators |
| `powerapps/canvas-app/` | The published canvas app (`.msapp`) and its readable screen source (`Src/*.pa.yaml`) |
| `specs/`, `data/`, `docs/` | Design specs, data model and import templates, user manual (PDF + source), UAT notes |
| `INSTALL.md` | **Start here to install on another tenant** |

Flows are in test mode: approvals and e-mails go to one address. Point them at real roles before production.

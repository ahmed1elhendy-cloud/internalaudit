# MHAO Internal Audit Management System (IAMS)

Design and code for an Internal Audit Management System on SharePoint, Power Apps, Power Automate and Power BI.

**Sanitised copy.** Email addresses are replaced by `user@example.com` and the tenant name by `YOURTENANT`. Replace them (and the SharePoint site URL) before importing anywhere.

| Folder | Contents |
|---|---|
| `sharepoint/` | `Provision-IAMS.ps1` (PnP PowerShell provisioning of lists, libraries, groups), `iams_spec.py` (list/column spec), `build.py`, `build_import.py`, `tmpl.py` (generators) |
| `powerautomate/solutions/Batch1-8` | Unpacked solution packages with the IAMS-WF* flow definitions (WF1a, WF2a-d, WF4, WF5, WF5c, WF5d, WF6, WF7, WF9) |
| `powerautomate/generators/` | Python that builds the solution packages |
| `powerautomate/flows.md` | Flow design notes |
| `powerbi/` | PBIP project (semantic model TMDL + report) and the generators |
| `powerapps/` | `scrResources_ResourceCentre.yaml` - Resource Centre screen, paste into a blank screen named `scrResources` in Studio |

Flows are in test mode: approvals and e-mails go to one address. Point them at real roles before production.

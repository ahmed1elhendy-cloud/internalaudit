# Keeping this repo current ("push to GitHub")

Run these refreshes, then sanitise and push. Each step overwrites the matching folder.

| Area | How to refresh | Repo folder |
|---|---|---|
| SharePoint schema | Read each list's fields over REST (`/_api/web/lists/.../fields`) and compare with `sharepoint/live_schema.txt`; update `sharepoint/iams_spec.py`, then `python sharepoint/build.py` (regenerates `Provision-IAMS.ps1` and `data/MHAO_IAMS_Data_Model.xlsx`) | `sharepoint/`, `data/` |
| Power Automate | Solutions > `IAMSAllFlows` > add any new flows (Add existing > Automation > Cloud flow) > Export (unmanaged) > unpack into `powerautomate/solutions/IAMSAllFlows`; replace list IDs with `@@LIST:<name>@@` tokens using `powerautomate/list-map.json` (add new lists to the map) | `powerautomate/` |
| Power Apps | Studio > File > Save as > Download a copy; unpack `.msapp` (zip) and copy `Src/*.pa.yaml`, `Header.json`, `Properties.json` | `powerapps/canvas-app/` |
| Power BI | Copy the PBIP folder (`IAMS.Report`, `IAMS.SemanticModel`) | `powerbi/` |
| Docs / specs | Copy changed files from the project docs | `docs/`, `specs/` |

**Sanitise before every push:** tenant name -> `YOURTENANT`, emails -> `user@example.com`, local paths, list GUIDs -> tokens. Then check:
`grep -rIn "<real tenant>\|<real domain>" . --exclude-dir=.git` must return nothing (the `.msapp` and the manual PDF are binaries and are exempt).

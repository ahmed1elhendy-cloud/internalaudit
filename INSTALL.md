# Installing IAMS on a new tenant

Everything needed is in this repo. Plan about half a day. Do it first on a **test site**.

## 0. What you need
- A SharePoint site (communication or team site) for the system, and Site Owner rights on it.
- A Power Platform environment where you can create apps and flows (a solution-aware environment with Dataverse; the flows are imported as a solution).
- PowerShell 7 with `PnP.PowerShell` (`Install-Module PnP.PowerShell`) and an Entra app registration for it (`Register-PnPEntraIDAppForInteractiveLogin`). You will need its **ClientId**.
- Power Apps Studio (browser), Power BI Desktop (optional, for the dashboards), Python 3 (only if you change the spec).
- Licences: SharePoint, Power Apps, Power Automate **Standard** connectors only (SharePoint, Office 365 Outlook, Approvals). Power BI Pro for viewers.

## 1. Create the SharePoint lists (about 10 min)
```powershell
cd sharepoint
.\Provision-IAMS.ps1 -SiteUrl https://<tenant>.sharepoint.com/sites/<YourSite> -ClientId <app-id>
```
Creates 18 lists, 6 libraries (including the questionnaire module and the Knowledge Documents library / Knowledge Index list), all columns, versioning, the seven IA_* groups, the reference configuration keys and the Resource Centre catalogue. It is safe to re-run. The schema comes from `iams_spec.py`; `live_schema.txt` is a dump of the live test site for comparison.

## 2. Load reference data and roles
1. Edit the data block in `sharepoint/Import-IAMS-Data.ps1` (Entities, Departments, Audit Universe) or use `data/MHAO_IAMS_Import_Templates.xlsx` as the pattern, then run `.\Import-IAMS-Data.ps1 -SiteUrl ... -ClientId ...`.
2. Open the **IA Configuration** list and set:
   - `Role.Owner`, `Role.Manager`, `Role.Auditor`, `Role.ActionOwner`, `Role.Executive`, `Role.BUHead`, `Role.DepartmentHead` - semicolon-separated emails, written `;a@company.com;b@company.com;` (leading and trailing semicolon). The app reads these at start to decide what each user sees. A person can hold several roles.
   - `HeadOfIAEmail`, `GroupCEOEmail` - used by reminders and escalations.
   - `ReminderDays1`, `ReminderDays2`, `EscalateCEOAfterDays` if you want other thresholds.
3. Add people to the `IA_*` SharePoint groups to match (see `data/MHAO_IAMS_Roles_and_Authorities_v3_Agreed.xlsx`).
4. Upload `data/MHAO_IA_Audit_Questionnaire_Template_v1.xlsx` to the **Questionnaire Templates** library.

## 3. Import the Power Automate flows (about 30 min)
The flows are stored sanitised in `powerautomate/solutions/IAMSAllFlows`: the site address is `YOURTENANT.sharepoint.com` and every list is a token. Fill these in for your site:
```powershell
cd powerautomate
.\Prepare-FlowSolution.ps1 -SiteUrl https://<tenant>.sharepoint.com/sites/<YourSite> -ClientId <app-id> -DefaultEmail someone@company.com
```
This writes `IAMSAllFlows_ready.zip`. Then in Power Automate: **Solutions > Import solution**, choose the zip, and create a connection for each of the connection references (SharePoint, Office 365 Outlook, Approvals) when prompted. After import:
- Turn the flows **on**. Order does not matter; `IAMS-Child-WriteAuditLog` and `IAMS-GetMyRole` must be on first (others call them).
- `IAMS-WF1a-PlanApproval`, `IAMS-WF3-FindingsApproval` and `IAMS-WF5d-ReviewOutcomeNotices` send approvals and emails to the `-DefaultEmail` address in test mode. Open each, and replace it with the real role lookup (the address is the one you passed) before go-live.
- Check that no flow shows a connection warning. A flow that was edited in the portal will show the new owner as its connection owner.

The flow behaviour is documented in `powerautomate/flows.md` and `specs/MHAO_IAMS_Flow_Specifications.md`.

## 4. Import the Power Apps canvas app (about 30 min)
1. Power Apps Studio > **Open** > **Browse** and select `powerapps/canvas-app/MHAO Internal Audit Portal.msapp` (or use **Apps > Import canvas app** with a zip you make from it). The readable source of each screen is in `powerapps/canvas-app/Src/*.pa.yaml` for review.
2. **Data**: the app still points at the original site. Remove the SharePoint data sources and add the new site's lists with the SharePoint connector (list titles are identical, so formulas keep working): Annual Audit Plan, Audit Engagements, Audit Findings Register, Audit Questionnaires, Audit Trail, Audit Universe, Corrective Action Tracker, Departments, Engagement Milestones, Entities, Evidence Repository, Follow-Up Reviews, IA Configuration, Knowledge Documents, Knowledge Index, Questionnaire Files, Questionnaire Items, Questionnaire Sections, Questionnaire Templates, Questionnaire Uploads, Reports Library, Risk Register, Self Assessment Register, Audit Working Papers.
3. **Flows**: open the Power Automate pane in Studio and re-add the flows the app calls (`IAMS-GetMyRole`, `IAMS-WF9-UploadEvidence`, `IAMS-WF6-DueDateExtension`, `IAMS-WF1a-PlanApproval`, `IAMS-WF2d-QuestionnaireUploadImport`). Search for `.Run(` in the screens to find every call site.
4. **Hard-coded site address**: search the app for `YOURTENANT.sharepoint.com` / the old tenant name and replace with your site URL. There are five places: scrQuestionnaires (template library link), scrQuestionnaireFill (edit form), scrQuestionnaireReview (display form), scrReports (two list links).
5. Save, **Publish**, then share with the audience (and give them SharePoint access, see step 2).

## 5. Power BI (optional)
Open `powerbi/IAMS.pbip` in Power BI Desktop (developer mode). In **Transform data > Manage parameters** set `SiteUrl` to your site, then refresh and sign in. Details and the dashboard list are in `powerbi/BUILD_NOTES.md` and `specs/MHAO_IAMS_PowerBI_Spec.md`.

## 6. Resource Centre documents
Upload the documents to the **Knowledge Documents** library (the user manual is in `docs/user-manual/`). In the **Knowledge Index** list paste each file's link into `DocLink`. Rows with no link show as "coming soon" in the app.

## 7. Smoke test
1. Create a plan item, submit for approval, approve it: an engagement, folders and milestones appear (WF1/WF1a).
2. In the app: create a finding, move it through the stages (WF3), add an action, upload evidence (WF9), validate it (WF5/WF5b/WF5c).
3. Issue a questionnaire, answer it as an auditee, review it (WF2a-d).
4. Confirm the `Audit Trail` list receives entries and the Power BI report refreshes.

## Troubleshooting
- *A flow cannot find a list*: Prepare-FlowSolution stops with the list names that are missing. Run step 1 again.
- *The app shows blank galleries*: check `Role.*` values and that the data sources were re-added to the new site.
- *Provision-IAMS fails on a column*: a lookup target may be missing; the script creates lists first, then columns, so re-run it.
- *Change the schema*: edit `sharepoint/iams_spec.py` and run `python build.py` in `sharepoint/` to regenerate `Provision-IAMS.ps1` and `data/MHAO_IAMS_Data_Model.xlsx`.

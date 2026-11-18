# MHAO IAMS - Power Apps Specification and Power Fx

One canvas app, `MHAO Internal Audit Portal`, with a tablet layout (1366x768) for desktop users and a phone layout app (`MHAO IA Fieldwork`) for the Fieldwork screen. Data sources are the SharePoint lists in `MHAO_IAMS_Data_Model.xlsx`, plus one flow for role lookup.

Column names below are the **internal names** from the workbook. Power Apps shows display names in the formula bar but accepts either; check IntelliSense after you connect the lists.

## 0. Data sources to add

IA_Entities, IA_Departments, IA_AuditUniverse, IA_RiskRegister, IA_AuditPlan, IA_Engagements, IA_Milestones, IA_Findings, IA_ActionPlans, IA_FollowUps, IA_CSARegister, IA_Config, IA_AuditLog (read only), Office365Users, and flows `IAMS-GetMyRole`, `IAMS-WF6-Extension`, `IAMS-GenerateReport`, `IAMS-UploadEvidence`.

Settings: Advanced -> **Data row limit = 2000**. Turn on "Use non-blocking OnStart rule" and "Explicit column selection".

## 1. Role detection (important)

SharePoint groups cannot be read directly from Power Apps with Standard connectors. Use a small flow `IAMS-GetMyRole` (see WF8 in the flow specifications). A person can hold several roles at once, so the flow returns **all** of them.

- Trigger: Power Apps (V2), input `Email` (text).
- Action `HTTP`: Send an HTTP request to SharePoint, GET `_api/web/siteusers/getbyemail('@{triggerBody()['text']}')/groups?$select=Title`.
- Compose `Raw`: `concat(if(contains(string(body('HTTP')),'IA_Owners'),'Owner,',''), ... one if() per group ...)`; Compose `Roles`: `if(empty(outputs('Raw')),'None',concat(',',outputs('Raw')))`.
- Respond to Power Apps: `roles` (text), for example `,DepartmentHead,ActionOwner,`.

Roles: Owner, Manager, Auditor, ActionOwner, Executive, BUHead, DepartmentHead (groups IA_Owners, IA_Managers, IA_Auditors, IA_ActionOwners, IA_Executives, IA_BUHeads, IA_DepartmentHeads).

Security note: the roles are only for **showing/hiding UI**. Real protection is the SharePoint permissions and the flows. Never rely on a hidden button.

## 2. App.OnStart

```powerfx
Set(varMe, User());
Set(varToday, Today());
Set(varYear, Year(Today()));
Set(varRoles, IfError(IAMSGetMyRole.Run(User().Email).roles, "None"));   // flow 'IAMS-GetMyRole' appears as IAMSGetMyRole (hyphens removed); check the name in the Power Automate pane

// Role flags: a person can hold several. Inheritance: Owner includes Manager, Manager includes Auditor.
Set(varIsOwner,          "," & "Owner" & "," in varRoles);
Set(varIsManager,        ("," & "Manager" & "," in varRoles) || varIsOwner);
Set(varIsAuditor,        ("," & "Auditor" & "," in varRoles) || varIsManager);
Set(varIsActionOwner,    "," & "ActionOwner" & "," in varRoles);
Set(varIsExec,           "," & "Executive" & "," in varRoles);
Set(varIsBUHead,         "," & "BUHead" & "," in varRoles);
Set(varIsDeptHead,       "," & "DepartmentHead" & "," in varRoles);
Set(varIsMgmt,           varIsActionOwner || varIsBUHead || varIsDeptHead);      // management side
Set(varHasAccess,        varRoles <> "None");

Concurrent(
    ClearCollect(colEntities, SortByColumns(Filter(IA_Entities, Active = true), "Title")),
    ClearCollect(colDepartments, Filter(IA_Departments, Active = true)),
    ClearCollect(colConfig, IA_Config)
);

// Palette
Set(varBrand, RGBA(31,56,100,1));
Set(varGreen, RGBA(46,160,67,1));
Set(varAmber, RGBA(230,162,0,1));
Set(varRed,   RGBA(207,34,46,1));
Set(varGrey,  RGBA(110,119,129,1));

// Selected-record holders used by the New/Edit forms (typed from a real record)
Set(varEngItem, First(IA_Engagements));
Set(varPlanItem, First(IA_AuditPlan));
Set(varFindingItem, First(IA_Findings));
Set(varActionItem, First(IA_ActionPlans));
Set(varFollowUpItem, First(IA_FollowUps))
```

Landing screen logic (`App.StartScreen` or Screen OnVisible): no roles -> no-access screen; Owner/Manager/Auditor/Executive -> Dashboard; management roles only (ActionOwner, BUHead, DepartmentHead) -> Findings or Actions.

```powerfx
If(!varHasAccess, Navigate(scrNoAccess), varIsAuditor || varIsExec, Navigate(scrDashboard), Navigate(scrActions))
```

Shared header: title, user name `varMe.FullName`, role badge `varRoles`, and one navigation menu (`ddNav`). The menu shows only the screens the person may use. Menu Items:

```powerfx
Filter(
  Table(
    {Value: "Dashboard",   Show: true},
    {Value: "Plan",        Show: varIsAuditor || varIsExec},
    {Value: "Engagements", Show: varIsAuditor || varIsExec},
    {Value: "Findings",    Show: true},
    {Value: "Actions",     Show: true},
    {Value: "Follow-Up",   Show: varIsAuditor || varIsExec || varIsBUHead || varIsDeptHead},
    {Value: "Fieldwork",   Show: varIsAuditor},
    {Value: "Reports",     Show: true}
  ),
  Show
)
```

| Screen | Visible to |
|---|---|
| Dashboard | everyone with a role (management roles see their own scope) |
| Plan, Engagements | Owner, Manager, Auditor, Executive |
| Findings, Actions | everyone with a role (rows are limited by SharePoint item permissions) |
| Follow-Up | Owner, Manager, Auditor, Executive, BU Head, Department Head |
| Fieldwork | Owner, Manager, Auditor |
| Reports | everyone with a role (management roles see issued reports only) |
| IA Configuration | Owner and Manager (edit) |

"+ New" and "Edit" buttons: visible to `varIsAuditor` (this includes Manager and Owner) for Findings, Actions and Follow-Ups; to `varIsManager` for Engagements and the Plan. Executives, BU Heads, Department Heads and Action Owners never see them (Action Owners update their own actions and respond to findings through the response screens).

Plan approval buttons: "Submit for review" (`varIsAuditor` or planner, sets `Pending Manager Review`); approval itself happens in Teams/Outlook through WF1a.

## 3. Delegation rules (read before writing any Filter)

- **Delegable on SharePoint:** `=`, `<>`, `<`, `>`, `<=`, `>=`, `And`, `Or`, `Not`, `StartsWith`, `Sort`, `SortByColumns`, `LookUp`, equals on `.Value` of Choice, equals on `Lookup.Id`, `Person.Email = x`.
- **Not delegable:** `CountRows`, `Sum`, `Average`, `Distinct`, `In`, `Search` on lookup/choice columns, `Len`, `Year()` on a column.
- Therefore **KPI tiles must not be built with CountRows over big lists** - they silently cap at 2000 rows. Use an embedded **Power BI tile** (Power BI tile control) for the dashboard KPIs, or have a nightly flow write the KPI values to `IA_Config`. Where counts are small and bounded (e.g. "my open actions" per user), CountRows(Filter(...)) is fine.
- Filter by **date range on a date column** instead of `Year(DueDate)`: `PlannedStart >= Date(varYear,1,1) && PlannedStart <= Date(varYear,12,31)`.
- Index columns used in filters (already flagged in the workbook).

## 4. Screens

### 4.1 scrDashboard - Executive Dashboard

Layout: header, row of 6 KPI cards, row of 5 navigation buttons, one embedded chart/list.

KPI cards: add a **Power BI tile** per card (or one report page tile) pointing at the Executive dashboard (dashboard 1). Fallback from config values written by a nightly flow:

```powerfx
Text(Value(LookUp(colConfig, Title = "KPI_OpenFindings").ConfigValue))
```

Small lists that can be live:

```powerfx
// My open actions (bounded by owner)
CountRows(Filter(IA_ActionPlans, ActionOwner.Email = varMe.Email, ActionStatus.Value <> "Closed"))
```

Critical findings table (Items):

```powerfx
Filter(IA_Findings, Rating.Value = "Critical", FindingStatus.Value <> "Closed", WorkflowStage.Value = "Issued")
```

Navigation: `Navigate(scrPlan)` etc. with `Visible` as in section 2.

### 4.2 scrPlan - Annual Audit Plan

Controls: year dropdown `ddYear` (Items `[varYear-1, varYear, varYear+1]`), entity dropdown `ddEntity` (Items `colEntities`, with an "All" option via `Table({Title:"All"}, colEntities)`), status dropdown, view toggle (List / Calendar / Gantt), gallery, "New audit" button.

Gallery Items:

```powerfx
SortByColumns(
  Filter(
    IA_AuditPlan,
    PlannedStart >= Date(ddYear.Selected.Value,1,1),
    PlannedStart <= Date(ddYear.Selected.Value,12,31),
    (ddEntity.Selected.Title = "All") || Entity.Id = ddEntity.Selected.ID,
    (ddStatus.Selected.Value = "All") || AuditStatus.Value = ddStatus.Selected.Value
  ),
  "PlannedStart", SortOrder.Ascending)
```

Row fields: AuditRef, Title, Entity.Value, AssignedAuditor.DisplayName, dates, `BudgetHours`, status pill colour:

```powerfx
Switch(ThisItem.AuditStatus.Value,
  "Completed", varGreen, "Deferred", varAmber, "Cancelled", varGrey,
  "In Progress", varBrand, "Fieldwork", varBrand, "Reporting", varBrand, varGrey)
```

Resource allocation panel (small data - plan items for the selected year only):

```powerfx
// Items of a Data table or chart (group by a text column, not a person record)
AddColumns(
  GroupBy(
    AddColumns(
      Filter(IA_AuditPlan, PlannedStart >= Date(varYear,1,1), PlannedStart <= Date(varYear,12,31)),
      "Auditor", AssignedAuditor.DisplayName),
    "Auditor", "rows"),
  "TotalHours", Sum(rows, BudgetHours))
```
(Fine up to 2000 plan items per year.)

New/Edit form (`frmPlan`, DataSource IA_AuditPlan): auto risk score when a Universe area is picked:

```powerfx
// Default for RiskScore data card
If(IsBlank(dcArea.Selected), 0, dcArea.Selected.RiskScore)
```

Submit button (Manager+ only): `OnSelect = SubmitForm(frmPlan)`, and `OnSuccess = Notify("Saved", NotificationType.Success)`. Approval status is changed only by Owner:

```powerfx
Patch(IA_AuditPlan, ThisItem, {ApprovalStatus: {Value:"Approved"}})   // Visible: varIsOwner && ThisItem.ApprovalStatus.Value="Pending Approval"
```
Patching that value triggers WF1.

Calendar view: Power Apps calendar controls are not in modern controls by default; use a monthly gallery or embed the Power BI gantt (recommended).

### 4.3 scrEngagement - Engagement Management

Access: gallery of engagements the user can see. Auditors see only their own:

```powerfx
If(varIsManager,
  Filter(IA_Engagements, Stage.Value <> "Closed"),
  Filter(IA_Engagements, Stage.Value <> "Closed", LeadAuditor.Email = varMe.Email))
```
(Team members: also run `Filter(IA_Engagements, Stage.Value <> "Closed", Concat... )` - multi-person columns cannot be filtered delegably; rely on SharePoint folder/item permissions to limit what the user sees, or show only lead-auditor items in the gallery and a separate "My team engagements" tab built with `Filter(IA_Engagements, Stage.Value <> "Closed")` - the list is small.)

Detail view: `varEng = gal.Selected`. Tabs (use a `varTab` variable): Overview, Scope & Objective, Team, Milestones, Working Papers, Findings.

Milestones tab: `Filter(IA_Milestones, Engagement.Id = varEng.ID)` with status pill; mark complete:

```powerfx
Patch(IA_Milestones, ThisItem, {MilestoneStatus:{Value:"Complete"}, CompletedDate: Today()})
```

Working Papers tab: button `Launch(varEng.EngagementFolderUrl.Url)`; do not load the library into the app.

Stage advance (Manager+): `Patch(IA_Engagements, varEng, {Stage:{Value:"Fieldwork"}})`.

### 4.4 scrFieldwork - Fieldwork (phone app)

Same data source set, portrait layout: three large buttons - **Observation**, **Evidence**, **Walkthrough/Test**.

- Observation: form to IA_Findings in `Draft` stage. `Patch(IA_Findings, Defaults(IA_Findings), {Title: txtTitle.Text, Engagement:{Id: varEng.ID, Value: varEng.Title}, Entity: varEng.Entity, Observation: txtObs.Text, RootCause: txtRC.Text, Rating:{Value: ddRating.Selected.Value}, WorkflowStage:{Value:"Draft"}})`
  Pass the lookup as `{Id: varEng.ID, Value: varEng.Title}`.
- Evidence: Add picture + Attachments control; collection `colEvidence`; Save button calls the upload flow in a loop:

```powerfx
ForAll(colEvidence As f,
  IAMSUploadEvidence.Run(varEng.EngagementID, ddEvType.Selected.Value, f.Name, f.Value, Coalesce(varActionId, 0)))
```
The flow decodes `base64ToBinary()` and creates the file in `IA_Evidence/<EngagementID>/<EvidenceType folder>`. Cap file size around 20 MB; for larger evidence upload through SharePoint directly.
- Walkthrough / sample test: store as notes + attached files into the matching evidence sub-folder (`Walkthroughs`, `Samples`, `Testing`), with a working-paper number text input. Keep a "Saved offline" collection via `SaveData(colDraftObs, "draftObs")` and `LoadData` in `OnStart`, flushed with `Connection.Connected`.

### 4.5 scrFindings - Findings Management

Gallery Items by role:

```powerfx
Filter(IA_Findings,
  (varIsManager) ||
  (varIsAuditor && Engagement.Id in colMyEngagementIds) ||        // small collection built in OnVisible
  (varIsMgmt && WorkflowStage.Value = "Issued"),                  // SharePoint item permissions already limit rows to own department/entity,
  (ddRating.Selected.Value = "All") || Rating.Value = ddRating.Selected.Value,
  (ddStatus.Selected.Value = "All") || FindingStatus.Value = ddStatus.Selected.Value)
```
(`in` is not delegable; keep it only on a small list, or drop the Auditor line. Management roles (Action Owner, BU Head, Department Head) have no list-level permission, so SharePoint returns only the findings they were granted at item level when the finding was issued.)

Workflow stage tracker: horizontal stepper bound to `ThisItem.WorkflowStage.Value`.

Buttons by stage and role:

| Button | Visible | OnSelect |
|---|---|---|
| Submit for review | `varIsAuditor && stage="Draft"` | `Patch(IA_Findings, sel, {WorkflowStage:{Value:"Manager Review"}})` |
| Respond (management) | `varIsMgmt && stage="Management Response"` | save `ManagementResponse`, `AgreementStatus`, `DueDate`, then set stage `Audit Review` |
| Complete audit review | `varIsAuditor && stage="Audit Review"` | stage `HoIA Approval` is set by the flow after approval; button only requests |
| Issue | n/a - done by WF3 after HoIA approval | |

All approvals (manager, HoIA) happen in Teams/Outlook via the flow. The app only moves the finding into the stage that starts the approval.

Related actions: `Filter(IA_ActionPlans, Finding.Id = sel.ID)` with "Add action" form. When creating an action, set `FindingRating: {Value: sel.Rating.Value}` and `Entity: sel.Entity`.

Request extension: `IAMSWF6Extension.Run("Finding", sel.ID, Text(dpNewDate.SelectedDate,"yyyy-mm-dd"), txtReason.Text, varMe.Email)`; show `Notify` with the returned text.

### 4.6 scrActions - Action Tracking (traffic lights)

Filters: Entity, Department, Rating (from the finding), Responsible manager, "show closed" toggle. Gallery:

```powerfx
Filter(IA_ActionPlans,
  (varIsManager || varIsExec || ActionOwner.Email = varMe.Email),
  (tglClosed.Value || ActionStatus.Value <> "Closed"),
  (ddEntity.Selected.Title = "All") || Entity.Id = ddEntity.Selected.ID)
```
(Filter by finding rating with `FindingRating.Value = ddRating.Selected.Value`; the column is copied from the finding when the action is created.)

Traffic-light icon colour (`Fill`):

```powerfx
If(ThisItem.ActionStatus.Value = "Closed", varGreen,
   ThisItem.DueDate < varToday, varRed,
   ThisItem.DueDate <= DateAdd(varToday, 30, TimeUnit.Days), varAmber,
   varGreen)
```
Label: `If(ThisItem.DueDate < varToday, "Overdue " & DateDiff(ThisItem.DueDate, varToday, TimeUnit.Days) & "d", "Due in " & DateDiff(varToday, ThisItem.DueDate, TimeUnit.Days) & "d")`

Owner update panel: slider `CompletionPct`; "Mark complete" requires evidence:

```powerfx
If(!ThisItem.EvidenceUploaded, Notify("Upload evidence first", NotificationType.Error),
  Patch(IA_ActionPlans, ThisItem, {CompletionPct:100, ActionStatus:{Value:"Complete - Awaiting Validation"}, CompletedDate: Today()}))
```
That patch triggers WF5. `EvidenceUploaded` is set by the upload flow after a file lands in the evidence folder (not by the user's checkbox).

### 4.7 scrFollowUp - Follow-Up Reviews

Gallery: `Filter(IA_FollowUps, Reviewer.Email = varMe.Email, IsBlank(Outcome))` (Manager sees all). Details show the action, owner evidence link (`Launch` to `IA_Evidence` folder), notes input. Outcome buttons:

```powerfx
Patch(IA_FollowUps, ThisItem, {Outcome:{Value:"Implemented"}, ReviewDate: Today(), TestingNotes: txtNotes.Text})
```
Same for "Partially Implemented", "Not Implemented", "Re-opened". Patching Outcome triggers WF5b which closes the action and the finding when all actions are validated. Re-open requires a note: `If(IsBlank(txtNotes.Text), Notify("Note required",NotificationType.Warning), Patch(...))`.

### 4.8 scrReports - Audit Committee Reporting

Four tiles: Quarterly IA Report, Annual IA Report, Outstanding Findings Report, Audit Plan Status. Inputs: period (quarter dropdown + year), entity (All or one).

```powerfx
Set(varBusy, true);
Set(varResult, IAMSGenerateReport.Run(ddType.Selected.Value, ddPeriod.Selected.Value, Text(ddYear.Selected.Value), ddEntity.Selected.Title));
Set(varBusy, false);
Notify("Report created: " & varResult.filename, NotificationType.Success);
Launch(varResult.url)
```
`IAMS-GenerateReport` pulls data (Get items), builds the document (Word template or HTML->PDF) and saves in `IA_Reports` with ReportType, ReportPeriod and Status `Draft`. Executives only see reports where `ReportStatus = "Issued"`.

### 4.9 scrRisk - Risk Register (linked from the dashboard)

Gallery `Filter(IA_RiskRegister, RiskStatus.Value <> "Closed", AuditArea.Id = varArea.ID)`. Heat-map: a 5x5 grid of buttons; each cell shows `CountRows(Filter(IA_RiskRegister, Likelihood = r, ImpactScore = c, RiskStatus.Value <> "Closed"))` (bounded by a small risk list; if the register exceeds 2000 items, build the heat map in Power BI).

## 5. Standards for all screens

- **Colour:** brand navy header; red/amber/green only for status; do not use colour alone - include text ("Overdue 12d").
- **Accessibility:** set `AccessibleLabel` on icons and buttons; tab order top-to-bottom; minimum 12-pt text.
- **Responsiveness:** build with containers (horizontal/vertical) and `Parent.Width` rather than fixed positions; phone app uses the portrait layout.
- **Loading:** show a spinner variable `varBusy` during any `Run`/`Patch`.
- **Errors:** after each Patch, `If(!IsEmpty(Errors(IA_Findings)), Notify(First(Errors(IA_Findings)).Message, NotificationType.Error))`.
- **Collections:** only small lookups (entities, departments, config). Never `ClearCollect` an entire large list.
- **Sharing:** share the app with the five security groups, not with individuals; give *Co-owner* to the Head of IA and one admin.

## 6. Test plan

1. Open the app as each role (create five test accounts) and confirm the landing screen, nav buttons and lists match section 2 and the Security sheet.
2. Create a plan item -> approve -> check WF1 created engagement, folders and milestones.
3. Raise a finding in the phone app, run it through all approval stages, add an action, upload evidence, mark complete, validate, and confirm the finding closes.
4. Set a DueDate in the past on a test action and run WF4 manually; confirm the traffic light is red and the escalation email goes to the test department head.
5. Load 3,000 dummy findings and confirm no screen shows a delegation warning (blue underline) on a column used in a filter.

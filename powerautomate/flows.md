# MHAO IAMS - Power Automate Flow Specifications (WF0-WF7)

Companion to `MHAO_IAMS_Data_Model.xlsx`. All flows use Standard connectors only (SharePoint, Approvals, Office 365 Outlook/Users, Microsoft Teams, Forms, Planner, see licensing notes at end).

## Build conventions (apply to every flow)

- **Solution:** build all flows inside one Power Platform solution `MHAO_IAMS` so they can be moved Dev -> Prod and use environment variables.
- **Environment variables:** `IA_SiteUrl` (site address), `IA_HeadOfIA_Email`, `IA_Admin_Email` (failure alerts).
- **Connections:** use a dedicated service account (e.g. `svc-ia-flows@mhao...`) for SharePoint actions that write `IA_AuditLog`, break permissions or update items the triggering user cannot edit. Approvals run as the flow owner.
- **Naming:** `IAMS-WF<n>-<Name>`; actions named for what they do (e.g. `Get Engagement`), never left as "Get item 2".
- **Error handling:** wrap main logic in a Scope `Try`; add Scope `Catch` (Configure run after: has failed / timed out) that emails `IA_Admin_Email` with `workflow()['run']['name']` and `result('Try')`. Scope `Finally` not required.
- **Trigger loops:** any flow that updates the item it triggered on must use a **trigger condition** so it does not re-fire (examples below), and set Concurrency Control = 1 on the trigger.
- **Audit log helper:** a child flow `IAMS-Child-WriteAuditLog` (manual trigger, inputs: SourceList, SourceItemId, EventType, Details, ByEmail) creates an item in `IA_AuditLog`. Every flow calls it on significant events.
- **Reading config:** `Get items` on `IA_Config` with `Title eq 'ReminderDays1'` etc. Never hard-code days or emails.

---

## WF0 - Reference Generator

| | |
|---|---|
| Trigger | SharePoint "When an item is created" - one flow per list (Universe, Risk Register, Audit Plan, Engagements, Findings, Action Plans, CSA Register) |
| Trigger condition | `@empty(triggerOutputs()?['body/AuditRef'])` (use the matching ref column) |
| Concurrency | 1 |

Prefixes: Universe `AU-` col `AuditAreaID`; Risk `RSK-` `RiskID`; Plan `IA-<year>-` `AuditRef`; Engagement `ENG-<year>-` `EngagementID`; Finding `FND-<year>-` `FindingID`; Action `CAPA-<year>-` `CAPAID`; CSA `CSA-<year>-` `CSAID`.

Steps
1. **Compose** `Ref` = `concat('IA-', string(triggerOutputs()?['body/PlanYear']), '-', formatNumber(triggerOutputs()?['body/ID'], '000'))` (use `utcNow('yyyy')` for lists without a year column; use `0000` for high-volume lists).
2. **Update item** the ref column with `Ref`.
3. For `IA_ActionPlans` only: if `FindingRating` is empty, Get the parent finding and set `FindingRating` = finding `Rating`.
4. Child flow WriteAuditLog (`Created`).

Notes: the ID is globally unique per list so there are no duplicates, but numbers can skip if items are deleted. Do not use the ref as the lookup key in flows; use item ID.

---

## WF1 - Audit Initiation

| | |
|---|---|
| Trigger | SharePoint "When an item is created or modified" on `IA_AuditPlan` |
| Trigger condition | `@and(equals(triggerOutputs()?['body/ApprovalStatus/Value'],'Approved'), equals(triggerOutputs()?['body/AuditStatus/Value'],'Planned'))` |
| Inputs read | plan item, Audit Universe item, Entity |

Steps (inside `Try`)
1. **Guard against duplicates:** Get items `IA_Engagements` filter `AuditPlanItem eq <plan ID>` (Top Count 1). If found -> Terminate (Succeeded).
2. **Create item** in `IA_Engagements`: Title = plan Title, AuditPlanItem Id = plan ID, Entity Id, LeadAuditor = AssignedAuditor, Stage = `Planning`, EngagementScope blank.
3. **Wait ~10 seconds** (lets WF0 write EngagementID), then **Get item** to read `EngagementID`.
4. **Create folders** (Create new folder, SharePoint):
   - `IA_WorkingPapers`: `/<EngagementID>`
   - `IA_Evidence`: `/<EngagementID>`, then subfolders `Planning`, `Walkthroughs`, `Samples`, `Testing`, `Reports`, `Management Evidence` (use Apply to each over an array).
5. **Set folder permissions** (HTTP to SharePoint action "Send an HTTP request to SharePoint"):
   - `POST _api/web/GetFolderByServerRelativeUrl('<path>')/ListItemAllFields/breakroleinheritance(copyRoleAssignments=false,clearSubscopes=true)`
   - Grant using `.../roleassignments/addroleassignment(principalid=<id>,roledefid=<id>)` to: IA_Owners (Full Control), IA_Managers (Edit), Lead Auditor and each team member (Contribute). Resolve user principal IDs with `_api/web/siteusers/getbyemail('<email>')`. Role definition IDs: query `_api/web/roledefinitions`.
6. **Create milestones** in `IA_Milestones` (Apply to each over a fixed array): Kick-off (Planned start), Walkthroughs (+14d), Fieldwork Complete (+Planned start + 70% of duration), Draft Report (Planned finish -14d), Management Responses (Draft + 10 working days), Final Report (Planned finish). Date math: `addDays(planStart, int(mul(div(duration, 100), 70)))`. Owner = lead auditor.
7. **Update plan item:** AuditStatus = `In Progress`; **update engagement** EngagementFolderUrl.
8. **Notify:** Teams "Post message in a chat or channel" to the audit team + email to Lead Auditor with links. (Optional: Planner "Create a task" per milestone.)
9. Child flow WriteAuditLog.

Caution: Step 5 gives unique permissions on two folders per audit only - fine for volume (limit is 50,000 unique scopes per list).

---

## WF2 - Questionnaire / CSA Distribution and Collection

Two flows.

**WF2a - Distribute** (Instant, triggered from Power Apps button with inputs: EntityId, DepartmentId, FormUrl, Period)
1. Get Department item -> DepartmentHead email.
2. Send email (V2) with Forms link (use one Form per CSA template; prefill via Forms "get prefilled URL" with Department/Period questions).
3. Create `IA_CSARegister` stub: Status Result blank, AssessmentPeriod, Entity, Department.

**WF2b - Collect** (Forms trigger "When a new response is submitted", one flow per Form)
1. **Get response details** (Form Id, Response Id).
2. **Compose score**: sum of numeric/rated answers: if the Form uses quiz points, use `Total points` from the response; otherwise map choice answers with a Switch to numeric values and sum, then `div(sum, maxPoints)*100`.
3. Result = `if(score>=80,'Satisfactory',if(score>=60,'Needs Attention','Unsatisfactory'))` (thresholds in `IA_Config` later).
4. **Attachments:** File Upload questions return JSON array; Apply to each -> Get file content using path -> Create file in `IA_Evidence/CSA/<CSAID>`.
5. Find the stub from 2a (filter Entity/Department/Period) else Create item; Update with Score, Result, FormResponseId, SubmittedBy (by email, `responder`), SubmissionDate, AttachmentsUrl.
6. If Result = `Unsatisfactory` -> email Audit Manager and add to Universe risk score review.
7. Dedupe: before creating, Get items filter `FormResponseId eq '<id>'`; skip if exists.

---

## WF3 - Findings Approval

| | |
|---|---|
| Trigger | SharePoint "When an item is modified" on `IA_Findings` |
| Trigger condition | stage changed to a value that needs action; keep a hidden text column `LastProcessedStage` (add it) and use `@not(equals(triggerOutputs()?['body/WorkflowStage/Value'], triggerOutputs()?['body/LastProcessedStage']))` |
| Concurrency | 1 |

Switch on `WorkflowStage`:

- **Manager Review:** Start and wait for an approval (`Approve/Reject - First to respond`) assigned to the engagement's Audit Manager (read from plan item). Approve -> stage `Management Response`. Reject -> stage `Draft`; email auditor with approver comments.
- **Management Response:** Send email + Teams message to ResponsibleManager with link to the Power Apps response screen. Create a Teams/Outlook reminder task with SLA 10 working days (calculate with a daily loop in WF4 variant or `addDays(utcNow(),14)`). When the app saves ManagementResponse + AgreementStatus + proposed DueDate, the app sets stage `Audit Review`.
- **Audit Review:** Approval to the Lead Auditor/Manager. If management `Disagreed` -> route to Head of IA for decision. Approve -> `HoIA Approval`; Reject -> back to `Management Response` with comments.
- **HoIA Approval:** Approval to Head of IA (from `IA_Config` `HeadOfIAEmail`). Approve -> stage `Issued`. Reject -> `Audit Review`.
- **Issued:** set DateIssued = today, OriginalDueDate = DueDate, FindingStatus = `Open`; notify ResponsibleManager, Department Head, Entity Head; **optional**: break item inheritance and grant ResponsibleManager + Department Head Edit/Contribute and Executives Read (this is how "own findings" is enforced).
- **Closed:** set ClosedDate.

Always: update `LastProcessedStage`, child flow WriteAuditLog (`Stage Change`, details = from -> to, approver, comment).

Rule: only Managers/Owners may move a finding to `Issued`; the app enforces by role, the flow re-checks the approver identity.

---

## WF4 - Action Reminders and Escalation

| | |
|---|---|
| Trigger | Recurrence daily, 07:00, time zone (UTC+04:00) Arabian Standard Time |
| Config | read `ReminderDays1` (30), `ReminderDays2` (15), `EscalateCEOAfterDays` (30), `GroupCEOEmail` |

Compose `Today` = `formatDateTime(convertTimeZone(utcNow(),'UTC','Arabian Standard Time'),'yyyy-MM-dd')`.

Five **Get items** actions on `IA_ActionPlans` (server-side OData filters, Top Count 5000, pagination on) - all exclude `ActionStatus eq 'Closed'`:

1. **R1:** `DueDate eq '<Today+30>' and ReminderStage eq 'None'` -> email Owner (cc Responsible Manager) -> set `ReminderStage = Reminder 30d`.
2. **R2:** `DueDate eq '<Today+15>' and ReminderStage eq 'Reminder 30d'` -> email + Teams -> `Reminder 15d`.
   (Use `le` instead of `eq` if the flow could miss a day: `DueDate le '<Today+15>' and ReminderStage eq 'Reminder 30d'`.)
3. **Overdue L1:** `DueDate lt '<Today>' and ReminderStage ne 'Escalated - Dept Head' and ReminderStage ne 'Escalated - CEO'` -> set `ActionStatus = Overdue`; lookup Finding -> Department -> `DepartmentHead` and email Dept Head + Owner; set stage `Escalated - Dept Head`; WriteAuditLog `Escalation`.
4. **Overdue L2:** `DueDate lt '<Today-30>' and ReminderStage ne 'Escalated - CEO'` -> lookup Entity -> `EntityCEO`, fallback `GroupCEOEmail`; email CEO cc Head of IA and Dept Head; set `Escalated - CEO`.
5. **Summary:** email Head of IA a daily digest only if any escalation happened (HTML table via Create HTML table).

Notes: filter on the action's `Entity` lookup column (already on the list) so you do not need extra Get item calls for CEO. Dates in OData filters must be `yyyy-MM-dd`.

---

## WF5 - Follow-Up Review

| | |
|---|---|
| Trigger | "When an item is created or modified" on `IA_ActionPlans` |
| Condition | `@and(equals(triggerOutputs()?['body/ActionStatus/Value'],'Complete - Awaiting Validation'), equals(triggerOutputs()?['body/ValidationStatus/Value'],'Not Started'))` |

1. Check evidence: Get files from `IA_Evidence/<EngagementID>/Management Evidence` filtered by `Action Id eq <ID>`. If none -> set ActionStatus back to `In Progress`, email owner "Evidence required". Stop.
2. **Create item** in `IA_FollowUps` (Finding, Action, Reviewer = FollowUpAuditor, ReviewDate = today + 10d); set ValidationStatus `Submitted`.
3. Notify Follow-up Auditor (Teams + Outlook task via Create event if wanted).
4. **Wait for auditor decision:** do not hold a flow open for weeks. Instead create WF5b below.

**WF5b - Validation outcome** Trigger: `IA_FollowUps` item modified, `Outcome` is not empty.
- `Implemented` / `Closed`: set the action `ActionStatus = Closed`, `ValidationStatus = Validated`, `CompletedDate`. Then Get items for other actions of the same finding where `ActionStatus ne 'Closed'`; if count = 0 -> set Finding `FindingStatus = Closed`, `WorkflowStage = Closed`, `ClosedDate`.
- `Partially Implemented`: ActionStatus `In Progress`, ValidationStatus `Rejected`, email owner with notes.
- `Not Implemented` / `Re-opened`: ActionStatus `Open`, Finding status `Re-opened`, ExtensionCount unchanged, notify Dept Head.
- WriteAuditLog (`Closure` / `Re-open`).

---

## WF6 - Due-Date Extension

| | |
|---|---|
| Trigger | Power Apps (V2) with inputs: ItemType (Finding/Action), ItemId, NewDueDate, Reason, RequesterEmail |

1. Get item. Validate `NewDueDate > current DueDate` (else respond with error text).
2. Approval to Audit Manager; if Finding rating is Critical/High, **sequential** second approval to Head of IA.
3. Approved: update DueDate = NewDueDate, `ExtensionCount + 1`, set OriginalDueDate if empty, reset `ReminderStage = None`. Rejected: notify requester.
4. Return "Respond to a Power App" with result text. WriteAuditLog (`Due Date Extension`, old -> new, reason, approvers).

---

## WF7 - Universe Refresh (optional)

Recurrence monthly. For each active Universe item: Get items `IA_RiskRegister` filter `AuditArea eq <id> and RiskStatus ne 'Closed'`; take the maximum `ResidualRisk` (`max()` over an array built with Select) -> update `RiskScore`; set `RiskRating` (>=15 Critical, >=10 High, >=5 Medium, else Low - confirm with MHAO methodology); recompute `NextAuditDate = addToTime(LastAuditDate, months by AuditFrequency, 'Month')`. Email Head of IA the list of areas whose NextAuditDate is past and which have no Plan item for the current year.

---

## Build order and testing

1. Create solution + env variables + child flow `WriteAuditLog`.
2. WF0 (all lists) - test by adding one item per list.
3. WF1, then WF3, WF4, WF5/5b, WF6, WF2, WF7.
4. Test with dummy entities and your own account as every role; check run history shows Succeeded and `IA_AuditLog` shows entries.
5. Turn flows on in the order above; WF4 last (it sends email to real people - point `GroupCEOEmail` at yourself during testing and set the Department Head fields to test users).

## Licensing notes

- Everything above is Standard connectors. "Populate a Microsoft Word template" (for Audit Committee reports) is a Premium connector in most tenants - the alternative is the Word Online (Business) connector's template action if your licence includes it, or generate reports from Power BI paginated reports. Confirm in your tenant before choosing.
- Approvals, Teams, Outlook, SharePoint and Forms are included with Microsoft 365 licences for flows run in the context of the M365 apps. Scheduled/instant flows used by many users may need a Power Automate per-user licence depending on your agreement; check with your M365 admin.


---

## WF8 - IAMS-GetMyRole (called by Power Apps)

| | |
|---|---|
| Trigger | Power Apps (V2); input `Email` (text) |
| Output | `role` (text): Owner, Manager, Auditor, ProcessOwner, Executive or None |

1. **Send an HTTP request to SharePoint**: GET `_api/web/siteusers/getbyemail('@{triggerBody()?['text']}')/groups?$select=Title`, header `Accept: application/json;odata=nometadata`. Run as the flow owner's connection (service account).
2. **Select** `body('HTTP')?['value']` -> `item()?['Title']` to get an array of group names `Groups`.
3. **Compose** `role` with highest precedence first:
   `if(contains(outputs('Groups'),'IA_Owners'),'Owner',if(contains(outputs('Groups'),'IA_Managers'),'Manager',if(contains(outputs('Groups'),'IA_Auditors'),'Auditor',if(contains(outputs('Groups'),'IA_ProcessOwners'),'ProcessOwner',if(contains(outputs('Groups'),'IA_Executives'),'Executive','None')))))`
4. **Respond to a Power App**: `role`.
5. If the HTTP call fails (user not found) -> Catch scope responds `None`.

---

## WF9 - IAMS-UploadEvidence (called by Power Apps)

| | |
|---|---|
| Trigger | Power Apps (V2); inputs `EngagementID` (text), `EvidenceType` (text), `FileName` (text), `FileContent` (file), `ActionId` (number, 0 = none) |
| Output | `url` (text) |

1. **Compose** `SubFolder` = `Switch(EvidenceType, 'Planning','Planning', 'Walkthrough','Walkthroughs', 'Sample','Samples', 'Testing','Testing', 'Management Evidence','Management Evidence', 'Validation','Management Evidence', 'Planning')`.
2. **Compose** `SafeName` = `replace(replace(replace(FileName,'#','_'),'%','_'),'&','_')` (SharePoint-illegal characters); prefix with `formatDateTime(utcNow(),'yyyyMMdd-HHmmss')_` to avoid overwrites.
3. **Create file** (SharePoint) in `IA_Evidence`, folder path `/<EngagementID>/<SubFolder>`, content `base64ToBinary(triggerBody()?['file']?['contentBytes'])`.
4. **Update file properties**: Engagement Id = item ID of the engagement (Get items `EngagementID eq '<id>'`), EvidenceType Value, UploadedByUser = flow caller email (`triggerBody()?['email']` via the User email dynamic token).
5. If `ActionId > 0`: Update item on `IA_ActionPlans` `EvidenceUploaded = true`; set the file's `Action` and `Finding` lookups from the action.
6. Respond with the file's link (`Link to item`). WriteAuditLog.

Limits: Power Apps -> flow payload is practical up to roughly 20 MB; for bigger evidence the app opens the SharePoint folder link instead. Validate extension against an allow-list (pdf, docx, xlsx, pptx, jpg, png, msg, csv, zip) and reject others with a clear message.

---

## WF10 - IAMS-GenerateReport (called by Power Apps)

| | |
|---|---|
| Trigger | Power Apps (V2); inputs `ReportType`, `Period` (Q1-Q4 or Full Year), `Year` (text), `Entity` (text or All) |
| Output | `filename`, `url` |

1. **Compose** `FromDate`/`ToDate` from Period+Year, e.g. Q1 = `<Year>-01-01` to `<Year>-03-31`; Full Year = Jan 1 to Dec 31. (Use `concat`/`formatDateTime`; for quarters use a `Switch`.)
2. **Switch on ReportType** to gather data with server-side filters (Top Count 5000, pagination on):
   - *Quarterly / Annual IA Report:* plan items in range (`PlannedStart ge` and `le`), engagements closed in range, findings issued in range (`DateIssued`), action plan status counts (Filter array to count), CSA results.
   - *Outstanding Findings Report:* findings `FindingStatus ne 'Closed'` and `WorkflowStage eq 'Issued'`; group by Entity and Rating.
   - *Audit Plan Status:* plan items for the year with `AuditStatus` and `% complete` (completed / approved).
   - Add `Entity/Id eq <id>` when Entity <> All.
3. **Build HTML**: `Create HTML table` per section with custom columns; wrap in a Compose with a title block (MHAO Group Internal Audit - report name - period - generated date in GST, `Confidential`), headline KPIs, and section headings. Use inline CSS only.
4. **Create the document**: save the HTML as `.doc` (Word opens HTML) in a temp OneDrive/SharePoint folder, then **Convert file** (OneDrive for Business, Standard) to PDF. Test this in your tenant: if HTML->PDF is not supported, keep the `.doc`/`.docx`. If you have a Premium Word template action, use it for a branded layout instead.
5. **Create file** in `IA_Reports` (folder by year) and **Update file properties**: ReportType, ReportPeriod, Version `v0.1`, ReportStatus `Draft`, Entity.
6. Respond with filename and URL. Draft reports are visible to Managers/Owners; only after review does the manager set `ReportStatus = Issued`, which makes it visible to Executives (their group is granted at folder level by flow on Issued, or the Executive access is limited to a separate "Issued" folder).

# MHAO IAMS - Power BI Dashboard Specification

One semantic model `MHAO IAMS Model` and one report with four pages (dashboards 1-4 from the original design), published to a workspace `MHAO Internal Audit` and distributed through a workspace app. Source: SharePoint Online lists (no gateway needed).

Column names are the internal names in `MHAO_IAMS_Data_Model.xlsx`. Verify them in Power Query after connecting.

## 1. Connect and shape the data

Power Query parameter `SiteUrl` = the Internal Audit site URL. For each list use `SharePoint.Tables(SiteUrl, [ApiVersion = 15])` (or the SharePoint Online List connector) and select the list. Rules for every query:

1. **Remove unused columns early** (system columns except `ID`, `Created`, `Modified`).
2. **Expand lookup columns** to a key column. In the connector, a lookup comes back as a record with `Id` and `Value`:
   `Table.AddColumn(src, "EntityId", each [Entity][Id], Int64.Type)`; `[Entity][Value]` is the title. Keep the Id for relationships.
3. **Choice columns** come back as a record with `Value`: `each [Rating][Value]`.
4. **Person columns** are records with `Email`, `DisplayName`: keep both: `each [ResponsibleManager][Email]` and `... [DisplayName]`. Convert emails to lower case for RLS.
5. **Multi-person (TeamMembers)**: create a text column `TeamEmails` = `Text.Combine(List.Transform([TeamMembers], each Text.Lower([Email])), ";")`.
6. Set data types explicitly; dates as `date`.
7. Fill nulls: counts as 0; text as "".

Queries to import (Import mode, not DirectQuery):

| Query | Source | Key columns kept |
|---|---|---|
| Entities | IA_Entities | ID, Title, EntityCode, EntityType, Country, Active, EntityHeadEmail |
| Departments | IA_Departments | ID, Title, EntityId, DepartmentHeadEmail |
| Universe | IA_AuditUniverse | ID, Title, EntityId, DepartmentId, RiskRating, RiskScore, LastAuditDate, NextAuditDate, UniverseStatus, ProcessCategory |
| Risks | IA_RiskRegister | ID, Title, AuditAreaId, EntityId, RiskCategory, Likelihood, ImpactScore, InherentRisk, ControlRating, ResidualRisk, RiskStatus, RiskOwnerEmail |
| Plan | IA_AuditPlan | ID, AuditRef, Title, PlanYear, AuditAreaId, EntityId, AuditType, PlannedStart, PlannedFinish, RiskScore, BudgetHours, ActualHours, AuditStatus, ApprovalStatus, AssignedAuditorEmail |
| Engagements | IA_Engagements | ID, EngagementID, AuditPlanItemId, EntityId, Stage, OverallOpinion, ActualStart, ActualEnd, LeadAuditorEmail, TeamEmails |
| Findings | IA_Findings | ID, FindingID, Title, EngagementId, EntityId, DepartmentId, RiskCategory, Rating, WorkflowStage, AgreementStatus, ResponsibleManagerEmail/Name, DateIssued, OriginalDueDate, DueDate, ExtensionCount, FindingStatus, ClosedDate |
| Actions | IA_ActionPlans | ID, CAPAID, FindingId, EntityId, ActionOwnerEmail/Name, DueDate, CompletionPct, EvidenceUploaded, ValidationStatus, ActionStatus, FindingRating, ReminderStage, CompletedDate, Created |
| FollowUps | IA_FollowUps | ID, FindingId, ActionId, ReviewDate, Outcome |
| CSA | IA_CSARegister | ID, EntityId, DepartmentId, AssessmentPeriod, SubmissionDate, Score, Result |
| Date | generated | see below |

Pagination: the connector pages automatically, but use `[ApiVersion = 15]` for large lists. If refresh gets slow (> 5 minutes) filter Findings/Actions to the last 5 years and keep a separate archive query.

### Date table (DAX)

```dax
Date =
VAR _min = DATE(YEAR(MIN(Plan[PlannedStart])) - 1, 1, 1)
VAR _max = DATE(YEAR(TODAY()) + 2, 12, 31)
RETURN ADDCOLUMNS(
    CALENDAR(_min, _max),
    "Year", YEAR([Date]),
    "Quarter", "Q" & QUARTER([Date]),
    "YearQuarter", YEAR([Date]) & "-Q" & QUARTER([Date]),
    "Month No", MONTH([Date]),
    "Month", FORMAT([Date], "MMM"),
    "YearMonth", FORMAT([Date], "yyyy-MM"))
```
Mark as date table. Relationships from `Date[Date]` (inactive where multiple): Plan[PlannedStart] (active), Findings[DateIssued] (active), Actions[DueDate] (inactive; use USERELATIONSHIP), Findings[ClosedDate] (inactive).

### Report date (Gulf time)

The service runs in UTC, so `TODAY()` is wrong in the first 4 hours of the UAE day.

```dax
Report Date =
VAR _n = NOW() + 4/24
RETURN DATE(YEAR(_n), MONTH(_n), DAY(_n))
```
Use this everywhere instead of `TODAY()`. (Create as a measure.)

## 2. Relationships (all single direction, one-to-many)

| One side | Many side |
|---|---|
| Entities[ID] | Departments[EntityId], Universe[EntityId], Risks[EntityId], Plan[EntityId], Engagements[EntityId], Findings[EntityId], Actions[EntityId], CSA[EntityId] |
| Departments[ID] | Findings[DepartmentId], CSA[DepartmentId], Universe[DepartmentId] |
| Universe[ID] | Risks[AuditAreaId], Plan[AuditAreaId] |
| Plan[ID] | Engagements[AuditPlanItemId] |
| Engagements[ID] | Findings[EngagementId] |
| Findings[ID] | Actions[FindingId], FollowUps[FindingId] |
| Date[Date] | Plan[PlannedStart], Findings[DateIssued], (inactive) Actions[DueDate], Findings[ClosedDate], CSA[SubmissionDate] |

Avoid many-to-many and bidirectional filters. Hide the key columns and all `Id` fields from report view.

## 3. Measures

Create a `_Measures` table. Folders: Plan, Findings, Actions, Risk, Committee.

```dax
-- PLAN
Approved Audits = CALCULATE(COUNTROWS(Plan), Plan[ApprovalStatus] = "Approved", Plan[AuditStatus] <> "Cancelled")
Completed Audits = CALCULATE(COUNTROWS(Plan), Plan[AuditStatus] = "Completed")
Open Audits = CALCULATE(COUNTROWS(Plan), Plan[ApprovalStatus] = "Approved", NOT(Plan[AuditStatus] IN {"Completed","Deferred","Cancelled"}))
Plan Completion % = DIVIDE([Completed Audits], [Approved Audits])

Active Universe Areas = CALCULATE(COUNTROWS(Universe), Universe[UniverseStatus] = "Active")
Audited Areas =
CALCULATE(DISTINCTCOUNT(Plan[AuditAreaId]), Plan[AuditStatus] = "Completed")
Audit Coverage % = DIVIDE([Audited Areas], [Active Universe Areas])
High Risk Coverage % =
DIVIDE(
    CALCULATE(DISTINCTCOUNT(Plan[AuditAreaId]), Plan[AuditStatus] = "Completed", TREATAS({"Critical","High"}, Universe[RiskRating])),
    CALCULATE(COUNTROWS(Universe), Universe[UniverseStatus] = "Active", Universe[RiskRating] IN {"Critical","High"}))
Budget vs Actual Hours % = DIVIDE(SUM(Plan[ActualHours]), SUM(Plan[BudgetHours]))

-- FINDINGS (issued findings only; drafts are not reported)
Issued Findings = CALCULATE(COUNTROWS(Findings), Findings[WorkflowStage] IN {"Issued","Closed"})
Open Findings = CALCULATE(COUNTROWS(Findings), Findings[WorkflowStage] = "Issued", NOT(Findings[FindingStatus] IN {"Closed","Risk Accepted"}))
Critical Findings Open = CALCULATE([Open Findings], Findings[Rating] = "Critical")
High Findings Open = CALCULATE([Open Findings], Findings[Rating] = "High")
Closed Findings = CALCULATE(COUNTROWS(Findings), Findings[FindingStatus] = "Closed")
Closure Rate % = DIVIDE([Closed Findings], [Issued Findings])
Finding Age (Days) = -- calculated column on Findings
    IF(ISBLANK(Findings[DateIssued]), BLANK(),
       IF(Findings[FindingStatus] = "Closed",
          DATEDIFF(Findings[DateIssued], Findings[ClosedDate], DAY),
          DATEDIFF(Findings[DateIssued], DATE(YEAR(NOW() + 4/24), MONTH(NOW() + 4/24), DAY(NOW() + 4/24)), DAY)))
Age Bucket = -- calculated column
    SWITCH(TRUE(), ISBLANK(Findings[Finding Age (Days)]), "n/a",
        Findings[Finding Age (Days)] <= 30, "0-30",
        Findings[Finding Age (Days)] <= 60, "31-60",
        Findings[Finding Age (Days)] <= 90, "61-90", "90+")

-- ACTIONS
Open Actions = CALCULATE(COUNTROWS(Actions), Actions[ActionStatus] <> "Closed")
Overdue Actions =
VAR _d = [Report Date]
RETURN CALCULATE(COUNTROWS(Actions), Actions[ActionStatus] <> "Closed", Actions[DueDate] < _d)
Overdue % = DIVIDE([Overdue Actions], [Open Actions])
Actions Due This Month =
VAR _d = [Report Date]
RETURN CALCULATE(COUNTROWS(Actions), Actions[ActionStatus] <> "Closed",
    Actions[DueDate] >= DATE(YEAR(_d), MONTH(_d), 1), Actions[DueDate] <= EOMONTH(_d, 0))
Avg Closure Days =
AVERAGEX(FILTER(Actions, Actions[ActionStatus] = "Closed" && NOT(ISBLANK(Actions[CompletedDate]))),
    DATEDIFF(Actions[Created], Actions[CompletedDate], DAY))
Days Overdue (col) = -- calculated column on Actions
    IF(Actions[ActionStatus] <> "Closed" && Actions[DueDate] < DATE(YEAR(NOW() + 4/24), MONTH(NOW() + 4/24), DAY(NOW() + 4/24)),
       DATEDIFF(Actions[DueDate], DATE(YEAR(NOW() + 4/24), MONTH(NOW() + 4/24), DAY(NOW() + 4/24)), DAY), 0)
Traffic Light = -- calculated column, text for conditional formatting
    SWITCH(TRUE(), Actions[ActionStatus] = "Closed", "Green",
        Actions[DueDate] < DATE(YEAR(NOW() + 4/24), MONTH(NOW() + 4/24), DAY(NOW() + 4/24)), "Red",
        Actions[DueDate] <= DATE(YEAR(NOW() + 4/24), MONTH(NOW() + 4/24), DAY(NOW() + 4/24)) + 30, "Amber", "Green")
Overdue > 30 Days = CALCULATE(COUNTROWS(Actions), Actions[Days Overdue (col)] > 30)

-- RISK
Avg Residual Risk = AVERAGE(Risks[ResidualRisk])
Entity Risk Score =
    -- weighted: residual risk plus findings pressure
    [Avg Residual Risk] + 2 * [Critical Findings Open] + 1 * [High Findings Open] + 0.5 * [Overdue Actions]
Entity Risk Rank = RANKX(ALL(Entities[Title]), [Entity Risk Score],, DESC, Dense)

-- COMMITTEE
CSA Unsatisfactory = CALCULATE(COUNTROWS(CSA), CSA[Result] = "Unsatisfactory")
Findings Issued QoQ = [Issued Findings] - CALCULATE([Issued Findings], DATEADD('Date'[Date], -1, QUARTER))
```

Notes:
- The weights in `Entity Risk Score` are a starting point; agree them with the Head of IA and document them on the page.
- Measures that read `NOW()` update on refresh only; schedule refresh at least 3 times per working day.
- `Audit Coverage %` as written is "areas with a completed audit in the filtered period". Add a Year slicer; for a rolling cycle, use `Universe[NextAuditDate] >= Report Date` instead. Confirm MHAO's definition.

## 4. Pages

Theme: navy `#1F3864` headers, neutral greys, status colours red `#CF222E`, amber `#E6A200`, green `#2EA043`. Rating colours: Critical dark red, High red-orange, Medium amber, Low grey-blue. Use the same rating colours on every page. Fonts: Segoe UI. Page size 16:9. Add a tooltip page for findings detail and a drill-through page `Finding Detail` (fields: FindingID, Title, Entity, Rating, ResponsibleManager, DueDate, actions table).

### Page 1 - Audit Executive Dashboard
- Slicers (top): Year, Entity, Audit Type.
- Cards: Plan Completion %, Audit Coverage %, Completed Audits, Open Audits, Open Findings, Overdue Actions (with red conditional colour if > 0).
- Chart: clustered column of Approved vs Completed Audits by Quarter.
- Chart: stacked bar of Audit Status by Entity.
- Table: audits in progress (AuditRef, Title, Entity, Stage, Lead Auditor, Planned Finish) with days-to-finish data bar.
- Line: Budget vs Actual Hours % by month.

### Page 2 - Findings Dashboard
- Slicers: Year issued, Entity, Department, Rating, Status.
- Cards: Issued Findings, Open Findings, Critical Open, Closure Rate %.
- Charts: Findings by Risk (donut by Rating, fixed colours), Findings by Entity (stacked bar by Rating), Findings by Process Category (bar - uses Universe[ProcessCategory] via Engagement -> Plan -> Universe; add a calculated column on Findings with RELATED chain, or a flattened column in Power Query), Aging Analysis (columns by Age Bucket, stacked by Rating), Findings by Risk Category (treemap).
- Table: open findings (FindingID, Title, Entity, Rating, Responsible Manager, Due Date, Age) with drill-through.

### Page 3 - Corrective Actions Dashboard
- Slicers: Entity, Department, Finding Rating, Action Owner.
- Cards: Open Actions, Overdue Actions, Overdue %, Actions Due This Month, Avg Closure Days, Overdue > 30 Days.
- Charts: Actions by Traffic Light by Entity (stacked), Overdue actions by owner (top 10 bar), Due-date profile (columns by month for next 6 months), Reminder/escalation stage count (bar of ReminderStage).
- Table: overdue actions with Days Overdue, conditional icon via `Traffic Light`.

### Page 4 - Audit Committee Dashboard
- Header: report period slicer (YearQuarter), entity slicer (default all).
- Top 10 Risks: table of Risks sorted by ResidualRisk (Top N filter = 10), columns: Risk, Entity, Category, Inherent, Control rating, Residual (data bars).
- Critical Findings: table filtered Rating = Critical and open.
- Overdue CAPAs: table of Overdue Actions > 30 days with owner and Entity.
- Audit Plan Progress: gauge/bar for Plan Completion % + small multiples by quarter.
- Entity Risk Ranking: bar chart sorted by Entity Risk Score, with rank label.
- Narrative box (Smart narrative or text box) for the Head of IA; footer with data refresh time (`Last Refreshed` measure from a query using `DateTime.LocalNow()`).

## 5. Row-level security

Create roles in Desktop (Modeling -> Manage roles). Add users/groups in the service (Semantic model -> Security).

| Role | Table filter (DAX) | Members |
|---|---|---|
| IA_Leadership | none (all data) | IA_Owners, IA_Managers |
| IA_Auditor | none (all data; "edit own" is enforced in the app, not in Power BI) | IA_Auditors |
| IA_Executive | none (all findings including drafts, all plan items, read only) | IA_Executives |
| IA_BUHead | `Entities`: `Entities[EntityHeadEmail] = LOWER(USERPRINCIPALNAME())` (flows to Findings, Actions, Plan via EntityId) | IA_BUHeads |
| IA_DepartmentHead | `Departments`: `Departments[DepartmentHeadEmail] = LOWER(USERPRINCIPALNAME())` | IA_DepartmentHeads |
| IA_ActionOwner | `Departments`: department of the person (`Departments[DepartmentHeadEmail]` or the department mapping used by WF3); `Actions`: `Actions[ActionOwnerEmail] = LOWER(USERPRINCIPALNAME())` | IA_ActionOwners |

Behaviour to understand:
- RLS filters flow down relationships: filtering `Engagements` limits Findings and Actions to those engagements. Plan and Universe are not filtered by the Engagement rule; if auditors should only see their plan items, add `Plan[AssignedAuditorEmail] = LOWER(USERPRINCIPALNAME())`.
- Users with **Admin, Member or Contributor** workspace roles bypass RLS. Give all consumers **Viewer** access through the workspace **app**, not workspace roles.
- Emails in SharePoint must match UPNs; if a person's UPN differs from their email, use `LOWER(USERPRINCIPALNAME())` against a column built from `Claims`/account instead.
- Test in Desktop with View as role, then in the service with Test as role.
- Executives, Business Unit Heads and Department Heads can be limited to aggregates by not publishing the Finding Detail page in their app audience. Management roles (BU Head, Department Head, Action Owner) see only issued findings: add `Findings[WorkflowStage] IN {"Issued","Closed"}` to their roles.

## 6. Publishing, refresh, governance

1. Workspace `MHAO Internal Audit`; Premium or PPU is **not** required for this model size, but every viewer needs Power BI Pro (or the workspace on Premium/Fabric capacity).
2. Dataset credentials: OAuth2 with a service account that can read all lists (member of IA_Owners read). Privacy level Organizational.
3. Scheduled refresh: 07:00, 12:00, 16:00 and 20:00 Gulf time (set the time zone to Arabian Standard Time).
4. Create the workspace app with audiences: Leadership (all pages), Audit team (pages 1-3), Executives (pages 1 and 4), Management: BU Heads, Department Heads, Action Owners (pages 1 and 3, own scope).
5. Sensitivity label: Confidential - Internal Audit on the semantic model and report.
6. Certification: have the Head of IA sign off the measure definitions (documented on a hidden "Definitions" page).
7. Embed in Power Apps: Power BI tile control -> dashboard pinned from the report (Page 1 visuals).
8. Alerts: data alert on `Overdue Actions` and `Critical Findings Open` for the Head of IA (tiles pinned to a dashboard).
9. Version control: keep the .pbix in the IA SharePoint site under Administration, with change notes.

## 7. Validation checklist

1. Compare card values with filtered SharePoint views for one entity (open findings, overdue actions, plan completion).
2. Confirm the `Report Date` measure matches UAE date after 20:00 UTC.
3. Test each RLS role with a real user in each role; confirm BU Heads, Department Heads and Action Owners see only their own entity/department and never Draft findings (Executives see all, by decision).
4. Check a closed finding with several actions (it must count as closed only when all actions are closed).
5. Refresh with 3,000+ dummy findings and 10,000 actions to confirm refresh time and visual response (< 3 seconds).

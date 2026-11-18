# MHAO IAMS - Implementation Checklist and Rollout Plan

Owner: Group Head of Internal Audit. Suggested duration: **14 weeks** from approval to steady state (Phases 0-6), assuming 1 builder (Power Platform), 1 audit business owner, part-time M365 admin and a security/compliance reviewer. Adjust dates once start is agreed.

Deliverables already prepared (this folder): `MHAO_IAMS_Data_Model.xlsx`, `Provision-IAMS.ps1`, `MHAO_IAMS_Flow_Specifications.md`, `MHAO_IAMS_PowerApps_Spec.md`, `MHAO_IAMS_PowerBI_Spec.md`.

**Status of what has been checked:** the specs were reviewed for logic and syntax by reading only. Nothing has been executed in a Microsoft 365 tenant (the Claude connection to your tenant is read-only), so Phase 2-3 are the first real test of the script, flows, Power Fx and DAX. Budget time for fixes.

---

## Phase 0 - Decisions and prerequisites (Week 1-2)

Decisions (record each in a decision log):
- [ ] Platform confirmed: SharePoint lists (this design) vs Dataverse. Trigger to revisit: > 100k findings/actions or true row-level security needs.
- [ ] Scope for go-live: which entities are in wave 1 (suggest Group head office + 1-2 subsidiaries).
- [ ] Risk methodology: likelihood/impact scales, control rating, rating thresholds (Critical/High/Medium/Low), audit frequency by rating. Replaces the placeholders in the model.
- [ ] Finding workflow: confirm stages, SLA for management response (default 10 working days), who approves (Manager, Head of IA), what happens on disagreement.
- [ ] Escalation rules: 30/15 days before, overdue -> Dept Head, 30 days overdue -> Entity CEO. Confirm the CEO in each entity.
- [ ] Reporting calendar: Audit Committee dates, report templates and formats (Word/PDF).
- [ ] Data classification and retention: confidentiality label, retention period for working papers and evidence, legal/regulatory requirements.
- [ ] Definition of KPIs (coverage, plan completion, closure rate, entity risk ranking weights). Head of IA signs off.

Prerequisites:
- [ ] Licences: Microsoft 365 (SharePoint, Teams, Forms, Outlook); Power Apps (included "seeded" use is limited to apps using SharePoint/Standard connectors from Microsoft 365 - confirm with licensing partner; per-user or per-app plan if needed); Power Automate (Standard connectors); **Power BI Pro** for every viewer unless workspace is on Premium/Fabric capacity.
- [ ] Environments: Power Platform Dev, Test, Prod environments (or at least Dev+Prod) with a `MHAO_IAMS` solution; confirm DLP policies allow SharePoint, Approvals, Teams, Outlook, Forms, Office 365 Users, OneDrive together.
- [ ] Service account for flows (licensed mailbox/user, MFA exempt only if policy allows via conditional access exclusion for automation) with access to the IA site.
- [ ] M365 security groups created and owners named: IA-Owners, IA-Managers, IA-Auditors, IA-ActionOwners, IA-Executives, IA-BUHeads, IA-DepartmentHeads. Add as members of the matching SharePoint groups. A person may belong to several groups (roles are cumulative; Owner includes Manager, which includes Auditor).
- [ ] Naming/location: site URL (e.g. `/sites/InternalAudit`), tenant admin to create it as a **private team site** (Teams-connected optional), no external sharing.
- [ ] Sensitivity label (Confidential - Internal Audit) available; retention label policy agreed with compliance.
- [ ] Reference data prerequisite: Department Head emails (IA_Departments.DepartmentHead) and Business Unit Head emails (IA_Entities.EntityHead). Item-level access for own-department findings (WF3) depends on them; do not add real users to IA-ActionOwners, IA-BUHeads or IA-DepartmentHeads until these are filled.
- [ ] Project governance: sponsor, steering group (monthly), change control for the model.

Exit criteria: decisions signed, licences confirmed, environments and service account ready.

---

## Phase 1 - Foundation: site and data (Week 2-4)

- [ ] Create the site; apply sensitivity label; disable external sharing; set site admins (Head of IA + IT admin).
- [ ] Create SharePoint groups and add the M365 security groups.
- [ ] Install PnP.PowerShell on an admin workstation (`Install-Module PnP.PowerShell`). Register or use the interactive login rights; the account needs Site Owner.
- [ ] **Run `Provision-IAMS.ps1` on a TEST site first.** Log errors. Fix script issues (likely areas: lookup field creation order, user fields, permission cmdlet parameters across PnP versions). Re-run until clean (script is re-runnable).
- [ ] Compare resulting lists/columns with the Columns sheet; spot check 5 lists and all lookups, choices, calculated fields.
- [ ] Run the script on the PRODUCTION site. Do not hand-edit column internal names afterwards.
- [ ] Verify indexed columns (list settings -> Indexed columns).
- [ ] Load reference data (use Excel/CSV import or "Edit in grid view"): Entities (code, type, CEO, head), Departments (+ heads), Config values (CEO fallback and Head of IA email).
- [ ] Load the Audit Universe and Risk Register from existing audit files (see data migration below).
- [ ] Verify security: test accounts in each group; confirm list-level permissions match the Security sheet; confirm that unqualified permissions only were applied (item/folder-level rules come in Phase 2).
- [ ] Create views: "My items", "Open", "Overdue" per list; set sensible default sorts; set list column formatting for ratings.

Exit: lists exist in Prod, reference data loaded, access tested.

---

## Phase 2 - Automation (Week 4-8)

Build in a solution in Dev, test in Test, import managed solution to Prod.

- [ ] Environment variables set (site URL, Head of IA email, admin email); connection references configured with the service account.
- [ ] Child flow `WriteAuditLog` first.
- [ ] WF0 for every list; test creating one item per list.
- [ ] WF1a (plan approval: Draft, Pending Manager Review, Pending Owner Approval, Approved) and WF8 (multi-role lookup) and WF9 (evidence upload) because the app depends on them.
- [ ] WF1 Audit initiation: test with a dummy approved plan item; verify engagement item, folders, permissions (log in as an unrelated auditor -> cannot open the folder), milestones.
- [ ] WF3 Findings approval: test every branch: approve, reject at each stage, disagree path.
- [ ] WF5 + WF5b follow-up: test partial implementation, re-open, and multi-action finding closure.
- [ ] WF6 extension and WF4 reminders: test with date-shifted dummy actions (set `DueDate` to today+30, +15, -1, -31) and run WF4 manually; confirm only the right people (test accounts) receive emails and stages update only once.
- [ ] WF2 CSA: create the first Form (pilot department), test response + attachment handling.
- [ ] WF10 report generation: test HTML-to-PDF conversion; if not supported, switch to the fallback or Power BI paginated option.
- [ ] Error handling: force a failure in each flow; confirm Catch scope emails the admin.
- [ ] Flow ownership: co-owners set (two people), solution documented; flow run history retention understood (28 days).

Exit: all flows pass the test scripts in Test environment; no unhandled failures.

---

## Phase 3 - Apps and reporting (Week 6-11, overlaps Phase 2)

Power Apps:
- [ ] Build app shell, role detection, navigation and the header component.
- [ ] Build screens in this order: Findings, Actions, Plan, Engagements, Follow-Up, Fieldwork (phone), Dashboard, Reports, Risk.
- [ ] Resolve all delegation warnings (blue underlines) on filtered columns; accept only on tiny lookup lists.
- [ ] Verify Power Fx names against real data source names (flows appear without hyphens, e.g. `IAMSGetMyRole`); fix any column name mismatches.
- [ ] Accessibility checker, labels, tab order; test on laptop, tablet and phone.
- [ ] Share with security groups only; set co-owners; add to Teams as a tab for the audit team.

Power BI:
- [ ] Build Power Query tables; confirm lookup/choice/person expansion; fix types.
- [ ] Build relationships, date table, measures (use the spec); **validate every measure** against a manual count from filtered SharePoint views for 2 entities and 2 periods. Document differences.
- [ ] Build four pages; add drill-through; set mobile layouts for the Committee page.
- [ ] RLS roles; test each (View as role, then with real users).
- [ ] Publish workspace app with audiences; schedule refresh at 07:00, 12:00, 16:00, 20:00 Gulf time.

Exit: apps and dashboards pass UAT scripts; measure sign-off by Head of IA.

---

## Phase 4 - UAT and security review (Week 10-12)

UAT script (each item is pass/fail with evidence screenshot):
1. Audit lifecycle end to end: universe -> plan -> approval -> engagement -> fieldwork -> finding -> management response -> approvals -> issue -> action -> evidence -> validation -> closure -> report.
2. Role access: every role tries to open every list/library/screen; record what each can and cannot see. Auditor A cannot open Auditor B's engagement folder; action owner sees only own department's findings; executives see all findings including drafts (read only); Business Unit Heads see their entity and Department Heads their department (issued findings only).
3. Reminders and escalation with date-shifted data.
4. Extensions: approval path for High/Critical.
5. Reports: all four committee reports generated for last quarter using migrated data; reviewed by the audit manager.
6. Performance: load test data (3,000 findings, 10,000 actions) and measure app screen load (< 3 s) and dashboard refresh.
7. Mobile fieldwork: capture observation + photo evidence offline then sync.
8. Negative tests: invalid dates, missing evidence, duplicate Forms response, file with illegal characters.

Security & compliance review:
- [ ] Permissions review by IT security; no direct user grants, only groups.
- [ ] External sharing off; anonymous links disabled; guest access none.
- [ ] Audit log (Purview) enabled for the site; test that edits/deletes of findings are visible.
- [ ] Retention/label applied to libraries; recycle bin policy understood.
- [ ] Backup/restore approach agreed (SharePoint version history, 93-day recycle bin, plus an export of lists via Power Automate/Power BI to a protected archive if required by policy).
- [ ] DPIA/privacy check if personal data (names of staff in findings) is in scope.
- [ ] Segregation of duties: a finding author cannot give final approval (enforced in WF3 by approver identity check).

Exit: UAT signed off by Head of IA and Audit Managers; security review closed with no high issues.

---

## Phase 5 - Data migration, training, go-live (Week 12-13)

Data migration:
- [ ] Inventory existing sources: Excel trackers, Word reports, shared drives, emails.
- [ ] Map to the model (Columns sheet). Decide the cut-off: migrate **open** findings/actions and the last 2-3 years of reports; archive older material as read-only files.
- [ ] Clean data (entity names to match Entities list, valid people emails, rating values to the new scale, date formats).
- [ ] Import via Excel/"Quick Edit", Power Automate or PnP bulk import; load in order: Entities, Departments, Universe, Risks, Plan, Engagements, Findings, Actions. Disable WF4 (reminders) and email actions during the load; re-enable after.
- [ ] Reconcile: counts and totals by entity and rating vs source; Head of IA signs the reconciliation.

Training (role-based, 60-90 min each, recorded):
- [ ] Auditors and managers: planning, fieldwork, findings, evidence, follow-up.
- [ ] Action owners/management: responding to findings, updating actions, uploading evidence, requesting extensions (30-min session + one-page guide).
- [ ] Executives/Audit Committee: dashboard walk-through (20 min).
- [ ] Admins: flows, run history, access management, runbook.
- [ ] Prepare quick reference guides, short videos, and an FAQ page on the site.

Go-live checklist:
- [ ] Cutover date announced; freeze on old trackers.
- [ ] Final data delta loaded; reconciliation signed.
- [ ] Prod flows turned on in the planned order; WF4 last, after verifying Config values and recipients.
- [ ] Communications sent to all users with links, support contacts, and what changes.
- [ ] Support mailbox/Teams channel staffed; known issues list published.
- [ ] Rollback plan: keep old trackers read-only for 60 days; you can pause flows and revert the app share.

---

## Phase 6 - Hypercare and optimisation (Week 13-14 and ongoing)

- [ ] Daily check of flow failures (first 2 weeks), then weekly.
- [ ] Triage user feedback twice weekly; fix list ordered by impact.
- [ ] Review first reminder/escalation cycle with actual recipients; tune wording and timing.
- [ ] Verify the first monthly Power BI refresh and committee pack.
- [ ] Wave 2 onboarding of remaining entities (repeat Phase 5 activities per entity; one training session per entity).
- [ ] 90-day review with sponsor: adoption (users active, items created), data quality (items missing owner/date), SLA performance (management response timeliness, overdue %).

---

## Timeline summary

| Weeks | Phase | Key output |
|---|---|---|
| 1-2 | 0 Decisions and prerequisites | Signed decisions, licences, environments |
| 2-4 | 1 Foundation | Site, lists, reference data, security groups |
| 4-8 | 2 Automation | WF0-WF10 tested in Test |
| 6-11 | 3 Apps and reporting | Power Apps and Power BI built |
| 10-12 | 4 UAT and security | UAT sign-off |
| 12-13 | 5 Migration, training, go-live | Wave 1 live |
| 13-14+ | 6 Hypercare | Stable operation; wave 2 plan |

## RACI (summary)

| Activity | Head of IA | Audit Managers | Builder | M365 Admin | Security | Entities |
|---|---|---|---|---|---|---|
| Decisions and KPI definitions | A/R | C | C | I | C | C |
| Site, groups, licences | A | I | C | R | C | I |
| Build lists, flows, apps, BI | A | C | R | C | I | I |
| UAT | A | R | C | I | C | C |
| Security review | A | I | C | C | R | I |
| Data migration | A | R | R | I | I | C |
| Training | A | R | R | I | I | C |
| Go-live decision | A/R | C | C | C | C | I |

## Risk register (implementation)

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Script/flow/app defects found only on first real run (untested specs) | High | Medium | Dev/Test environments, test scripts per phase, 20% build contingency |
| Licensing gaps (Premium connectors, Power BI Pro) | Medium | High | Confirm in Phase 0; avoid Premium actions (fallbacks documented) |
| Poor data quality in migrated trackers | High | Medium | Cleaning step, reconciliation, migrate only open items |
| Low adoption by management respondents | Medium | High | Email-first approvals, short training, executive sponsorship, escalation rules |
| Confidentiality breach through wrong permissions | Low | High | Group-only permissions, folder/item rules by flow, permission review, Purview audit |
| Flow throttling/limits with growth | Low | Medium | Filtered queries, indexes, pagination, dashboards from Power BI not the app |
| Key-person dependency (single builder) | Medium | Medium | Solution documentation, co-owners, runbook |
| KPI definitions disputed | Medium | Medium | Head of IA sign-off on a Definitions page |

## Success measures (review at 90 days)

- 100% of new findings raised and issued through the system; 0 side trackers.
- Management responses received within SLA: target >= 85%.
- Overdue actions reduced by agreed percentage versus baseline.
- Committee pack produced in < 1 day (was manual).
- Zero access incidents; audit trail complete for every issued finding.

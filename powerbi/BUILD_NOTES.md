
## Power BI build (2026-11-03)
- **Project:** C:\Users\<you>\Internal Audit Management System\PowerBI\IAMS.pbip (PBIP: IAMS.Report + IAMS.SemanticModel). Generated from the saved spec; opened in Power BI Desktop and refreshed from SharePoint (site InternalAuditTest). Both pages load: Overview and Findings and Actions.
- **Fixes needed on first load:** TMDL indentation (in/let); SharePoint.Tables returns INTERNAL column names (fnListItems renames to display names via the list's field metadata); lookups and multi-value Entity columns are read by REST (fnLkpRest, fnJoinLkp, fnEntityRows) because the standard connector returned them blank or failed with a 500.
- **Setup note:** first refresh needs the SharePoint sign-in (Microsoft account, pick your work account) and Privacy levels set to Organizational for YOURTENANT.sharepoint.com (or ignore privacy checks for this file). Done by Ahmed.
- **Data scale:** Completion % in the Actions list is stored 0-100; the model divides by 100.
- **Blank tiles are real data gaps (test data):** no Date Issued, Department, Compliance Result, Risk Register rows yet; Compliance Rate and Satisfactory % stay blank until populated.
- **Still to do:** publish to the Power BI service and scheduled refresh need Pro (Ahmed's licence pending); Power Apps KPI tiles with report link; WF10 report/PDF export from the report; test all slicers with richer data.

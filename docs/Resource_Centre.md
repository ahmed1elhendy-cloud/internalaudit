# IAMS – Resource Centre (knowledge documents screen) – updated 2026-11-19

Status: DONE and LIVE. 16 tiles, documents uploaded and linked, published 2026-11-19 ~13:16 (after v108). Repo re-exported (GitHub commit b519b42).

## 2026-11-19 (later): templates, documents and links
- Added two tiles in "System and templates" (second row, Y=512): btnRC15 "Internal Audit Report Template" (X=16) and btnRC16 "Internal Audit Presentation Template" (X=285). REFERENCE group moved down (heading Y=618, tiles Y=648).
- Questionnaire Templates tile (btnRC10) now navigates to the Questionnaires screen (scrQuestionnaires).
- Knowledge Index now has 16 rows (new: items 15 and 16). DocLinks set for: Internal Audit Charter (Governance/MHAO_Internal_Audit_Charter_v1.pdf), Code of Ethics and Independence (Governance/MHAO_Code_of_Ethics_and_Independence.docx?web=1, opens in Word for the web), Quick-start Guide (System and templates/MHAO_IAMS_Quick_Start_Guide.pdf; one-page PDF), Report Template (.docx?web=1, opens in the browser) and Presentation Template (.pptx) in System and templates. IMS User Manual already had a link; IIA Standards and Glossary link to the web.
- Still without a DocLink (grey "Coming soon"): Internal Audit Methodology, Annual Audit Plan and Risk Assessment, Audit Report Rating Guide, Sampling Guide, Working-paper Standards, Contacts.
- What's New tile: Reference/MHAO_IAMS_Whats_New_Release_Notes.pdf (Release 1.1, Nov 2026, one page) uploaded and linked. Quick-start one-pager was reformatted and re-uploaded. No republish needed for DocLink changes (player refresh only).
- Cleanup: QU-6, QU-7 and the QU-12 stress test file removed from Questionnaire Files.

## 2026-11-19: why the tab was missing on the live app, and the fix
- Cause: published versions had been rebuilt from an older state, so the 15 nav galleries lost the Resource Centre entry. Fix: restored v104 (became v107), re-applied Items/OnSelect/TemplateSize 121 on the 15 galleries and OnSelect = Select(Parent) on the 15 tab labels, published as v108.
- Restore caveat: restoring fails with "locked by user" while any Studio session is open or closed in the last ~15 minutes. A restore creates a draft that must still be published.
- Rule: do not republish from an older restore point without re-checking the nav galleries. Keep the repo copy (powerapps/canvas-app/Src) as the reference.

## Decisions (Ahmed, 2026-11-17)
- Grouped sections, big tiles, last tab after Reports, name "Resource Centre". Tiles fed by SharePoint list Knowledge Index (change documents without editing the app). Blank DocLink shows grey tile with Notify "Coming soon - document not uploaded yet". Visible only to varIsAuditor.

## Tiles (4 groups, 16)
Governance: Internal Audit Charter; Code of Ethics and Independence.
Methodology: Internal Audit Methodology; Annual Audit Plan and Risk Assessment; Audit Report Rating Guide; Sampling Guide; Working-paper Standards.
System and templates: IMS User Manual; Quick-start Guide; Questionnaire Templates (opens Questionnaires screen); Internal Audit Report Template; Internal Audit Presentation Template.
Reference: IIA Global Internal Audit Standards (website); Glossary (placeholder = IIA page); Contacts (PDF); What's New (PDF).

## SharePoint (site InternalAuditTest)
- Library Knowledge Documents (folders Governance, Methodology, System and templates, Reference).
- List Knowledge Index: Title, DocGroup, Description, DocLink (hyperlink), IconName, Version, ReviewDate, SortOrder; 16 rows.
- Permissions: IA_Owners Full Control, IA_Managers Edit, IA_Auditors Read.

## Power Apps
- scrResources: header, gold "< Back to Dashboard", 4 group headings, tiles btnRC01..16 (257x92, X = 16/285/554/823). Tile formulas use a LookUp on Knowledge Index by Title and DocLink (not DocLink.Url).
- Nav galleries on every screen (galNav_5..14, galNav, galNav_1..4), TemplateSize 121. Items include {Value:"Resource Centre",Show:varIsAuditor}; OnSelect has the "Resource Centre" case navigating to scrResources. Tab labels: OnSelect = Select(Parent).
- To add a new document tile: add a Knowledge Index row, upload the file, set DocLink; for a new tile duplicate the pattern of btnRC15.

## Remaining
1. Upload the remaining 6 methodology/contacts documents and paste links into Knowledge Index.DocLink; replace the Glossary placeholder.
2. Ahmed: hard-refresh the player and confirm the new tiles open their documents.

## Studio automation notes
- Studio is slow; wait 10-60 s and re-check. Only press ctrl+a when the formula or property box is focused.
- The property name box is a combobox: click it (twice if it does not open), then pick from the list; the list opens at the top (use scroll, End works only when the list has focus). Set formulas in the formula bar, not the pane Text box (that makes literal text).
- Control copy/paste fails in this environment; insert new buttons via Insert > Button, then set X/Y/Width/Height (click, ctrl+a, type, Enter), border 0, radius 10, font size 12.
- SharePoint upload from automation: add a temporary input[type=file] in the page, use file_upload on it, then REST files/add with X-RequestDigest; set DocLink with MERGE (SP.FieldUrlValue).

# IAMS UAT Round 5 - Fixes (2026-11-18)

Studio changes saved, NOT yet published (publish from Studio to release).

## Fixed
1. Plan tab Plan Year dropdown: added "All" (values are text; default = current year). KPI tiles and plan gallery handle "All".
3. Add new engagement, Entity dropdown showed "Item 1, Item 2": DisplayFields/SearchFields = ["Value"].
4. Add new engagement, Engagement Type dropdown: same fix.
- Plan data source "Annual Audit Plan" re-added in Studio (it had been dropped while testing a multi-select) and lblPlanMain / Audit Area card Update restored to single-select formulas.

2b. Duplicate area names in Plan form Audit Area dropdown: Audit Universe has one row per area per entity (52 rows; not true duplicates, no data deleted). Dropdown now lists "Area · Entity" and only areas of the selected Entity.

## Not fixed
2. Plan form Audit Area multi-select: kept SINGLE select per decision. SharePoint column is unchanged (single lookup).
- Not re-tested in the published app.

## Restore and redo (18 Nov 2026)
- App restored to v87 (saved as v102) to bring back the original two-column New plan item layout, then fixes redone and saved (not published).
- Redone: Plan Year "All" (text values; counts and gallery use Value()); Plan form Entity list from the Entities list; Audit Area list filtered by selected Entity (tested in preview: MHAO Group shows 9 areas; MHAO Mobility has none in Audit Universe).
- Engagement form Entity and Engagement Type: the old combo boxes rendered blank popups whatever Items they had. Deleted and re-inserted as new combo boxes (same names DataCardValue4 / DataCardValue24, Items from Entities list / fixed choice list); both lists now show in preview. Engagement Type is single-select, Entity stays multi-select. Overall Opinion and Team Members also checked: populated.
- Not published.

## New finding and Audit Area fixes (18 Nov 2026)
- New finding: Responsible Manager dropdown showed numbers because the combo had no display field; added DisplayName so it lists names.
- New finding: removed the system "Name" and "Created" fields from the form. Status, Risk Category, Rating, Workflow Stage, Engagement, Entity, Compliance Result, Management Acceptance and Management Agreement were each opened in preview and list correctly.
- New plan item: Audit Area was empty when no Entity was chosen, because the Entity box starts with one blank selected item. Items now treat that as "no Entity" and list all areas; with an Entity chosen it filters to that Entity.
- Saved in Studio only; not published.

## Questionnaire upload import: duplicate questions (19 Nov 2026)

**Symptom:** uploaded questionnaires showed repeated sections and questions that were not in the Excel file (questionnaires 8 and 9).

**Root cause:** flow `IAMS-WF2d-QuestionnaireUploadImport` built the section list from `Section No` strings and the section/item JSON from hand-concatenated strings. Section numbers such as `1` and `1.0` produced duplicate section keys, so each duplicate section re-imported all of its rows. Quotes, backslashes and tabs in text could also break the JSON.

**Fix (live flow, saved):**
- `Section_list` now keys on `int(first(split(string('Section No'),'.')))` so each section is created once.
- `Create_section` and `Create_item` build their bodies with an escaping helper (backslash, double quote, tab, CR, LF) and `json()`; Ref falls back to `<section>.<seq>` when blank.

**Test results (all fields compared to the source xlsx):**
- Real files V4 / V4v: 9 items in 4 sections and 6 items in 3 sections, 0 differences.
- Stress file (quotes, backslash path, Arabic, 330-char question, tab/space in section title, `<`, `&`, `%`, `>`): 4 sections, 9 items, all text identical. Answer round-trip (Yes/No, Explanation, Document Ref, Owner with Arabic and quotes) stored and read back identically; the app screens bind directly to the stored fields.

**Known remaining behaviour:** newlines in a question become spaces; an invalid Evidence Rule silently becomes "Never"; differing titles under one section number merge under the first title; rows with no Section No are skipped; blank Ref is not auto-filled (stress file only; the template computes Ref); Template Info is not imported.
Questionnaires 8 and 9 still contain the old duplicates and should be deleted and re-uploaded.

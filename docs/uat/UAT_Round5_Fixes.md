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

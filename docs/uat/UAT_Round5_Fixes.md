# IAMS UAT Round 5 - Fixes (2026-11-18)

Studio changes saved, NOT yet published (publish from Studio to release).

## Fixed
1. Plan tab Plan Year dropdown: added "All" (values are text; default = current year). KPI tiles and plan gallery handle "All".
3. Add new engagement, Entity dropdown showed "Item 1, Item 2": DisplayFields/SearchFields = ["Value"].
4. Add new engagement, Engagement Type dropdown: same fix.
- Plan data source "Annual Audit Plan" re-added in Studio (it had been dropped while testing a multi-select) and lblPlanMain / Audit Area card Update restored to single-select formulas.

## Not fixed
2. Plan form Audit Area multi-select: kept SINGLE select per decision. SharePoint column is unchanged (single lookup).
2b. Duplicate area names in the Audit Area dropdown (e.g. Finance x6, one per entity in the Audit Universe list): not changed. Proposed fix: show "Area - Entity" labels filtered by the selected Entity.
- Not re-tested in the published app.

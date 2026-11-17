import os, json, shutil
from model import ROOT, w, build
REP = os.path.join(ROOT, "IAMS.Report")
DEFR = os.path.join(REP, "definition")
S = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/"

NAVY, NAVY2, BLUE, LIGHT, BG, RED, GREY, INK = "#0A2A66", "#143D85", "#1F6FD6", "#D6E8FF", "#EEF3FA", "#D32F2F", "#6B7A90", "#1B2A41"

def col(entity, prop):
    return {"Column": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}}
def mea(entity, prop):
    return {"Measure": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}}
def proj(field, entity, prop, active=None):
    p = {"field": field, "queryRef": "%s.%s" % (entity, prop), "nativeQueryRef": prop}
    if active: p["active"] = True
    return p
def C(e, p): return proj(col(e, p), e, p)
def M(e, p): return proj(mea(e, p), e, p)
def lit(v): return {"expr": {"Literal": {"Value": v}}}
def T(s): return lit("'%s'" % s.replace("'", "''"))
def clr(hexv): return {"solid": {"color": lit("'%s'" % hexv)}}
def num(n): return lit("%sD" % n)
def boo(b): return lit("true" if b else "false")

def box(title=None, bg="#FFFFFF", border="#DCE6F5", radius=10, title_color=NAVY, title_size=12, shadow=True, title_align="left"):
    o = {}
    if title:
        o["title"] = [{"properties": {"show": boo(True), "text": T(title), "fontSize": num(title_size), "bold": boo(True),
                                      "fontColor": clr(title_color), "alignment": T(title_align), "fontFamily": T("Segoe UI Semibold")}}]
    else:
        o["title"] = [{"properties": {"show": boo(False)}}]
    if bg is None:
        o["background"] = [{"properties": {"show": boo(False)}}]
    else:
        o["background"] = [{"properties": {"show": boo(True), "color": clr(bg), "transparency": num(0)}}]
    if border:
        o["border"] = [{"properties": {"show": boo(True), "color": clr(border), "radius": num(radius)}}]
    else:
        o["border"] = [{"properties": {"show": boo(False)}}]
    o["dropShadow"] = [{"properties": {"show": boo(bool(shadow))}}]
    return o

counter = [0]
def visual(pd, vtype, x, y, w_, h, roles=None, container=None, objects=None, sort=None, sync=None):
    counter[0] += 1
    name = "v%03d" % counter[0]
    v = {"visualType": vtype}
    if roles:
        v["query"] = {"queryState": {r: {"projections": ps} for r, ps in roles.items()}}
        if sort:
            v["query"]["sortDefinition"] = {"sort": [{"field": sort[0], "direction": sort[1]}], "isDefaultSort": True}
        v["drillFilterOtherVisuals"] = True
    if objects: v["objects"] = objects
    if container: v["visualContainerObjects"] = container
    if sync: v["syncGroup"] = sync
    doc = {"$schema": S + "visualContainer/2.0.0/schema.json", "name": name,
           "position": {"x": x, "y": y, "z": counter[0], "height": h, "width": w_, "tabOrder": counter[0]}, "visual": v}
    w(os.path.join(pd, "visuals", name, "visual.json"), json.dumps(doc, indent=2))

# ---------- primitives ----------
def rect(pd, x, y, w_, h, fill, shape="rectangle", radius=0):
    shp = {"tileShape": T(shape)}
    if shape == "rectangle" and radius: shp = {"tileShape": T("rectangle"), "roundEdge": num(radius)}
    visual(pd, "shape", x, y, w_, h, objects={
        "shape": [{"properties": shp}],
        "fill": [{"properties": {"show": boo(True), "fillColor": clr(fill), "transparency": num(0)}}],
        "outline": [{"properties": {"show": boo(False)}}]},
        container={"background": [{"properties": {"show": boo(False)}}], "border": [{"properties": {"show": boo(False)}}],
                   "dropShadow": [{"properties": {"show": boo(False)}}], "title": [{"properties": {"show": boo(False)}}]})

def tbox(pd, x, y, w_, h, runs, align="Left"):
    """runs: list of (text, size_pt, color, bold) ; one paragraph"""
    tr = [{"value": t, "textStyle": {"fontSize": "%spt" % sz, "color": c, "fontWeight": "bold" if b else "normal",
                                      "fontFamily": "Segoe UI Semibold" if b else "Segoe UI"}} for (t, sz, c, b) in runs]
    visual(pd, "textbox", x, y, w_, h, objects={"general": [{"properties": {"paragraphs": [{"textRuns": tr, "horizontalTextAlignment": align}]}}]},
           container=box(bg=None, border=None, shadow=False))

def icon(pd, x, y, glyph, fill=NAVY, size=38):
    rect(pd, x, y, size, size, fill, shape="oval")
    tbox(pd, x, y + 2, size, size - 4, [(glyph, 14, "#FFFFFF", True)], align="Center")

QUEUE = []
def button(pd, x, y, w_, h, text, target=None, fill=NAVY, color="#FFFFFF"):
    rect(pd, x, y, w_, h, fill, radius=8)
    def later():
        tbox(pd, x, y + (6 if w_ < 120 else 8), w_, h - (10 if w_ < 120 else 14), [(text, 10 if w_ < 120 else 11, color, True)], align="Center")
        c = box(bg=None, border=None, shadow=False)
        if target:
            c["visualLink"] = [{"properties": {"show": boo(True), "type": T("PageNavigation"), "navigationSection": T(target)}}]
        visual(pd, "actionButton", x, y, w_, h, objects={
            "fill": [{"properties": {"show": boo(False)}}], "outline": [{"properties": {"show": boo(False)}}],
            "text": [{"properties": {"show": boo(False)}}], "icon": [{"properties": {"shapeType": T("blank")}}]}, container=c)
    QUEUE.append(later)

NAVS = [("Overview", "pgOverview"), ("Findings & Actions", "pgDrill"), ("Reports", "pgReport")]
def navbtn(pd, i):
    button(pd, 14, 200 + i * 52, 172, 42, NAVS[i][0], target=NAVS[i][1], fill="#2563C9")

def card(pd, x, y, w_, h, ent, meas, title, glyph, gfill=NAVY, vcolor=NAVY):
    visual(pd, "card", x, y, w_, h, {"Values": [M(ent, meas)]},
           objects={"labels": [{"properties": {"fontSize": num(28), "color": clr(vcolor), "fontFamily": T("Segoe UI Semibold")}}],
                    "categoryLabels": [{"properties": {"show": boo(False)}}]},
           container=box(title=title, title_size=11, title_color=INK))
    icon(pd, x + w_ - 48, y + 10, glyph, gfill, 34)

def slicer(pd, x, y, w_, h, ent, prop, group, label):
    visual(pd, "slicer", x, y, w_, h, {"Values": [proj(col(ent, prop), ent, prop, active=True)]},
           objects={"data": [{"properties": {"mode": T("Dropdown")}}],
                    "header": [{"properties": {"show": boo(False)}}],
                    "items": [{"properties": {"fontSize": num(10), "fontColor": clr(INK)}}]},
           container=box(title=label, title_size=9, title_color=GREY, radius=8, shadow=False),
           sync={"groupName": group, "fieldChanges": True, "filterChanges": True})

def sidebar(pd, H):
    rect(pd, 0, 0, 200, H, NAVY)
    rect(pd, 0, H - 120, 200, 120, NAVY2)
    tbox(pd, 14, 18, 176, 90, [("MHAO", 12, "#9CC4FF", True), ("\nAudit Analysis\nDashboard", 18, "#FFFFFF", True)])
    tbox(pd, 14, 120, 176, 60, [("Better insights.\nStronger controls.\nGreater transparency.", 10, "#D6E8FF", False)])
    navbtn(pd, 0)
    tbox(pd, 14, H - 110, 176, 100, [("Accurate Audits.\nBetter Decisions.", 14, "#FFFFFF", True), ("\n\nMHAO Internal Audit", 9, "#9CC4FF", False)])

def header(pd):
    tbox(pd, 215, 12, 560, 52, [("Audit Analysis ", 26, NAVY, True), ("Dashboard", 26, BLUE, True)])
    tbox(pd, 215, 62, 560, 40, [("Track audit performance, identify key risks, analyse findings and monitor compliance across all entities.", 10, GREY, False)])
    slicer(pd, 790, 8, 130, 62, "Date", "Year", "slYear", "Year")
    slicer(pd, 928, 8, 150, 62, "Entities", "Entity", "slEntity", "Entity")
    slicer(pd, 1086, 8, 150, 62, "Engagements", "Engagement Type", "slType", "Audit Type")
    slicer(pd, 1244, 8, 130, 62, "Findings", "Status", "slStatus", "Status")
    button(pd, 1384, 14, 106, 50, "Download Report", target="pgReport")

PAGE_W, PAGE_H = 1500, 960

def page(pid, display, builder, width=PAGE_W, height=PAGE_H):
    pd = os.path.join(DEFR, "pages", pid)
    w(os.path.join(pd, "page.json"), json.dumps({"$schema": S + "page/2.0.0/schema.json", "name": pid, "displayName": display,
        "displayOption": "FitToPage", "height": height, "width": width,
        "objects": {"background": [{"properties": {"color": clr(BG), "transparency": num(0)}}],
                    "outspace": [{"properties": {"color": clr("#DCE6F5"), "transparency": num(0)}}]}}, indent=2))
    counter[0] = 0
    builder(pd)
    if pid != 'pgReport': navbtn(pd, 1); navbtn(pd, 2)
    while QUEUE: QUEUE.pop(0)()
    if pid == 'pgReport':
        while counter[0] < 46: rect(pd, 0, 0, 1, 1, BG)   # overwrite stale files from earlier builds

# ---------- chart style helpers ----------
def labels(show=True, style=None, size=9):
    p = {"show": boo(show), "fontSize": num(size), "color": clr(INK)}
    if style: p["labelStyle"] = T(style)
    return [{"properties": p}]
def legend(pos="Right"):
    return [{"properties": {"show": boo(True), "position": T(pos), "fontSize": num(9), "labelColor": clr(INK)}}]
def pt(prop_ent, prop, value, color):
    return {"properties": {"fill": clr(color)}, "selector": {"data": [{"scopeId": {"Comparison": {"ComparisonKind": 0,
            "Left": col(prop_ent, prop), "Right": {"Literal": {"Value": "'%s'" % value}}}}}]}}
def one_color(color):
    return [{"properties": {"fill": clr(color)}}]
RATING = [("Critical", "#B71C1C"), ("High", "#E53935"), ("Medium", "#F6C026"), ("Low", "#2F80ED")]
COMPLIANCE = [("Compliant", "#0A2A66"), ("Non-compliant", "#E53935"), ("N/A", "#A9BCD6")]
def table_style(size=9):
    return {"columnHeaders": [{"properties": {"fontColor": clr("#FFFFFF"), "backColor": clr(NAVY), "fontSize": num(size), "bold": boo(True)}}],
            "values": [{"properties": {"fontSize": num(size), "fontColorPrimary": clr(INK), "backColorPrimary": clr("#FFFFFF"),
                                       "fontColorSecondary": clr(INK), "backColorSecondary": clr("#F2F6FC")}}],
            "grid": [{"properties": {"gridVertical": boo(False), "gridHorizontalColor": clr("#E1E8F3")}}]}

def trend(pd, x, y, w_, h):
    visual(pd, "lineClusteredColumnComboChart", x, y, w_, h,
           {"Category": [C("Date", "Year-Month")], "Y": [M("Findings", "Total Findings")], "Y2": [M("Findings", "Findings Closed in Period")]},
           sort=(col("Date", "Year-Month"), "Ascending"),
           objects={"legend": legend("Top"), "labels": labels(True), "dataPoint": one_color(NAVY),
                    "lineStyles": [{"properties": {"strokeWidth": num(3)}}],
                    "categoryAxis": [{"properties": {"labelColor": clr(GREY), "fontSize": num(9)}}],
                    "valueAxis": [{"properties": {"labelColor": clr(GREY), "fontSize": num(9), "gridlineColor": clr("#E1E8F3")}}]},
           container=box(title="Audit Findings Trend (issued vs closed)"))

def donut(pd, x, y, w_, h, field, title, palette=None):
    dp = [pt("Findings", field, v, c) for v, c in palette] if palette else None
    o = {"legend": legend("Right"), "labels": labels(True, "Percent of total")}
    if dp: o["dataPoint"] = dp
    visual(pd, "donutChart", x, y, w_, h, {"Category": [C("Findings", field)], "Y": [M("Findings", "Total Findings")]}, objects=o, container=box(title=title))

def hbar(pd, x, y, w_, h, cat, meas, title, color=NAVY, ent="Findings", sortm=True):
    visual(pd, "barChart", x, y, w_, h, {"Category": [C(ent, cat[1]) if False else C(cat[0], cat[1])], "Y": [M(meas[0], meas[1])]},
           sort=(mea(meas[0], meas[1]), "Descending") if sortm else None,
           objects={"labels": labels(True), "dataPoint": one_color(color), "legend": [{"properties": {"show": boo(False)}}],
                    "categoryAxis": [{"properties": {"labelColor": clr(INK), "fontSize": num(9)}}],
                    "valueAxis": [{"properties": {"show": boo(False)}}]},
           container=box(title=title))

def status_bars(pd, x, y, w_, h):
    visual(pd, "barChart", x, y, w_, h, {"Category": [C("Plan", "Audit Type")], "Series": [C("Plan", "Audit Status")], "Y": [M("Plan", "Plan Items")]},
           objects={"legend": legend("Top"), "labels": labels(True),
                    "dataPoint": [pt("Plan", "Audit Status", "Completed", NAVY), pt("Plan", "Audit Status", "In Progress", "#5AA2F0"), pt("Plan", "Audit Status", "Planned", "#C2CCDA")],
                    "categoryAxis": [{"properties": {"labelColor": clr(INK), "fontSize": num(9)}}],
                    "valueAxis": [{"properties": {"show": boo(False)}}]},
           container=box(title="Audit Status by Engagement Type"))

def table(pd, x, y, w_, h, fields, title, sort=None, size=9):
    visual(pd, "tableEx", x, y, w_, h, {"Values": fields}, sort=sort, objects=table_style(size), container=box(title=title))

KPI_OVERVIEW = [("Engagements", "Total Audits", "Total Audits", "☰", NAVY, NAVY), ("Findings", "Total Findings", "Findings Identified", "⚠", NAVY, NAVY),
                ("Findings", "Resolved Findings", "Resolved Findings", "✔", NAVY, NAVY), ("Findings", "Open Findings", "Open Findings", "!", RED, RED),
                ("Findings", "Compliance Rate", "Compliance Rate", "%", NAVY, NAVY), ("Engagements", "Satisfactory %", "Satisfactory Engagements", "☺", NAVY, NAVY),
                ("Engagements", "Avg Audit Duration (days)", "Avg Audit Duration (days)", "⏱", NAVY, NAVY)]
KPI_DRILL = [("Actions", "Overdue Actions", "Overdue Actions", "!", RED, RED), ("Findings", "Avg Age of Open Findings (days)", "Avg Age of Open Findings (days)", "⏱", NAVY, NAVY),
             ("Findings", "Findings with Extensions", "Due-date Extensions", "↻", NAVY, NAVY), ("Actions", "Action Completion %", "Action Completion %", "✔", NAVY, NAVY),
             ("Actions", "Validation Backlog", "Validation Backlog", "☰", NAVY, NAVY), ("Milestones", "Late Milestones", "Late Milestones", "⚑", RED, RED),
             ("Plan", "Hours Used %", "Actual vs Budget Hours", "%", NAVY, NAVY)]

def kpi_row(pd, kp, y=96, h=104):
    x = 215
    for e, m, t, g, gf, vc in kp:
        card(pd, x, y, 174, h, e, m, t, g, gf, vc); x += 182

def overview(pd):
    sidebar(pd, PAGE_H); header(pd); kpi_row(pd, KPI_OVERVIEW)
    trend(pd, 215, 212, 560, 285)
    donut(pd, 785, 212, 330, 285, "Risk Category", "Findings by Category")
    hbar(pd, 1125, 212, 365, 285, ("Findings", "Entity"), ("Findings", "Total Findings"), "Findings by Entity")
    donut(pd, 215, 507, 300, 270, "Rating", "Findings by Risk Level", RATING)
    hbar(pd, 525, 507, 300, 270, ("Findings", "Department"), ("Findings", "Total Findings"), "Findings by Department", color=BLUE)
    donut(pd, 835, 507, 300, 270, "Compliance Result", "Compliance Status", COMPLIANCE)
    table(pd, 1145, 507, 345, 270, [C("Risks", "Risk Title"), C("Risks", "Risk Category"), C("Risks", "Risk Score")], "Top 5 Key Risks",
          sort=(col("Risks", "Risk Score"), "Descending"))
    status_bars(pd, 215, 787, 1275, 160)

def drill(pd):
    sidebar(pd, PAGE_H); header(pd); kpi_row(pd, KPI_DRILL)
    table(pd, 215, 212, 780, 285, [C("Findings", "Finding ID"), C("Findings", "Finding Title"), C("Findings", "Entity"), C("Findings", "Rating"), C("Findings", "Status"), C("Findings", "Current Due Date")],
          "Findings Register", sort=(col("Findings", "Date Issued"), "Descending"))
    hbar(pd, 1005, 212, 485, 285, ("Findings", "Department"), ("Findings", "Total Findings"), "Findings by Department", color=BLUE)
    table(pd, 215, 507, 780, 440, [C("Actions", "Action ID"), C("Actions", "Action Title"), C("Actions", "Entity"), C("Actions", "Status"), C("Actions", "Due Date"), C("Actions", "Completion %"), C("Actions", "Validation Status")],
          "Corrective Actions", sort=(col("Actions", "Due Date"), "Ascending"))
    table(pd, 1005, 507, 485, 215, [C("Risks", "Risk Title"), C("Risks", "Risk Category"), C("Risks", "Risk Score")], "Top Key Risks (by risk score)", sort=(col("Risks", "Risk Score"), "Descending"))
    visual(pd, "barChart", 1005, 732, 485, 215, {"Category": [C("Questionnaires", "Status")], "Y": [M("Questionnaires", "Questionnaires")]},
           objects={"labels": labels(True), "dataPoint": one_color(NAVY), "valueAxis": [{"properties": {"show": boo(False)}}]}, container=box(title="Questionnaire Status"))

def report(pd):
    W = 1100
    rect(pd, 0, 0, W, 118, NAVY)
    tbox(pd, 30, 14, 760, 52, [("MHAO Internal Audit Report", 26, "#FFFFFF", True)])
    tbox(pd, 30, 68, 760, 36, [("Internal Audit Management System · findings, actions and risk summary", 11, "#9CC4FF", False)])
    visual(pd, "card", 800, 40, 270, 50, {"Values": [M("Date", "Report Date Text")]},
           objects={"labels": [{"properties": {"fontSize": num(12), "color": clr("#FFFFFF")}}], "categoryLabels": [{"properties": {"show": boo(False)}}]},
           container=box(bg=None, border=None, shadow=False))
    button(pd, 960, 124, 130, 30, "← Dashboard", target="pgOverview", fill=BLUE)
    slicer(pd, 20, 124, 120, 54, "Date", "Year", "slYear", "Year")
    slicer(pd, 148, 124, 170, 54, "Entities", "Entity", "slEntity", "Entity")
    slicer(pd, 326, 124, 170, 54, "Engagements", "Engagement Type", "slType", "Audit Type")
    slicer(pd, 504, 124, 140, 54, "Findings", "Status", "slStatus", "Status")
    kp = KPI_OVERVIEW
    x = 20
    for i, (e, m, t, g, gf, vc) in enumerate(kp[:4]):
        card(pd, x, 190, 252, 92, e, m, t, g, gf, vc); x += 260
    x = 20
    for i, (e, m, t, g, gf, vc) in enumerate(kp[4:]):
        card(pd, x, 290, 252, 92, e, m, t, g, gf, vc); x += 260
    trend(pd, 20, 396, 1060, 250)
    donut(pd, 20, 656, 345, 260, "Rating", "Findings by Risk Level", RATING)
    donut(pd, 377, 656, 345, 260, "Risk Category", "Findings by Category")
    hbar(pd, 734, 656, 346, 260, ("Findings", "Entity"), ("Findings", "Total Findings"), "Findings by Entity")
    table(pd, 20, 926, 1060, 300, [C("Findings", "Finding ID"), C("Findings", "Finding Title"), C("Findings", "Entity"), C("Findings", "Rating"), C("Findings", "Status"), C("Findings", "Current Due Date")],
          "Findings Register", sort=(col("Findings", "Date Issued"), "Descending"), size=9)
    table(pd, 20, 1238, 1060, 190, [C("Actions", "Action ID"), C("Actions", "Action Title"), C("Actions", "Entity"), C("Actions", "Status"), C("Actions", "Due Date"), C("Actions", "Completion %")],
          "Corrective Actions", sort=(col("Actions", "Due Date"), "Ascending"), size=9)
    table(pd, 20, 1438, 1060, 80, [C("Risks", "Risk Title"), C("Risks", "Risk Category"), C("Risks", "Risk Score")], "Top Key Risks", sort=(col("Risks", "Risk Score"), "Descending"), size=9)
    tbox(pd, 20, 1526, 1060, 24, [("Confidential · MHAO Internal Audit · Save as PDF: File > Export > PDF (Desktop) or Export > PDF (Power BI service)", 8, GREY, False)], align="Center")

THEME = {"name": "IAMS Navy", "dataColors": [NAVY, BLUE, "#5AA2F0", "#A9BCD6", "#143D85", "#F6C026", "#E53935", "#2E9E6B"],
         "background": "#FFFFFF", "foreground": INK, "tableAccent": NAVY,
         "textClasses": {"title": {"fontFace": "Segoe UI Semibold", "color": NAVY, "fontSize": 12}, "label": {"fontFace": "Segoe UI", "color": INK, "fontSize": 9},
                         "callout": {"fontFace": "Segoe UI Semibold", "color": NAVY, "fontSize": 28}}}

def build_report():
    shutil.rmtree(REP, ignore_errors=True)
    w(os.path.join(REP, "definition.pbir"), json.dumps({"$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
        "version": "4.0", "datasetReference": {"byPath": {"path": "../IAMS.SemanticModel"}}}, indent=2))
    w(os.path.join(DEFR, "version.json"), json.dumps({"$schema": S + "versionMetadata/1.0.0/schema.json", "version": "2.0.0"}, indent=2))
    w(os.path.join(REP, "StaticResources", "RegisteredResources", "IAMS_Theme.json"), json.dumps(THEME, indent=2))
    ver = {"visual": "1.8.50", "report": "2.0.50", "page": "1.3.50"}
    w(os.path.join(DEFR, "report.json"), json.dumps({"$schema": S + "report/3.1.0/schema.json",
        "themeCollection": {"baseTheme": {"name": "CY24SU10", "reportVersionAtImport": ver, "type": "SharedResources"},
                            "customTheme": {"name": "IAMS_Theme.json", "reportVersionAtImport": ver, "type": "RegisteredResources"}},
        "resourcePackages": [{"name": "RegisteredResources", "type": "RegisteredResources",
                              "items": [{"name": "IAMS_Theme.json", "path": "IAMS_Theme.json", "type": "CustomTheme"}]}],
        "settings": {"useStylableVisualContainerHeader": True, "exportDataMode": "AllowSummarized", "defaultDrillFilterOtherVisuals": True}}, indent=2))
    w(os.path.join(DEFR, "pages", "pages.json"), json.dumps({"$schema": S + "pagesMetadata/1.0.0/schema.json",
        "pageOrder": ["pgOverview", "pgDrill", "pgReport"], "activePageName": "pgOverview"}, indent=2))
    page("pgOverview", "Overview", overview)
    page("pgDrill", "Findings and Actions", drill)
    page("pgReport", "Reports", report, width=1100, height=1556)

if __name__ == "__main__":
    build(); build_report(); print("ok")

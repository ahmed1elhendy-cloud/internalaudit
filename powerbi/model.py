import os, json, uuid, shutil
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
SM = os.path.join(ROOT, "IAMS.SemanticModel")
DEF = os.path.join(SM, "definition")
T = "\t"

def w(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)

def q(name):
    # TMDL identifier quoting
    if all(c.isalnum() or c == "_" for c in name):
        return name
    return "'" + name.replace("'", "''") + "'"

# ---------- shared M helpers (expressions) ----------
HELPERS = {
"fnLkpValue": '''(v as any) as nullable text =>
			if v = null then null
			else if v is record then (let x = Record.FieldOrDefault(v, "Value", null) in if x = null then null else Text.From(x))
			else if v is table then Text.Combine(List.Transform(Table.ToRecords(v), each Text.From(Record.FieldOrDefault(_, "Value", ""))), "; ")
			else if v is list then Text.Combine(List.Transform(v, each if _ is record then Text.From(Record.FieldOrDefault(_, "Value", "")) else Text.From(_)), "; ")
			else Text.From(v)''',
"fnLkpId": '''(v as any) as nullable number =>
			if v = null then null
			else if v is record then Record.FieldOrDefault(v, "Id", null)
			else if v is number then v
			else null''',
"fnLkpList": '''(v as any) as list =>
			if v = null then {null}
			else if v is record then {Record.FieldOrDefault(v, "Value", null)}
			else if v is table then (if Table.RowCount(v) = 0 then {null} else List.Transform(Table.ToRecords(v), each Record.FieldOrDefault(_, "Value", null)))
			else if v is list then (if List.Count(v) = 0 then {null} else List.Transform(v, each if _ is record then Record.FieldOrDefault(_, "Value", null) else _))
			else {Text.From(v)}''',
"fnListItems": '''(listTitle as text) as table =>
			let
				Source = SharePoint.Tables(SiteUrl, [ApiVersion = 15]),
				Items = Source{[Title = listTitle]}[Items],
				Fields = Json.Document(Web.Contents(SiteUrl, [RelativePath = "_api/web/lists/getbytitle('" & listTitle & "')/fields", Query = [#"$select" = "Title,InternalName", #"$filter" = "Hidden eq false"], Headers = [Accept = "application/json;odata=nometadata"]]))[value],
				Cols = Table.ColumnNames(Items),
				Cand = List.Select(List.Transform(Fields, each {[InternalName], [Title]}), each List.Contains(Cols, _{0}) and _{0} <> _{1} and not Text.StartsWith(_{0}, "Link") and not List.Contains(Cols, _{1})),
				Uniq = List.Distinct(Cand, each _{1}),
				Result = Table.RenameColumns(Items, Uniq, MissingField.Ignore)
			in
				Result''',
"fnLkpRest": '''(listTitle as text, displayName as text) as table =>
			let
				Fields = Json.Document(Web.Contents(SiteUrl, [RelativePath = "_api/web/lists/getbytitle('" & listTitle & "')/fields", Query = [#"$select" = "Title,InternalName", #"$filter" = "Hidden eq false"], Headers = [Accept = "application/json;odata=nometadata"]]))[value],
				Match = List.Select(Fields, each [Title] = displayName and not Text.StartsWith([InternalName], "Link")),
				Internal = if List.Count(Match) = 0 then displayName else Match{0}[InternalName],
				Src = Json.Document(Web.Contents(SiteUrl, [RelativePath = "_api/web/lists/getbytitle('" & listTitle & "')/items", Query = [#"$select" = "ID," & Internal & "/Id," & Internal & "/Title", #"$expand" = Internal, #"$top" = "5000"], Headers = [Accept = "application/json;odata=nometadata"]]))[value],
				T = Table.FromList(Src, Splitter.SplitByNothing(), {"R"}),
				Parsed = Table.AddColumn(T, "P", each let e = Record.FieldOrDefault([R], Internal, null), l = if e = null then {} else if e is list then e else {e} in [ID = [R][ID], Key = if List.Count(l) = 0 then null else l{0}[Id], Value = if List.Count(l) = 0 then null else Text.Combine(List.Transform(l, each Text.From(_[Title])), "; ")]),
				Out = Table.FromRecords(Table.Column(Parsed, "P"), type table [ID = Int64.Type, Key = Int64.Type, Value = text])
			in
				Out''',
"fnJoinLkp": '''(t as table, listTitle as text, displayName as text, keyName as nullable text) as table =>
			let
				L = fnLkpRest(listTitle, displayName),
				Dropped = Table.RemoveColumns(t, {displayName}, MissingField.Ignore),
				J = Table.NestedJoin(Dropped, {"ID"}, L, {"ID"}, "LK", JoinKind.LeftOuter),
				E = Table.ExpandTableColumn(J, "LK", {"Key", "Value"}, {"__Key", "__Value"}),
				R1 = Table.RenameColumns(E, {{"__Value", displayName}}),
				Final = if keyName = null then Table.RemoveColumns(R1, {"__Key"}) else Table.RenameColumns(R1, {{"__Key", keyName}})
			in
				Final''',
"fnEntityRows": '''(listTitle as text) as table =>
			let
				Src = Json.Document(Web.Contents(SiteUrl, [RelativePath = "_api/web/lists/getbytitle('" & listTitle & "')/items", Query = [#"$select" = "ID,Entity/Title", #"$expand" = "Entity", #"$top" = "5000"], Headers = [Accept = "application/json;odata=nometadata"]])),
				T = Table.FromList(Src[value], Splitter.SplitByNothing(), {"R"}),
				Names = Table.AddColumn(T, "Entity", each let e = Record.FieldOrDefault([R], "Entity", null) in if e = null then {null} else if e is list then (if List.Count(e) = 0 then {null} else List.Transform(e, each Record.FieldOrDefault(_, "Title", null))) else {Record.FieldOrDefault(e, "Title", null)}),
				Ids = Table.AddColumn(Names, "ID", each [R][ID], Int64.Type),
				Keep = Table.SelectColumns(Ids, {"ID", "Entity"}),
				Exp = Table.ExpandListColumn(Keep, "Entity")
			in
				Exp''',
"fnPerson": '''(v as any) as nullable text =>
			if v = null then null
			else if v is record then (let t = Record.FieldOrDefault(v, "Title", null) in if t = null then Record.FieldOrDefault(v, "DisplayName", null) else t)
			else if v is table then Text.Combine(List.Transform(Table.ToRecords(v), each Text.From(Record.FieldOrDefault(_, "Title", ""))), "; ")
			else Text.From(v)''',
}

def list_query(title, cols, extra="", raw=False):
    """cols: list of source column names to select"""
    sel = ", ".join('"%s"' % c for c in cols)
    if raw:
        head = "\t\t\t\tSource = SharePoint.Tables(SiteUrl, [ApiVersion = 15]),\n\t\t\t\tItems = Source{[Title = \"%s\"]}[Items],\n" % title
    else:
        head = "\t\t\t\tListName = \"%s\",\n\t\t\t\tItems = fnListItems(ListName),\n" % title
    return "let\n" + head + "\t\t\t\tSel = Table.SelectColumns(Items, {%s}, MissingField.UseNull)" % sel + extra

class Tbl:
    def __init__(self, name):
        self.name = name; self.cols = []; self.measures = []; self.mq = ""; self.hidden=False; self.extra=""
    def col(self, name, dtype="string", fmt=None, summ=None, key=False, sortby=None, hidden=False):
        self.cols.append((name, dtype, fmt, summ, key, sortby, hidden)); return self
    def meas(self, name, expr, fmt=None, folder=None, desc=None):
        self.measures.append((name, expr, fmt, folder, desc)); return self
    def render(self):
        o = []
        o.append("table %s" % q(self.name))
        if self.extra: o.append(T + self.extra)
        o.append("")
        for (name, expr, fmt, folder, desc) in self.measures:
            if desc: o.append(T + "/// " + desc)
            o.append(T + "measure %s = %s" % (q(name), expr))
            if fmt: o.append(T*2 + "formatString: " + fmt)
            if folder: o.append(T*2 + "displayFolder: " + folder)
            o.append("")
        for (name, dtype, fmt, summ, key, sortby, hidden) in self.cols:
            o.append(T + "column %s" % q(name))
            o.append(T*2 + "dataType: " + dtype)
            if fmt: o.append(T*2 + "formatString: " + fmt)
            if key: o.append(T*2 + "isKey")
            if hidden: o.append(T*2 + "isHidden")
            o.append(T*2 + "sourceColumn: " + name)
            o.append(T*2 + "summarizeBy: " + (summ or ("sum" if dtype in ("int64","double") else "none")))
            o.append("")
        o.append(T + "partition %s = m" % q(self.name))
        o.append(T*2 + "mode: import")
        o.append(T*2 + "source =")
        o.append(T*4 + self.mq.replace("\n", "\n"))
        o.append("")
        return "\n".join(o) + "\n"

DATE_FMT = "dd mmm yyyy"
tables = []

# ---------------- Plan ----------------
plan = Tbl("Plan")
plan_cols = ["ID","Audit Title","Audit Ref","Plan Year","Audit Type","Audit Area","Planned Start","Planned Finish","Risk Score","Budget Hours","Actual Hours","Audit Status","Approval Status"]
plan.mq = list_query("Annual Audit Plan", plan_cols + ["Entity"],
 ',\n\t\t\t\tArea = fnJoinLkp(Sel, ListName, "Audit Area", null),\n'
 '\t\t\t\tNoEnt = Table.RemoveColumns(Area, {"Entity"}),\n'
 '\t\t\t\tTyped = Table.TransformColumnTypes(NoEnt, {{"ID", Int64.Type}, {"Plan Year", Int64.Type}, {"Planned Start", type date}, {"Planned Finish", type date}, {"Risk Score", type number}, {"Budget Hours", type number}, {"Actual Hours", type number}, {"Audit Title", type text}, {"Audit Ref", type text}, {"Audit Type", type text}, {"Audit Status", type text}, {"Approval Status", type text}})\n'
 '\t\t\t\tin\n\t\t\t\t\tTyped')
plan.col("ID","int64",summ="none",key=True,hidden=True).col("Audit Title").col("Audit Ref").col("Plan Year","int64",fmt="0",summ="none").col("Audit Type").col("Audit Area").col("Planned Start","dateTime",fmt=DATE_FMT).col("Planned Finish","dateTime",fmt=DATE_FMT).col("Risk Score","double",fmt="0.0",summ="none").col("Budget Hours","double",fmt="#,0",summ="none").col("Actual Hours","double",fmt="#,0",summ="none").col("Audit Status").col("Approval Status")
plan.meas("Plan Items","COUNTROWS(Plan)",fmt="#,0",folder="Audit plan")
plan.meas("Budget Hours Total","SUM(Plan[Budget Hours])",fmt="#,0",folder="Audit plan")
plan.meas("Actual Hours Total","SUM(Plan[Actual Hours])",fmt="#,0",folder="Audit plan")
plan.meas("Hours Used %","DIVIDE([Actual Hours Total], [Budget Hours Total])",fmt="0%",folder="Audit plan",desc="Actual hours as a share of budget hours.")
tables.append(plan)

# ---------------- PlanEntities (bridge) ----------------
pe = Tbl("PlanEntities")
pe.mq = ('let\n\t\t\t\tSrc = fnEntityRows("Annual Audit Plan"),\n'
 '\t\t\t\tRen = Table.RenameColumns(Src, {{"ID", "Plan ID"}}),\n'
 '\t\t\t\tTyped = Table.TransformColumnTypes(Ren, {{"Plan ID", Int64.Type}, {"Entity", type text}})\n'
 '\t\t\t\tin\n\t\t\t\t\tTyped')
pe.col("Plan ID","int64",summ="none",hidden=True).col("Entity")
tables.append(pe)

# ---------------- Engagements ----------------
eng = Tbl("Engagements")
eng_cols = ["ID","Engagement ID","Engagement Title","Audit Plan Item","Start Date","End Date","Stage","Overall Opinion","Engagement Type","Lead Auditor"]
eng.mq = list_query("Audit Engagements", eng_cols,
 ',\n\t\t\t\tPlanId = fnJoinLkp(Sel, ListName, "Audit Plan Item", "Plan ID"),\n'
 '\t\t\t\tLead = fnJoinLkp(PlanId, ListName, "Lead Auditor", null),\n'
 '\t\t\t\tNoLk = Table.RemoveColumns(Lead, {"Audit Plan Item"}),\n'
 '\t\t\t\tTyped = Table.TransformColumnTypes(NoLk, {{"ID", Int64.Type}, {"Start Date", type date}, {"End Date", type date}, {"Engagement ID", type text}, {"Engagement Title", type text}, {"Stage", type text}, {"Overall Opinion", type text}, {"Engagement Type", type text}})\n'
 '\t\t\t\tin\n\t\t\t\t\tTyped')
eng.col("ID","int64",summ="none",key=True,hidden=True).col("Engagement ID").col("Engagement Title").col("Start Date","dateTime",fmt=DATE_FMT).col("End Date","dateTime",fmt=DATE_FMT).col("Stage").col("Overall Opinion").col("Engagement Type").col("Lead Auditor").col("Plan ID","int64",summ="none",hidden=True)
eng.meas("Total Audits","CALCULATE(DISTINCTCOUNT(Engagements[ID]), USERELATIONSHIP(EngagementEntities[Entity], Entities[Entity]))",fmt="#,0",folder="KPIs",desc="Engagements in the current filter. Uses the entity bridge so the Entity slicer applies.")
eng.meas("Satisfactory %","VAR rated = CALCULATE(COUNTROWS(FILTER(Engagements, NOT ISBLANK(Engagements[Overall Opinion]))), USERELATIONSHIP(EngagementEntities[Entity], Entities[Entity])) VAR sat = CALCULATE(COUNTROWS(FILTER(Engagements, Engagements[Overall Opinion] = \"Satisfactory\")), USERELATIONSHIP(EngagementEntities[Entity], Entities[Entity])) RETURN DIVIDE(sat, rated)",fmt="0%",folder="KPIs",desc="Engagements with Overall Opinion Satisfactory / engagements with an opinion.")
eng.meas("Avg Audit Duration (days)","CALCULATE(AVERAGEX(FILTER(Engagements, NOT ISBLANK(Engagements[Start Date]) && NOT ISBLANK(Engagements[End Date])), DATEDIFF(Engagements[Start Date], Engagements[End Date], DAY)), USERELATIONSHIP(EngagementEntities[Entity], Entities[Entity]))",fmt="0",folder="KPIs",desc="Average of End Date minus Start Date.")
tables.append(eng)

# ---------------- EngagementEntities ----------------
ee = Tbl("EngagementEntities")
ee.mq = ('let\n\t\t\t\tSrc = fnEntityRows("Audit Engagements"),\n'
 '\t\t\t\tRen = Table.RenameColumns(Src, {{"ID", "Engagement ID Key"}}),\n'
 '\t\t\t\tTyped = Table.TransformColumnTypes(Ren, {{"Engagement ID Key", Int64.Type}, {"Entity", type text}})\n'
 '\t\t\t\tin\n\t\t\t\t\tTyped')
ee.col("Engagement ID Key","int64",summ="none",hidden=True).col("Entity")
tables.append(ee)

# ---------------- Findings ----------------
fin = Tbl("Findings")
fin_cols = ["ID","Finding ID","Finding Title","Engagement","Entity","Department","Risk Category","Rating","Workflow Stage","Status","Date Issued","Closed Date","Original Due Date","Current Due Date","Extension Count","Compliance Result"]
fin.mq = list_query("Audit Findings Register", fin_cols,
 ',\n\t\t\t\tEngId = fnJoinLkp(Sel, ListName, "Engagement", "Engagement Key"),\n'
 '\t\t\t\tLk = fnJoinLkp(fnJoinLkp(EngId, ListName, "Entity", null), ListName, "Department", null),\n'
 '\t\t\t\tNoLk = Table.RemoveColumns(Lk, {"Engagement"}),\n'
 '\t\t\t\tTyped = Table.TransformColumnTypes(NoLk, {{"ID", Int64.Type}, {"Date Issued", type date}, {"Closed Date", type date}, {"Original Due Date", type date}, {"Current Due Date", type date}, {"Extension Count", Int64.Type}, {"Finding ID", type text}, {"Finding Title", type text}, {"Risk Category", type text}, {"Rating", type text}, {"Workflow Stage", type text}, {"Status", type text}, {"Compliance Result", type text}})\n'
 '\t\t\t\tin\n\t\t\t\t\tTyped')
fin.col("ID","int64",summ="none",key=True,hidden=True).col("Finding ID").col("Finding Title").col("Engagement Key","int64",summ="none",hidden=True).col("Entity").col("Department").col("Risk Category").col("Rating").col("Workflow Stage").col("Status").col("Date Issued","dateTime",fmt=DATE_FMT).col("Closed Date","dateTime",fmt=DATE_FMT).col("Original Due Date","dateTime",fmt=DATE_FMT).col("Current Due Date","dateTime",fmt=DATE_FMT).col("Extension Count","int64",fmt="0",summ="none").col("Compliance Result")
OPEN = '{"Open", "In Progress", "Pending Validation", "Re-opened"}'
RES = '{"Closed", "Risk Accepted"}'
fin.meas("Total Findings","COUNTROWS(Findings)",fmt="#,0",folder="KPIs",desc="Findings identified.")
fin.meas("Open Findings","CALCULATE([Total Findings], Findings[Status] IN %s)" % OPEN,fmt="#,0",folder="KPIs")
fin.meas("Resolved Findings","COALESCE(CALCULATE([Total Findings], Findings[Status] IN %s), 0)" % RES,fmt="#,0",folder="KPIs")
fin.meas("Compliance Rate","DIVIDE(CALCULATE([Total Findings], Findings[Compliance Result] = \"Compliant\"), CALCULATE([Total Findings], Findings[Compliance Result] IN {\"Compliant\", \"Non-compliant\"}))",fmt="0.0%",folder="KPIs",desc="Compliant / (Compliant + Non-compliant) findings.")
fin.meas("Findings Closed in Period","CALCULATE([Total Findings], USERELATIONSHIP(Findings[Closed Date], 'Date'[Date]))",fmt="#,0",folder="Trend",desc="Findings by the month they were closed (uses Closed Date).")
fin.meas("Findings % of Total","DIVIDE([Total Findings], CALCULATE([Total Findings], ALLSELECTED(Findings)))",fmt="0.0%",folder="Trend")
fin.meas("Avg Age of Open Findings (days)","COALESCE(AVERAGEX(FILTER(Findings, Findings[Status] IN %s && NOT ISBLANK(Findings[Date Issued])), DATEDIFF(Findings[Date Issued], TODAY(), DAY)), 0)" % OPEN,fmt="0",folder="Process")
fin.meas("Findings with Extensions","COALESCE(CALCULATE([Total Findings], Findings[Extension Count] > 0), 0)",fmt="#,0",folder="Process",desc="Findings whose due date was extended at least once.")
tables.append(fin)

# ---------------- Actions ----------------
act = Tbl("Actions")
act_cols = ["ID","Action ID","Action Title","Finding","Entity","Due Date","Completion %","Evidence Uploaded","Validation Status","Status","Finding Rating","Actual Completion Date","ExtensionCount"]
act.mq = list_query("Corrective Action Tracker", act_cols,
 ',\n\t\t\t\tFid = fnJoinLkp(Sel, ListName, "Finding", "Finding Key"),\n'
 '\t\t\t\tLk = fnJoinLkp(Fid, ListName, "Entity", null),\n'
 '\t\t\t\tNoLk = Table.RemoveColumns(Lk, {"Finding"}),\n'
 '\t\t\t\tTyped = Table.TransformColumnTypes(NoLk, {{"ID", Int64.Type}, {"Due Date", type date}, {"Actual Completion Date", type date}, {"Completion %", type number}, {"Evidence Uploaded", type logical}, {"ExtensionCount", Int64.Type}, {"Action ID", type text}, {"Action Title", type text}, {"Validation Status", type text}, {"Status", type text}, {"Finding Rating", type text}}),\n'
 '\t\t\t\tScaled = Table.TransformColumns(Typed, {{"Completion %", each if _ = null then null else _ / 100, type number}})\n'
 '\t\t\t\tin\n\t\t\t\t\tScaled')
act.col("ID","int64",summ="none",key=True,hidden=True).col("Action ID").col("Action Title").col("Finding Key","int64",summ="none",hidden=True).col("Entity").col("Due Date","dateTime",fmt=DATE_FMT).col("Completion %","double",fmt="0%",summ="none").col("Evidence Uploaded","boolean",summ="none").col("Validation Status").col("Status").col("Finding Rating").col("Actual Completion Date","dateTime",fmt=DATE_FMT).col("ExtensionCount","int64",fmt="0",summ="none")
DONE = '{"Completed", "Complete", "Closed", "Complete - Awaiting Validation", "Validated"}'
act.meas("Overdue Actions","CALCULATE(COUNTROWS(Actions), FILTER(Actions, Actions[Due Date] < TODAY() && NOT (Actions[Status] IN %s)))" % DONE,fmt="#,0",folder="Process",desc="Due date passed and action not completed.")
act.meas("Action Completion %","AVERAGE(Actions[Completion %])",fmt="0%",folder="Process",desc="Average Completion % across actions. If it shows 0-1 as 100%, the source stores fractions; if it looks too small, the source stores 0-100 and the format should change.")
act.meas("Validation Backlog","COALESCE(CALCULATE(COUNTROWS(Actions), Actions[Validation Status] IN {\"Submitted\", \"Under Review\"}), 0)",fmt="#,0",folder="Process")
act.meas("Total Actions","COUNTROWS(Actions)",fmt="#,0",folder="Process")
tables.append(act)

# ---------------- Milestones ----------------
ms = Tbl("Milestones")
ms_cols = ["ID","Milestone","Engagement","Type","Due Date","Completed Date","Status"]
ms.mq = list_query("Engagement Milestones", ms_cols,
 ',\n\t\t\t\tEid = fnJoinLkp(Sel, ListName, "Engagement", "Engagement Key"),\n'
 '\t\t\t\tNoLk = Table.RemoveColumns(Eid, {"Engagement"}),\n'
 '\t\t\t\tTyped = Table.TransformColumnTypes(NoLk, {{"ID", Int64.Type}, {"Due Date", type date}, {"Completed Date", type date}, {"Milestone", type text}, {"Type", type text}, {"Status", type text}})\n'
 '\t\t\t\tin\n\t\t\t\t\tTyped')
ms.col("ID","int64",summ="none",key=True,hidden=True).col("Milestone").col("Engagement Key","int64",summ="none",hidden=True).col("Type").col("Due Date","dateTime",fmt=DATE_FMT).col("Completed Date","dateTime",fmt=DATE_FMT).col("Status")
ms.meas("Late Milestones","COUNTROWS(FILTER(Milestones, Milestones[Status] = \"Late\" || (ISBLANK(Milestones[Completed Date]) && Milestones[Due Date] < TODAY())))",fmt="#,0",folder="Process",desc="Status Late, or not completed and past due.")
tables.append(ms)

# ---------------- Risks ----------------
rk = Tbl("Risks")
rk_cols = ["ID","Risk ID","Risk Title","Audit Area","Entity","Risk Category","Likelihood","Impact","Control Rating","Status"]
rk.mq = list_query("Risk Register", rk_cols,
 ',\n\t\t\t\tLk = fnJoinLkp(fnJoinLkp(Sel, ListName, "Audit Area", null), ListName, "Entity", null),\n'
 '\t\t\t\tTyped = Table.TransformColumnTypes(Lk, {{"ID", Int64.Type}, {"Likelihood", type number}, {"Impact", type number}, {"Control Rating", type number}, {"Risk ID", type text}, {"Risk Title", type text}, {"Risk Category", type text}, {"Status", type text}}),\n'
 '\t\t\t\tScore = Table.AddColumn(Typed, "Risk Score", each if [Likelihood] = null or [Impact] = null then null else [Likelihood] * [Impact], type number)\n'
 '\t\t\t\tin\n\t\t\t\t\tScore')
rk.col("ID","int64",summ="none",key=True,hidden=True).col("Risk ID").col("Risk Title").col("Audit Area").col("Entity").col("Risk Category").col("Likelihood","double",fmt="0",summ="none").col("Impact","double",fmt="0",summ="none").col("Control Rating","double",fmt="0",summ="none").col("Status").col("Risk Score","double",fmt="0",summ="none")
rk.meas("Max Risk Score","MAX(Risks[Risk Score])",fmt="0",folder="Risk")
tables.append(rk)

# ---------------- Questionnaires ----------------
qn = Tbl("Questionnaires")
qn_cols = ["ID","Questionnaire ID","Questionnaire Name","Engagement","Audit Type","Status","Issued Date","Question Count"]
qn.mq = list_query("Audit Questionnaires", qn_cols,
 ',\n\t\t\t\tEid = fnJoinLkp(Sel, ListName, "Engagement", "Engagement Key"),\n'
 '\t\t\t\tNoLk = Table.RemoveColumns(Eid, {"Engagement"}),\n'
 '\t\t\t\tTyped = Table.TransformColumnTypes(NoLk, {{"ID", Int64.Type}, {"Issued Date", type date}, {"Question Count", Int64.Type}, {"Questionnaire ID", type text}, {"Questionnaire Name", type text}, {"Audit Type", type text}, {"Status", type text}})\n'
 '\t\t\t\tin\n\t\t\t\t\tTyped')
qn.col("ID","int64",summ="none",key=True,hidden=True).col("Questionnaire ID").col("Questionnaire Name").col("Engagement Key","int64",summ="none",hidden=True).col("Audit Type").col("Status").col("Issued Date","dateTime",fmt=DATE_FMT).col("Question Count","int64",fmt="0",summ="none")
qn.meas("Questionnaires","COUNTROWS(Questionnaires)",fmt="#,0",folder="Questionnaires")
qn.meas("Questionnaires To Review","CALCULATE(COUNTROWS(Questionnaires), Questionnaires[Status] IN {\"Under Review\", \"Returned\", \"In Progress\", \"Issued\"})",fmt="#,0",folder="Questionnaires")
tables.append(qn)

# ---------------- Entities ----------------
en = Tbl("Entities")
en.mq = list_query("Entities", ["ID","Title"], raw=True, extra=
 ',\n\t\t\t\tRen = Table.RenameColumns(Sel, {{"Title", "Entity"}}),\n'
 '\t\t\t\tTyped = Table.TransformColumnTypes(Ren, {{"ID", Int64.Type}, {"Entity", type text}})\n'
 '\t\t\t\tin\n\t\t\t\t\tTyped')
en.col("ID","int64",summ="none",hidden=True).col("Entity")
tables.append(en)

# ---------------- Date ----------------
dt = Tbl("Date")
dt.extra = "dataCategory: Time"
dt.mq = ('let\n\t\t\t\tDays = List.Dates(#date(2024, 1, 1), 2557, #duration(1, 0, 0, 0)),\n'
 '\t\t\t\tT = Table.FromList(Days, Splitter.SplitByNothing(), {"Date"}),\n'
 '\t\t\t\tTyped = Table.TransformColumnTypes(T, {{"Date", type date}}),\n'
 '\t\t\t\tYr = Table.AddColumn(Typed, "Year", each Date.Year([Date]), Int64.Type),\n'
 '\t\t\t\tYm = Table.AddColumn(Yr, "Year-Month", each Date.ToText([Date], "yyyy-MM"), type text)\n'
 '\t\t\t\tin\n\t\t\t\t\tYm')
dt.col("Date","dateTime",fmt=DATE_FMT,key=True).col("Year","int64",fmt="0",summ="none").col("Year-Month")
dt.meas("Report Date Text","\"Generated \" & FORMAT(TODAY(), \"dd mmm yyyy\")",folder="Report",desc="Caption for the printable report page.")
tables.append(dt)

# ---------------- Relationships ----------------
rels = [
 ("Findings.'Engagement Key'", "Engagements.ID", True),
 ("Actions.'Finding Key'", "Findings.ID", True),
 ("Engagements.'Plan ID'", "Plan.ID", True),
 ("Milestones.'Engagement Key'", "Engagements.ID", True),
 ("Questionnaires.'Engagement Key'", "Engagements.ID", True),
 ("Findings.Entity", "Entities.Entity", True),
 ("Actions.Entity", "Entities.Entity", False),
 ("Risks.Entity", "Entities.Entity", True),
 ("PlanEntities.'Plan ID'", "Plan.ID", True),
 ("PlanEntities.Entity", "Entities.Entity", False),
 ("EngagementEntities.'Engagement ID Key'", "Engagements.ID", True),
 ("EngagementEntities.Entity", "Entities.Entity", False),
 ("Findings.'Date Issued'", "'Date'.Date", True),
 ("Findings.'Closed Date'", "'Date'.Date", False),
]
def rel_text():
    o=[]
    for i,(f,t,act_) in enumerate(rels):
        o.append("relationship r%02d" % (i+1))
        o.append(T+"fromColumn: "+f)
        o.append(T+"toColumn: "+t)
        if not act_: o.append(T+"isActive: false")
        o.append("")
    return "\n".join(o)

# ---------------- Measures table ----------------
mt = Tbl("Measures")
mt.mq = 'let\n\t\t\t\tSource = #table(type table [Name = text], {{"Measures"}})\n\t\t\t\tin\n\t\t\t\t\tSource'
mt.col("Name", hidden=True)
# page/overview measures are on other tables already; add a few cross-table ones here

def build():
    if os.path.isdir(ROOT): shutil.rmtree(ROOT)
    # semantic model
    w(os.path.join(SM, "definition.pbism"), json.dumps({"$schema":"https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json","version":"4.0","settings":{}}, indent=2))
    w(os.path.join(DEF, "database.tmdl"), "database\n\tcompatibilityLevel: 1600\n")
    ml = ["model Model","\tculture: en-US","\tdefaultPowerBIDataSourceVersion: powerBI_V3","\tdiscourageImplicitMeasures",""]
    for t in tables: ml.append("ref table %s" % q(t.name))
    ml.append("")
    ml.append("ref expression SiteUrl")
    for h in HELPERS: ml.append("ref expression %s" % h)
    w(os.path.join(DEF,"model.tmdl"), "\n".join(ml)+"\n")
    ex = ['expression SiteUrl = "https://YOURTENANT.sharepoint.com/sites/InternalAuditTest" meta [IsParameterQuery = true, IsParameterQueryRequired = true, Type = "Text"]','\tlineageTag: '+str(uuid.uuid4()),""]
    for h,body in HELPERS.items():
        ex.append("expression %s =" % h)
        ex.append("\t\t"+body)
        ex.append("\tlineageTag: "+str(uuid.uuid4()))
        ex.append("")
    w(os.path.join(DEF,"expressions.tmdl"), "\n".join(ex)+"\n")
    for t in tables:
        w(os.path.join(DEF,"tables",t.name+".tmdl"), t.render())
    w(os.path.join(DEF,"relationships.tmdl"), rel_text())
    w(os.path.join(ROOT,"IAMS.pbip"), json.dumps({"version":"1.0","artifacts":[{"report":{"path":"IAMS.Report"}}],"settings":{"enableAutoRecovery":True}}, indent=2))

if __name__=="__main__":
    build(); print("model built")

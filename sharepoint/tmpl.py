import sys
sys.path.insert(0,"/home/claude")
from iams_spec import *
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.comments import Comment
from openpyxl.utils import get_column_letter

L = {l["name"]: l for l in LISTS}
def choices(listname, col):
    for c in L[listname]["cols"]:
        if c[0] == col: return c[3]["choices"]

wb = Workbook(); wb.remove(wb.active)
H = PatternFill("solid", fgColor="1F3864"); HF = Font(bold=True, color="FFFFFF")
REQ = PatternFill("solid", fgColor="C00000")
N = 300

# Instructions
ws = wb.create_sheet("Instructions")
txt = [
 ("MHAO IAMS - Import Templates", True),
 ("Fill the sheets in this order: Entities, Departments, AuditUniverse, Config. Do not rename sheets or column headings.", False),
 ("Red headings = required. Blue headings = optional. Use the dropdowns where they appear.", False),
 ("People columns: enter the work EMAIL address exactly as in Microsoft 365 (e.g. user@example.com).", False),
 ("Dates: enter as yyyy-mm-dd (e.g. 2026-03-31).", False),
 ("Entity / Department columns: type the name exactly as it appears on the Entities / Departments sheets (use the dropdown).", False),
 ("Active: choose Yes or No.", False),
 ("Do NOT fill reference numbers (Audit Area ID etc.). The system generates them.", False),
 ("Keep one row per item, no blank rows between, no merged cells. Maximum 300 rows per sheet in this template.", False),
 ("", False),
 ("Examples (do not copy into the sheets)", True),
 ("Entities: Entity Name = 'MHAO Properties LLC'; Entity Code = 'MPL'; Entity Type = Subsidiary; Country = 'UAE'; Entity Head = a.head@..; Entity CEO = c.ceo@..; Active = Yes", False),
 ("Departments: Department Name = 'Finance'; Entity = 'MHAO Properties LLC'; Department Head = f.head@..; Active = Yes", False),
 ("AuditUniverse: Auditable Area = 'Procure-to-Pay'; Entity = 'MHAO Properties LLC'; Department = 'Finance'; Process Category = Procurement; Risk Rating = High; Risk Score = 15; Audit Frequency = Annual", False),
 ("Risk Score = Likelihood (1-5) x Impact (1-5), so 1 to 25. Use the MHAO-approved methodology.", False),
]
for t,b in txt:
    ws.append([t]); ws.cell(ws.max_row,1).font = Font(bold=b, size=13 if b else 11)
ws.column_dimensions["A"].width = 130

def make(name, cols, widths):
    ws = wb.create_sheet(name)
    for j,(hdr, req, note) in enumerate(cols,1):
        c = ws.cell(1,j,hdr); c.font = HF; c.fill = REQ if req else H
        c.alignment = Alignment(wrap_text=True, vertical="center")
        if note: c.comment = Comment(note, "IAMS")
        ws.column_dimensions[get_column_letter(j)].width = widths[j-1]
    ws.row_dimensions[1].height = 32; ws.freeze_panes = "A2"
    return ws
def dv_list(ws, col, formula, rows=N):
    d = DataValidation(type="list", formula1=formula, allow_blank=True, showErrorMessage=True,
                       errorTitle="Invalid value", error="Please choose a value from the list.")
    ws.add_data_validation(d); d.add(f"{col}2:{col}{rows+1}")
def inline(vals): return '"' + ",".join(vals) + '"'

# Lists sheet (hidden-ish) for choices
lst = wb.create_sheet("Lists")
lists = {
 "EntityType": choices("IA_Entities","EntityType"),
 "YesNo": ["Yes","No"],
 "ProcessCategory": choices("IA_AuditUniverse","ProcessCategory"),
 "Rating": choices("IA_AuditUniverse","RiskRating"),
 "Frequency": choices("IA_AuditUniverse","AuditFrequency"),
 "UniverseStatus": choices("IA_AuditUniverse","UniverseStatus"),
}
for j,(k,v) in enumerate(lists.items(),1):
    lst.cell(1,j,k).font = Font(bold=True)
    for i,x in enumerate(v,2): lst.cell(i,j,x)
    lst.column_dimensions[get_column_letter(j)].width = 22
def rng(k):
    j = list(lists).index(k)+1; n = len(lists[k])+1
    return f"=Lists!${get_column_letter(j)}$2:${get_column_letter(j)}${n}"

# Entities
e = make("Entities", [
 ("Entity Name", True, "Full legal or trading name. Must be unique."),
 ("Entity Code", True, "Short unique code, e.g. MPL"),
 ("Entity Type", False, "Parent, Subsidiary, Associate or Joint Venture"),
 ("Country", False, ""),
 ("Entity Head Email", False, "Entity head / MD work email"),
 ("Entity CEO Email", False, "Receives the 30-days-overdue escalation"),
 ("Active", True, "Yes or No"),
], [38,14,18,16,34,34,10])
dv_list(e,"C",rng("EntityType")); dv_list(e,"G",rng("YesNo"))

# Departments
d = make("Departments", [
 ("Department Name", True, ""),
 ("Entity", True, "Choose from the Entities sheet"),
 ("Department Head Email", False, "First escalation level for overdue actions"),
 ("Active", True, "Yes or No"),
], [34,38,34,10])
dv_list(d,"B", f"=Entities!$A$2:$A${N+1}"); dv_list(d,"D",rng("YesNo"))

# Audit universe
u = make("AuditUniverse", [
 ("Auditable Area", True, "Process, function or entity that can be audited"),
 ("Entity", True, "Choose from the Entities sheet"),
 ("Department", False, "Choose from the Departments sheet"),
 ("Process Category", False, ""),
 ("Process Owner Email", False, ""),
 ("Risk Rating", False, "Critical, High, Medium, Low"),
 ("Risk Score (1-25)", False, "Likelihood x Impact"),
 ("Last Audit Date", False, "yyyy-mm-dd; leave blank if never audited"),
 ("Audit Frequency", False, ""),
 ("Status", True, "Active, Retired, On Hold"),
], [38,38,28,22,34,14,14,16,16,14])
dv_list(u,"B", f"=Entities!$A$2:$A${N+1}"); dv_list(u,"C", f"=Departments!$A$2:$A${N+1}")
dv_list(u,"D",rng("ProcessCategory")); dv_list(u,"F",rng("Rating"))
dv_list(u,"I",rng("Frequency")); dv_list(u,"J",rng("UniverseStatus"))
sc = DataValidation(type="whole", operator="between", formula1="1", formula2="25", allow_blank=True,
                    showErrorMessage=True, error="Whole number from 1 to 25")
u.add_data_validation(sc); sc.add(f"G2:G{N+1}")
for r in range(2,N+2): u.cell(r,8).number_format = "yyyy-mm-dd"

# Config
c = make("Config", [("Key", True, "Do not change keys"), ("Value", True, ""), ("Description", False, "")], [26,40,70])
for k,v,dsc in CONFIG_SEED:
    c.append([k, v, dsc])
    if k in ("ReminderDays1","ReminderDays2","EscalateCEOAfterDays"): pass
c.cell(c.max_row+2,1,"Fill GroupCEOEmail and HeadOfIAEmail. The three day values can stay as they are unless MHAO's policy differs.").font = Font(italic=True)

wb.move_sheet("Lists", offset=10)
wb.save("/mnt/user-data/outputs/MHAO_IAMS_Import_Templates.xlsx")
print("saved")

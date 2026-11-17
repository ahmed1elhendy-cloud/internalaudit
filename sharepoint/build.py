import sys, uuid, re
from xml.sax.saxutils import escape
sys.path.insert(0, "/home/claude")
from iams_spec import *
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

OUT = "/mnt/user-data/outputs"
TYPE_LABEL = dict(text="Single line of text", note="Multiple lines of text", choice="Choice", number="Number", date="Date (date only)",
                  bool="Yes/No", user="Person", usermulti="Person (multiple)", lookup="Lookup", calc="Calculated", url="Hyperlink")

# ---------------------------------------------------------------- Excel
wb = Workbook()
HFILL = PatternFill("solid", fgColor="1F3864"); HFONT = Font(bold=True, color="FFFFFF", name="Calibri")
thin = Side(style="thin", color="BFBFBF"); BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)

def sheet(name, headers, rows, widths):
    ws = wb.create_sheet(name)
    ws.append(headers)
    for c in ws[1]:
        c.fill, c.font = HFILL, HFONT
        c.alignment = Alignment(vertical="center", wrap_text=True)
    for r in rows:
        ws.append(list(r))
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical="top"); c.border = BORDER
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    return ws

wb.remove(wb.active)

# README
ws = wb.create_sheet("README")
lines = [
 ("MHAO Internal Audit Management System (IAMS) - Data Model", True),
 ("Platform: SharePoint Online lists/libraries + Power Apps + Power Automate + Power BI (Standard connectors only).", False),
 ("", False),
 ("Sheets", True),
 ("Lists - every SharePoint list and library with purpose", False),
 ("Columns - full column dictionary (internal name, type, choices, required, indexed, notes)", False),
 ("Relationships - lookup relationships (Power Apps data model)", False),
 ("Security - SharePoint groups and permission matrix", False),
 ("Workflows - Power Automate flows (incl. additions to your original design)", False),
 ("PowerApps - screen-to-data-source map", False),
 ("Design Decisions - changes/additions versus the original draft, and open items", False),
 ("", False),
 ("Companion file: Provision-IAMS.ps1 creates the lists, columns, groups and seed config from this same spec (PnP.PowerShell).", False),
 ("Items in Config sheet values (e.g. CEO email) must be filled in before the reminder flow runs.", False),
]
for t, b in lines:
    ws.append([t]); ws.cell(ws.max_row, 1).font = Font(bold=b, size=14 if b and ws.max_row == 1 else 11)
ws.column_dimensions["A"].width = 120

n_cols = lambda L: len(L["cols"]) + 1
rows = [(L["name"], L["title"], "List", L["purpose"], n_cols(L)) for L in LISTS] + \
       [(L["name"], L["title"], "Document library", L["purpose"], len(L["cols"])) for L in LIBRARIES]
sheet("Lists", ["Internal name", "Display name", "Type", "Purpose", "Custom columns (+Title for lists)"], rows, [22, 28, 18, 80, 16])

crow = []
for L in LISTS:
    crow.append((L["name"], "Title", L["title_display"], "Single line of text", "Yes", "", "", "Default Title column, renamed"))
    for (i, d, t, o) in L["cols"]:
        extra = o.get("choices") and "; ".join(o["choices"]) or (f"-> {o['list']}" if t == "lookup" else (o.get("formula", "")))
        rng = ""
        if "min" in o or "max" in o: rng = f"{o.get('min','')}..{o.get('max','')}"
        crow.append((L["name"], i, d, TYPE_LABEL[t], "Yes" if o.get("required") else "", "Yes" if o.get("indexed") else "", extra, "; ".join(x for x in [o.get("note",""), f"range {rng}" if rng else "", f"default {o['default']}" if 'default' in o else ""] if x)))
for L in LIBRARIES:
    for (i, d, t, o) in L["cols"]:
        extra = o.get("choices") and "; ".join(o["choices"]) or (f"-> {o['list']}" if t == "lookup" else "")
        crow.append((L["name"], i, d, TYPE_LABEL[t], "Yes" if o.get("required") else "", "Yes" if o.get("indexed") else "", extra, f"default {o['default']}" if 'default' in o else ""))
sheet("Columns", ["List / library", "Internal name", "Display name", "Type", "Required", "Indexed", "Choices / lookup target / formula", "Notes"], crow, [22, 22, 32, 22, 9, 9, 70, 50])

sheet("Relationships", ["From (many)", "Lookup column", "To (one)", "Cardinality"], RELATIONSHIPS, [24, 28, 24, 14])

srows = [(g, GROUP_LABEL[g]) for g in GROUPS]
ws = sheet("Security", ["SharePoint group", "Role / Permission by object"], srows, [22, 40])
start = ws.max_row + 2
ws.cell(start, 1, "Permission matrix").font = Font(bold=True)
hdr = ["Object"] + [GROUP_LABEL[g] for g in GROUPS]
for j, h in enumerate(hdr, 1):
    c = ws.cell(start + 1, j, h); c.fill, c.font = HFILL, HFONT; c.alignment = Alignment(wrap_text=True)
for r, p in enumerate(PERMS, start + 2):
    for j, v in enumerate(p, 1):
        c = ws.cell(r, j, v); c.alignment = Alignment(wrap_text=True, vertical="top"); c.border = BORDER
for col, w in zip("ABCDEFGH", [34, 26, 26, 30, 32, 30, 30, 30]):
    ws.column_dimensions[col].width = w

sheet("Workflows", ["Flow", "Trigger", "Steps", "Lists touched", "Notes"], WORKFLOWS, [28, 38, 80, 34, 50])
sheet("PowerApps", ["Screen", "Purpose", "Data sources", "Key logic / notes"], POWERAPPS, [28, 40, 44, 90])
sheet("Design Decisions", ["Topic", "Decision / recommendation"], GAPS, [30, 130])
sheet("Config seed", ["Key", "Value", "Description"], CONFIG_SEED, [26, 14, 60])
wb.save(f"{OUT}/MHAO_IAMS_Data_Model.xlsx")

# ---------------------------------------------------------------- PowerShell
def field_xml(i, d, t, o, disp=None):
    attrs = f'DisplayName="{escape(d, {chr(34): "&quot;"})}" Name="{i}" StaticName="{i}" Group="IAMS"'
    attrs += ' Required="TRUE"' if o.get("required") else ' Required="FALSE"'
    if o.get("indexed"): attrs += ' Indexed="TRUE"'
    if t == "text": return f'<Field Type="Text" {attrs} MaxLength="255" />'
    if t == "note": return f'<Field Type="Note" {attrs} NumLines="6" RichText="FALSE" />'
    if t == "choice":
        ch = "".join(f"<CHOICE>{escape(c)}</CHOICE>" for c in o["choices"])
        dflt = f"<Default>{escape(o['default'])}</Default>" if "default" in o else ""
        return f'<Field Type="Choice" {attrs} Format="Dropdown"><CHOICES>{ch}</CHOICES>{dflt}</Field>'
    if t == "number":
        mm = "".join(f' {k.capitalize()}="{o[k]}"' for k in ("min", "max") if k in o)
        dflt = f"<Default>{o['default']}</Default>" if "default" in o else ""
        return f'<Field Type="Number" {attrs}{mm}>{dflt}</Field>'
    if t == "date": return f'<Field Type="DateTime" {attrs} Format="DateOnly" />'
    if t == "bool": return f'<Field Type="Boolean" {attrs}><Default>{o.get("default","0")}</Default></Field>'
    if t == "user": return f'<Field Type="User" {attrs} List="UserInfo" ShowField="ImnName" UserSelectionMode="PeopleOnly" />'
    if t == "usermulti": return f'<Field Type="UserMulti" {attrs} List="UserInfo" ShowField="ImnName" UserSelectionMode="PeopleOnly" Mult="TRUE" />'
    if t == "url": return f'<Field Type="URL" {attrs} Format="Hyperlink" />'
    if t == "lookup": return f'<Field Type="Lookup" {attrs} List="@@LIST:{o["list"]}@@" ShowField="Title" />'
    if t == "calc":
        refs = "".join(f'<FieldRef Name="{r}" />' for r in o["refs"])
        return f'<Field Type="Calculated" {attrs} ResultType="{o["result"]}" ReadOnly="TRUE"><Formula>{escape(re.sub(r"\[(\w+)\]", lambda m: "[" + (disp or {}).get(m.group(1), m.group(1)) + "]", o["formula"]))}</Formula><FieldRefs>{refs}</FieldRefs></Field>'
    raise ValueError(t)

def ps_str(s): return "'" + s.replace("'", "''") + "'"

def perm_role(s, obj, grp):
    s = s.strip()
    if s.startswith("No access"): return None
    low = s.lower()
    if any(k in low for k in ("assigned", " own", "(own", "issued only", "via forms", "respond")): return None  # qualified -> item/folder level
    for k in ("Full Control", "Edit", "Contribute", "Read"):
        if s.startswith(k): return k
    return None

ps = []
ps.append("""<#
 MHAO IAMS - SharePoint provisioning script (generated from MHAO_IAMS_Data_Model.xlsx spec)
 Requires: PnP.PowerShell (Install-Module PnP.PowerShell), Site Owner rights on the target site.
 Usage:    .\\Provision-IAMS.ps1 -SiteUrl https://<tenant>.sharepoint.com/sites/InternalAuditTest -ClientId <app ID>
           App-only (Sites.Selected): add  -Tenant YOURTENANT.onmicrosoft.com -CertificatePath C:\\path\\app.pfx -CertificatePassword (Read-Host -AsSecureString)
           (PnP.PowerShell 2.x needs your own Entra app registration: see Register-PnPEntraIDAppForInteractiveLogin)
 NOTE: Written without access to a live tenant - run first on a TEST site. Script is re-runnable (skips existing lists/fields).
#>
param(
  [Parameter(Mandatory=$true)][string]$SiteUrl,
  [Parameter(Mandatory=$true)][string]$ClientId,
  [string]$Tenant,                 # e.g. YOURTENANT.onmicrosoft.com (needed for certificate / app-only sign-in)
  [string]$CertificatePath,        # .pfx path -> app-only sign-in with Sites.Selected
  [securestring]$CertificatePassword
)
$ErrorActionPreference = 'Stop'
if ($CertificatePath) {
  # App-only: app has SharePoint 'Sites.Selected' (Application) + a FullControl grant on this ONE site
  Connect-PnPOnline -Url $SiteUrl -ClientId $ClientId -Tenant $Tenant -CertificatePath $CertificatePath -CertificatePassword $CertificatePassword
} else {
  Connect-PnPOnline -Url $SiteUrl -Interactive -ClientId $ClientId
}

function Update-DefaultView($list, [string[]]$fields) {
  try {
    $v = Get-PnPView -List $list | Where-Object { $_.DefaultView } | Select-Object -First 1
    if (-not $v) { Write-Warning "  no default view found: $list"; return }
    try { Set-PnPView -List $list -Identity $v.Id -Fields $fields | Out-Null }
    catch { Set-PnPView -List $list -Identity $v.Title -Fields $fields | Out-Null }
    Write-Host "  view updated: $list"
  } catch { Write-Warning "  view NOT updated for ${list}: $($_.Exception.Message)" }
}
function Ensure-List($name, $template) {
  if (-not (Get-PnPList -Identity $name -ErrorAction SilentlyContinue)) {
    Write-Host "Creating $name"; New-PnPList -Title $name -Url $(if ($template -eq 'DocumentLibrary') { $name } else { "Lists/$name" }) -Template $template -OnQuickLaunch | Out-Null
  } else { Write-Host "Exists: $name" }
}
function Ensure-Field($list, $internal, $xml, $display) {
  $f = Get-PnPField -List $list -Identity $internal -ErrorAction SilentlyContinue
  if ($f) {
    if ($display -and $f.Title -ne $display) { Set-PnPField -List $list -Identity $internal -Values @{Title=$display} | Out-Null; Write-Host "  renamed: $list.$internal -> $display" }
    else { Write-Host "  field exists: $list.$internal" }
    return
  }
  $xml = [regex]::Replace($xml, '@@LIST:([A-Za-z_]+)@@', { param($m) '{' + (Get-PnPList -Identity $m.Groups[1].Value).Id.ToString() + '}' })
  Add-PnPFieldFromXml -List $list -FieldXml $xml | Out-Null
  Write-Host "  + $list.$internal"
}
""")
ps.append("# ---- 0. Re-runs: lists get friendly titles at the end of a run, so restore the IA_ names first (found by their address)")
ps.append("$allLists = Get-PnPList -Includes RootFolder")
for L in LISTS + LIBRARIES:
    n = L['name']
    ps.append(f"$l = $allLists | Where-Object {{ $_.RootFolder.Name -eq {ps_str(n)} }} | Select-Object -First 1; if ($l -and $l.Title -ne {ps_str(n)}) {{ Set-PnPList -Identity $l.Id -Title {ps_str(n)} | Out-Null; Write-Host '  restored name: {n}' }}")
ps.append("# ---- 1. Lists and libraries")
for L in LISTS: ps.append(f"Ensure-List {ps_str(L['name'])} 'GenericList'")
for L in LIBRARIES: ps.append(f"Ensure-List {ps_str(L['name'])} 'DocumentLibrary'")
ps.append("\n# ---- 2. Columns (dependency order: lookup targets are created first)")
for L in LISTS:
    ps.append(f"Set-PnPField -List {ps_str(L['name'])} -Identity 'Title' -Values @{{Title={ps_str(L['title_display'])}}} | Out-Null")
    for (i, d, t, o) in L["cols"]:
        ps.append(f"Ensure-Field {ps_str(L['name'])} {ps_str(i)} {ps_str(field_xml(i, d, t, o, {c[0]: c[1] for c in L['cols']}))} {ps_str(d)}")
for L in LIBRARIES:
    for (i, d, t, o) in L["cols"]:
        ps.append(f"Ensure-Field {ps_str(L['name'])} {ps_str(i)} {ps_str(field_xml(i, d, t, o, {c[0]: c[1] for c in L['cols']}))} {ps_str(d)}")

ps.append("\n# ---- 3. Versioning, list settings, audit-log append-only text")
for L in LISTS + LIBRARIES:
    ps.append(f"Set-PnPList -Identity {ps_str(L['name'])} -EnableVersioning $true -MajorVersions 50 | Out-Null")
ps.append("Set-PnPList -Identity 'IA_AuditLog' -EnableAttachments $false | Out-Null")

ps.append("\n# ---- 3b. Show the columns in each default view (long text columns left out to keep views readable)")
for L in LISTS:
    flds = ["LinkTitle"] + [c[0] for c in L["cols"] if c[2] != "note"]
    ps.append(f"Update-DefaultView {ps_str(L['name'])} @({', '.join(ps_str(x) for x in flds)})")
for L in LIBRARIES:
    flds = ["DocIcon", "LinkFilename"] + [c[0] for c in L["cols"] if c[2] != "note"]
    ps.append(f"Update-DefaultView {ps_str(L['name'])} @({', '.join(ps_str(x) for x in flds)})")

ps.append("\n# ---- 4. Evidence/Working-paper subfolder template (created per engagement by flow WF1; sample root only)")
ps.append("# Subfolders per engagement: " + ", ".join(EVIDENCE_SUBFOLDERS))

ps.append("\n# ---- 5. Seed configuration values")
for k, v, dsc in CONFIG_SEED:
    ps.append(f"if (-not (Get-PnPListItem -List 'IA_Config' -Query \"<View><Query><Where><Eq><FieldRef Name='Title'/><Value Type='Text'>{k}</Value></Eq></Where></Query></View>\")) {{ Add-PnPListItem -List 'IA_Config' -Values @{{Title={ps_str(k)}; ConfigValue={ps_str(v if v else 'TBD')}; ConfigDescription={ps_str(dsc)}}} | Out-Null }}")

ps.append("\n# ---- 6. Groups and baseline list-level permissions")
ps.append("# Only UNQUALIFIED permissions are applied. Anything marked '(assigned)', '(own ...)' or 'issued only' in the Security sheet")
ps.append("# is intentionally NOT granted here; it is applied at folder/item level by flows WF1/WF3 so users never see more than intended.")
for g in GROUPS:
    ps.append(f"if (-not (Get-PnPGroup -Identity {ps_str(g)} -ErrorAction SilentlyContinue)) {{ New-PnPGroup -Title {ps_str(g)} -Description {ps_str(GROUP_LABEL[g])} | Out-Null }}")
roles_by_group = {g: [] for g in GROUPS}
for p in PERMS:
    if p[0] == "Power BI": continue
    for obj in p[0].split(" / "):
        for g, val in zip(GROUPS, p[1:]):
            r = perm_role(val, obj, g)
            if r: roles_by_group[g].append((obj, r))
objs = sorted({o for g in roles_by_group.values() for o, _ in g} | {o for p in PERMS if p[0] != "Power BI" for o in p[0].split(" / ")})
for obj in objs:
    ps.append(f"Set-PnPList -Identity {ps_str(obj)} -BreakRoleInheritance -CopyRoleAssignments:$false -ClearSubscopes | Out-Null")
    for g in GROUPS:
        for o, r in roles_by_group[g]:
            if o == obj: ps.append(f"Set-PnPListPermission -Identity {ps_str(obj)} -Group {ps_str(g)} -AddRole {ps_str(r)}")

ps.append("\n# ---- 7. Friendly display titles (done last so lookups above resolve by internal name)")
for L in LISTS + LIBRARIES:
    ps.append(f"Set-PnPList -Identity {ps_str(L['name'])} -Title {ps_str(L['title'])} | Out-Null")
ps.append("\nWrite-Host 'IAMS provisioning complete. Next: add members to IA_* groups, set Entity CEO/Dept Head data, build flows WF0-WF7.'")
open(f"{OUT}/Provision-IAMS.ps1", "w", encoding="utf-8-sig").write("\n".join(ps) + "\n")
print("ok", len(ps))

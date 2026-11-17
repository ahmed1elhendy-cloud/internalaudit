import openpyxl, json, datetime
wb = openpyxl.load_workbook('/mnt/user-data/uploads/Internal Audit Management System/MHAO_IAMS_Import_Templates.xlsx')
def rows(n):
    return [r for r in wb[n].iter_rows(min_row=2, values_only=True) if any(c not in (None, "") for c in r)]
def s(v): return None if v in (None, "") else str(v).strip()
def d(v): return v.strftime("%Y-%m-%d") if hasattr(v, "year") else s(v)
ents = [dict(Title=s(r[0]), EntityCode=s(r[1]), EntityType=s(r[2]), Country=s(r[3]), EntityHead=s(r[4]), EntityCEO=s(r[5]), Active=(s(r[6]) or "Yes") == "Yes") for r in rows("Entities")]
deps = [dict(Title=s(r[0]), Entity=s(r[1]), DepartmentHead=s(r[2]), Active=(s(r[3]) or "Yes") == "Yes") for r in rows("Departments")]
uni = []
for i, r in enumerate(rows("AuditUniverse"), 1):
    uni.append(dict(Title=s(r[0]), AuditAreaID=f"AU-{i:04d}", Entity=s(r[1]), Department=s(r[2]), ProcessCategory=s(r[3]), ProcessOwner=s(r[4]),
                    RiskRating=s(r[5]), RiskScore=r[6], LastAuditDate=d(r[7]), AuditFrequency=s(r[8]), UniverseStatus=s(r[9]) or "Active"))
cfg = {r[0]: s(r[1]) for r in rows("Config") if r[0] in ("ReminderDays1", "ReminderDays2", "EscalateCEOAfterDays", "GroupCEOEmail", "HeadOfIAEmail") and s(r[1])}
data = json.dumps(dict(entities=ents, departments=deps, universe=uni, config=cfg), ensure_ascii=False, indent=1)
assert "\n'@" not in data
ps = r'''<#
 MHAO IAMS - load reference data (Entities, Departments, Audit Universe, Config) into the test site.
 Data below was read from MHAO_IAMS_Import_Templates.xlsx. Safe to re-run: existing rows are skipped (matched by name).
 Usage: same sign-in options as Provision-IAMS.ps1 (-SiteUrl -ClientId -Tenant -CertificatePath -CertificatePassword)
#>
param(
  [Parameter(Mandatory=$true)][string]$SiteUrl,
  [Parameter(Mandatory=$true)][string]$ClientId,
  [string]$Tenant, [string]$CertificatePath, [securestring]$CertificatePassword
)
$ErrorActionPreference = 'Stop'
if ($CertificatePath) { Connect-PnPOnline -Url $SiteUrl -ClientId $ClientId -Tenant $Tenant -CertificatePath $CertificatePath -CertificatePassword $CertificatePassword }
else { Connect-PnPOnline -Url $SiteUrl -Interactive -ClientId $ClientId }

# restore IA_ names if a previous run renamed the lists to friendly titles
$allLists = Get-PnPList -Includes RootFolder
foreach ($n in 'IA_Entities','IA_Departments','IA_AuditUniverse','IA_Config') {
  $l = $allLists | Where-Object { $_.RootFolder.Name -eq $n } | Select-Object -First 1
  if ($l -and $l.Title -ne $n) { Set-PnPList -Identity $l.Id -Title $n | Out-Null }
}

$data = @'
''' + data + r'''
'@ | ConvertFrom-Json

function Clean($h) { $o = @{}; foreach ($k in $h.Keys) { if ($null -ne $h[$k] -and "$($h[$k])" -ne '') { $o[$k] = $h[$k] } }; $o }
function Add-Row($list, $values, $label) {
  try { Add-PnPListItem -List $list -Values (Clean $values) | Out-Null; return $true }
  catch { Write-Warning "  FAILED ${label}: $($_.Exception.Message)"; return $false }
}

# ---- Entities
Write-Host "Entities"
$existing = @{}; Get-PnPListItem -List 'IA_Entities' -PageSize 500 | ForEach-Object { $existing[$_['Title']] = $_.Id }
$entId = @{}
foreach ($e in $data.entities) {
  if ($existing.ContainsKey($e.Title)) { $entId[$e.Title] = $existing[$e.Title]; Write-Host "  exists: $($e.Title)"; continue }
  $vals = @{ Title=$e.Title; EntityCode=$e.EntityCode; EntityType=$e.EntityType; Country=$e.Country; EntityHead=$e.EntityHead; EntityCEO=$e.EntityCEO; Active=[bool]$e.Active }
  if (Add-Row 'IA_Entities' $vals $e.Title) { Write-Host "  + $($e.Title)" }
}
Get-PnPListItem -List 'IA_Entities' -PageSize 500 | ForEach-Object { $entId[$_['Title']] = $_.Id }

# ---- Departments
Write-Host "Departments"
$existing = @{}; Get-PnPListItem -List 'IA_Departments' -PageSize 500 | ForEach-Object { $existing["$($_['Title'])|$($_['Entity'].LookupId)"] = $_.Id }
$depId = @{}
foreach ($d in $data.departments) {
  $eid = $entId[$d.Entity]; if (-not $eid) { Write-Warning "  unknown entity '$($d.Entity)' for department '$($d.Title)'"; continue }
  $key = "$($d.Title)|$eid"
  if ($existing.ContainsKey($key)) { Write-Host "  exists: $($d.Entity) / $($d.Title)"; continue }
  $vals = @{ Title=$d.Title; Entity=$eid; DepartmentHead=$d.DepartmentHead; Active=[bool]$d.Active }
  if (Add-Row 'IA_Departments' $vals "$($d.Entity)/$($d.Title)") { Write-Host "  + $($d.Entity) / $($d.Title)" }
}
Get-PnPListItem -List 'IA_Departments' -PageSize 500 | ForEach-Object { $depId["$($_['Title'])|$($_['Entity'].LookupId)"] = $_.Id }

# ---- Audit Universe
Write-Host "Audit Universe"
$existing = @{}; Get-PnPListItem -List 'IA_AuditUniverse' -PageSize 500 | ForEach-Object { $existing["$($_['Title'])|$($_['Entity'].LookupId)"] = $_.Id }
foreach ($u in $data.universe) {
  $eid = $entId[$u.Entity]; if (-not $eid) { Write-Warning "  unknown entity '$($u.Entity)' for '$($u.Title)'"; continue }
  $key = "$($u.Title)|$eid"
  if ($existing.ContainsKey($key)) { Write-Host "  exists: $($u.Entity) / $($u.Title)"; continue }
  $vals = @{ Title=$u.Title; AuditAreaID=$u.AuditAreaID; Entity=$eid; ProcessCategory=$u.ProcessCategory; ProcessOwner=$u.ProcessOwner
             RiskRating=$u.RiskRating; RiskScore=$u.RiskScore; LastAuditDate=$u.LastAuditDate; AuditFrequency=$u.AuditFrequency; UniverseStatus=$u.UniverseStatus }
  if ($u.Department) { $did = $depId["$($u.Department)|$eid"]; if ($did) { $vals['Department'] = $did } else { Write-Warning "  department '$($u.Department)' not found under '$($u.Entity)' for '$($u.Title)'" } }
  if (Add-Row 'IA_AuditUniverse' $vals "$($u.Entity)/$($u.Title)") { Write-Host "  + $($u.AuditAreaID) $($u.Entity) / $($u.Title)" }
}

# ---- Config values (only those you filled in)
Write-Host "Config"
foreach ($p in $data.config.PSObject.Properties) {
  $item = Get-PnPListItem -List 'IA_Config' -PageSize 100 | Where-Object { $_['Title'] -eq $p.Name } | Select-Object -First 1
  if ($item) { Set-PnPListItem -List 'IA_Config' -Identity $item.Id -Values @{ ConfigValue = $p.Value } | Out-Null; Write-Host "  set $($p.Name)" }
}

# friendly titles again
$friendly = @{ 'IA_Entities'='Entities'; 'IA_Departments'='Departments'; 'IA_AuditUniverse'='Audit Universe'; 'IA_Config'='IA Configuration' }
foreach ($k in $friendly.Keys) { Set-PnPList -Identity $k -Title $friendly[$k] | Out-Null }
Write-Host "Data load complete."
'''
open('/mnt/user-data/outputs/Import-IAMS-Data.ps1', 'w', encoding='utf-8-sig').write(ps)
print(len(ents), len(deps), len(uni), cfg)

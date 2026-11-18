<#
 MHAO IAMS - SharePoint provisioning script (generated from MHAO_IAMS_Data_Model.xlsx spec)
 Requires: PnP.PowerShell (Install-Module PnP.PowerShell), Site Owner rights on the target site.
 Usage:    .\Provision-IAMS.ps1 -SiteUrl https://<tenant>.sharepoint.com/sites/InternalAuditTest -ClientId <app ID>
           App-only (Sites.Selected): add  -Tenant YOURTENANT.onmicrosoft.com -CertificatePath C:\path\app.pfx -CertificatePassword (Read-Host -AsSecureString)
           (PnP.PowerShell 2.x needs your own Entra app registration: see Register-PnPEntraIDAppForInteractiveLogin)
 NOTE: Matches the live test-site schema (see live_schema.txt). Run first on a TEST site. Re-runnable (skips existing lists/fields).
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

# ---- 0. Re-runs: lists get friendly titles at the end of a run, so restore the IA_ names first (found by their address)
$allLists = Get-PnPList -Includes RootFolder
$l = $allLists | Where-Object { $_.RootFolder.Name -eq 'IA_Entities' } | Select-Object -First 1; if ($l -and $l.Title -ne 'IA_Entities') { Set-PnPList -Identity $l.Id -Title 'IA_Entities' | Out-Null; Write-Host '  restored name: IA_Entities' }
$l = $allLists | Where-Object { $_.RootFolder.Name -eq 'IA_Departments' } | Select-Object -First 1; if ($l -and $l.Title -ne 'IA_Departments') { Set-PnPList -Identity $l.Id -Title 'IA_Departments' | Out-Null; Write-Host '  restored name: IA_Departments' }
$l = $allLists | Where-Object { $_.RootFolder.Name -eq 'IA_AuditUniverse' } | Select-Object -First 1; if ($l -and $l.Title -ne 'IA_AuditUniverse') { Set-PnPList -Identity $l.Id -Title 'IA_AuditUniverse' | Out-Null; Write-Host '  restored name: IA_AuditUniverse' }
$l = $allLists | Where-Object { $_.RootFolder.Name -eq 'IA_RiskRegister' } | Select-Object -First 1; if ($l -and $l.Title -ne 'IA_RiskRegister') { Set-PnPList -Identity $l.Id -Title 'IA_RiskRegister' | Out-Null; Write-Host '  restored name: IA_RiskRegister' }
$l = $allLists | Where-Object { $_.RootFolder.Name -eq 'IA_AuditPlan' } | Select-Object -First 1; if ($l -and $l.Title -ne 'IA_AuditPlan') { Set-PnPList -Identity $l.Id -Title 'IA_AuditPlan' | Out-Null; Write-Host '  restored name: IA_AuditPlan' }
$l = $allLists | Where-Object { $_.RootFolder.Name -eq 'IA_Engagements' } | Select-Object -First 1; if ($l -and $l.Title -ne 'IA_Engagements') { Set-PnPList -Identity $l.Id -Title 'IA_Engagements' | Out-Null; Write-Host '  restored name: IA_Engagements' }
$l = $allLists | Where-Object { $_.RootFolder.Name -eq 'IA_Milestones' } | Select-Object -First 1; if ($l -and $l.Title -ne 'IA_Milestones') { Set-PnPList -Identity $l.Id -Title 'IA_Milestones' | Out-Null; Write-Host '  restored name: IA_Milestones' }
$l = $allLists | Where-Object { $_.RootFolder.Name -eq 'IA_Findings' } | Select-Object -First 1; if ($l -and $l.Title -ne 'IA_Findings') { Set-PnPList -Identity $l.Id -Title 'IA_Findings' | Out-Null; Write-Host '  restored name: IA_Findings' }
$l = $allLists | Where-Object { $_.RootFolder.Name -eq 'IA_ActionPlans' } | Select-Object -First 1; if ($l -and $l.Title -ne 'IA_ActionPlans') { Set-PnPList -Identity $l.Id -Title 'IA_ActionPlans' | Out-Null; Write-Host '  restored name: IA_ActionPlans' }
$l = $allLists | Where-Object { $_.RootFolder.Name -eq 'IA_FollowUps' } | Select-Object -First 1; if ($l -and $l.Title -ne 'IA_FollowUps') { Set-PnPList -Identity $l.Id -Title 'IA_FollowUps' | Out-Null; Write-Host '  restored name: IA_FollowUps' }
$l = $allLists | Where-Object { $_.RootFolder.Name -eq 'IA_CSARegister' } | Select-Object -First 1; if ($l -and $l.Title -ne 'IA_CSARegister') { Set-PnPList -Identity $l.Id -Title 'IA_CSARegister' | Out-Null; Write-Host '  restored name: IA_CSARegister' }
$l = $allLists | Where-Object { $_.RootFolder.Name -eq 'IA_AuditLog' } | Select-Object -First 1; if ($l -and $l.Title -ne 'IA_AuditLog') { Set-PnPList -Identity $l.Id -Title 'IA_AuditLog' | Out-Null; Write-Host '  restored name: IA_AuditLog' }
$l = $allLists | Where-Object { $_.RootFolder.Name -eq 'IA_Config' } | Select-Object -First 1; if ($l -and $l.Title -ne 'IA_Config') { Set-PnPList -Identity $l.Id -Title 'IA_Config' | Out-Null; Write-Host '  restored name: IA_Config' }
$l = $allLists | Where-Object { $_.RootFolder.Name -eq 'IA_Questionnaires' } | Select-Object -First 1; if ($l -and $l.Title -ne 'IA_Questionnaires') { Set-PnPList -Identity $l.Id -Title 'IA_Questionnaires' | Out-Null; Write-Host '  restored name: IA_Questionnaires' }
$l = $allLists | Where-Object { $_.RootFolder.Name -eq 'IA_QnrSections' } | Select-Object -First 1; if ($l -and $l.Title -ne 'IA_QnrSections') { Set-PnPList -Identity $l.Id -Title 'IA_QnrSections' | Out-Null; Write-Host '  restored name: IA_QnrSections' }
$l = $allLists | Where-Object { $_.RootFolder.Name -eq 'IA_QnrItems' } | Select-Object -First 1; if ($l -and $l.Title -ne 'IA_QnrItems') { Set-PnPList -Identity $l.Id -Title 'IA_QnrItems' | Out-Null; Write-Host '  restored name: IA_QnrItems' }
$l = $allLists | Where-Object { $_.RootFolder.Name -eq 'IA_QnrUploads' } | Select-Object -First 1; if ($l -and $l.Title -ne 'IA_QnrUploads') { Set-PnPList -Identity $l.Id -Title 'IA_QnrUploads' | Out-Null; Write-Host '  restored name: IA_QnrUploads' }
$l = $allLists | Where-Object { $_.RootFolder.Name -eq 'Knowledge Index' } | Select-Object -First 1; if ($l -and $l.Title -ne 'Knowledge Index') { Set-PnPList -Identity $l.Id -Title 'Knowledge Index' | Out-Null; Write-Host '  restored name: Knowledge Index' }
$l = $allLists | Where-Object { $_.RootFolder.Name -eq 'IA_WorkingPapers' } | Select-Object -First 1; if ($l -and $l.Title -ne 'IA_WorkingPapers') { Set-PnPList -Identity $l.Id -Title 'IA_WorkingPapers' | Out-Null; Write-Host '  restored name: IA_WorkingPapers' }
$l = $allLists | Where-Object { $_.RootFolder.Name -eq 'IA_Evidence' } | Select-Object -First 1; if ($l -and $l.Title -ne 'IA_Evidence') { Set-PnPList -Identity $l.Id -Title 'IA_Evidence' | Out-Null; Write-Host '  restored name: IA_Evidence' }
$l = $allLists | Where-Object { $_.RootFolder.Name -eq 'IA_QnrFiles' } | Select-Object -First 1; if ($l -and $l.Title -ne 'IA_QnrFiles') { Set-PnPList -Identity $l.Id -Title 'IA_QnrFiles' | Out-Null; Write-Host '  restored name: IA_QnrFiles' }
$l = $allLists | Where-Object { $_.RootFolder.Name -eq 'IA_QnrTemplates' } | Select-Object -First 1; if ($l -and $l.Title -ne 'IA_QnrTemplates') { Set-PnPList -Identity $l.Id -Title 'IA_QnrTemplates' | Out-Null; Write-Host '  restored name: IA_QnrTemplates' }
$l = $allLists | Where-Object { $_.RootFolder.Name -eq 'Knowledge Documents' } | Select-Object -First 1; if ($l -and $l.Title -ne 'Knowledge Documents') { Set-PnPList -Identity $l.Id -Title 'Knowledge Documents' | Out-Null; Write-Host '  restored name: Knowledge Documents' }
$l = $allLists | Where-Object { $_.RootFolder.Name -eq 'IA_Reports' } | Select-Object -First 1; if ($l -and $l.Title -ne 'IA_Reports') { Set-PnPList -Identity $l.Id -Title 'IA_Reports' | Out-Null; Write-Host '  restored name: IA_Reports' }
# ---- 1. Lists and libraries
Ensure-List 'IA_Entities' 'GenericList'
Ensure-List 'IA_Departments' 'GenericList'
Ensure-List 'IA_AuditUniverse' 'GenericList'
Ensure-List 'IA_RiskRegister' 'GenericList'
Ensure-List 'IA_AuditPlan' 'GenericList'
Ensure-List 'IA_Engagements' 'GenericList'
Ensure-List 'IA_Milestones' 'GenericList'
Ensure-List 'IA_Findings' 'GenericList'
Ensure-List 'IA_ActionPlans' 'GenericList'
Ensure-List 'IA_FollowUps' 'GenericList'
Ensure-List 'IA_CSARegister' 'GenericList'
Ensure-List 'IA_AuditLog' 'GenericList'
Ensure-List 'IA_Config' 'GenericList'
Ensure-List 'IA_Questionnaires' 'GenericList'
Ensure-List 'IA_QnrSections' 'GenericList'
Ensure-List 'IA_QnrItems' 'GenericList'
Ensure-List 'IA_QnrUploads' 'GenericList'
Ensure-List 'Knowledge Index' 'GenericList'
Ensure-List 'IA_WorkingPapers' 'DocumentLibrary'
Ensure-List 'IA_Evidence' 'DocumentLibrary'
Ensure-List 'IA_QnrFiles' 'DocumentLibrary'
Ensure-List 'IA_QnrTemplates' 'DocumentLibrary'
Ensure-List 'Knowledge Documents' 'DocumentLibrary'
Ensure-List 'IA_Reports' 'DocumentLibrary'

# ---- 2. Columns (dependency order: lookup targets are created first)
Set-PnPField -List 'IA_Entities' -Identity 'Title' -Values @{Title='Entity Name'} | Out-Null
Ensure-Field 'IA_Entities' 'EntityCode' '<Field Type="Text" DisplayName="Entity Code" Name="EntityCode" StaticName="EntityCode" Group="IAMS" Required="TRUE" Indexed="TRUE" MaxLength="255" />' 'Entity Code'
Ensure-Field 'IA_Entities' 'EntityType' '<Field Type="Choice" DisplayName="Entity Type" Name="EntityType" StaticName="EntityType" Group="IAMS" Required="FALSE" Format="Dropdown"><CHOICES><CHOICE>Parent</CHOICE><CHOICE>Subsidiary</CHOICE><CHOICE>Associate</CHOICE><CHOICE>Joint Venture</CHOICE></CHOICES></Field>' 'Entity Type'
Ensure-Field 'IA_Entities' 'Country' '<Field Type="Text" DisplayName="Country" Name="Country" StaticName="Country" Group="IAMS" Required="FALSE" MaxLength="255" />' 'Country'
Ensure-Field 'IA_Entities' 'EntityHead' '<Field Type="User" DisplayName="Entity Head / MD" Name="EntityHead" StaticName="EntityHead" Group="IAMS" Required="FALSE" List="UserInfo" ShowField="ImnName" UserSelectionMode="PeopleOnly" />' 'Entity Head / MD'
Ensure-Field 'IA_Entities' 'EntityCEO' '<Field Type="User" DisplayName="Entity CEO (escalation L2)" Name="EntityCEO" StaticName="EntityCEO" Group="IAMS" Required="FALSE" List="UserInfo" ShowField="ImnName" UserSelectionMode="PeopleOnly" />' 'Entity CEO (escalation L2)'
Ensure-Field 'IA_Entities' 'Active' '<Field Type="Boolean" DisplayName="Active" Name="Active" StaticName="Active" Group="IAMS" Required="FALSE"><Default>1</Default></Field>' 'Active'
Set-PnPField -List 'IA_Departments' -Identity 'Title' -Values @{Title='Department Name'} | Out-Null
Ensure-Field 'IA_Departments' 'Entity' '<Field Type="Lookup" DisplayName="Entity" Name="Entity" StaticName="Entity" Group="IAMS" Required="TRUE" Indexed="TRUE" List="@@LIST:IA_Entities@@" ShowField="Title" />' 'Entity'
Ensure-Field 'IA_Departments' 'DepartmentHead' '<Field Type="User" DisplayName="Department Head" Name="DepartmentHead" StaticName="DepartmentHead" Group="IAMS" Required="FALSE" List="UserInfo" ShowField="ImnName" UserSelectionMode="PeopleOnly" />' 'Department Head'
Ensure-Field 'IA_Departments' 'Active' '<Field Type="Boolean" DisplayName="Active" Name="Active" StaticName="Active" Group="IAMS" Required="FALSE"><Default>1</Default></Field>' 'Active'
Set-PnPField -List 'IA_AuditUniverse' -Identity 'Title' -Values @{Title='Auditable Area'} | Out-Null
Ensure-Field 'IA_AuditUniverse' 'AuditAreaID' '<Field Type="Text" DisplayName="Audit Area ID" Name="AuditAreaID" StaticName="AuditAreaID" Group="IAMS" Required="FALSE" Indexed="TRUE" MaxLength="255" />' 'Audit Area ID'
Ensure-Field 'IA_AuditUniverse' 'Entity' '<Field Type="Lookup" DisplayName="Entity" Name="Entity" StaticName="Entity" Group="IAMS" Required="TRUE" Indexed="TRUE" List="@@LIST:IA_Entities@@" ShowField="Title" />' 'Entity'
Ensure-Field 'IA_AuditUniverse' 'Department' '<Field Type="Lookup" DisplayName="Department" Name="Department" StaticName="Department" Group="IAMS" Required="FALSE" Indexed="TRUE" List="@@LIST:IA_Departments@@" ShowField="Title" />' 'Department'
Ensure-Field 'IA_AuditUniverse' 'ProcessCategory' '<Field Type="Choice" DisplayName="Process Category" Name="ProcessCategory" StaticName="ProcessCategory" Group="IAMS" Required="FALSE" Format="Dropdown"><CHOICES><CHOICE>Finance</CHOICE><CHOICE>Procurement</CHOICE><CHOICE>HR &amp; Payroll</CHOICE><CHOICE>IT</CHOICE><CHOICE>Sales</CHOICE><CHOICE>Operations</CHOICE><CHOICE>Legal &amp; Compliance</CHOICE><CHOICE>Projects</CHOICE><CHOICE>Treasury</CHOICE><CHOICE>Other</CHOICE></CHOICES></Field>' 'Process Category'
Ensure-Field 'IA_AuditUniverse' 'ProcessOwner' '<Field Type="User" DisplayName="Process Owner" Name="ProcessOwner" StaticName="ProcessOwner" Group="IAMS" Required="FALSE" List="UserInfo" ShowField="ImnName" UserSelectionMode="PeopleOnly" />' 'Process Owner'
Ensure-Field 'IA_AuditUniverse' 'RiskRating' '<Field Type="Choice" DisplayName="Risk Rating" Name="RiskRating" StaticName="RiskRating" Group="IAMS" Required="FALSE" Indexed="TRUE" Format="Dropdown"><CHOICES><CHOICE>Critical</CHOICE><CHOICE>High</CHOICE><CHOICE>Medium</CHOICE><CHOICE>Low</CHOICE></CHOICES></Field>' 'Risk Rating'
Ensure-Field 'IA_AuditUniverse' 'RiskScore' '<Field Type="Number" DisplayName="Risk Score (1-25)" Name="RiskScore" StaticName="RiskScore" Group="IAMS" Required="FALSE" Min="1" Max="25"></Field>' 'Risk Score (1-25)'
Ensure-Field 'IA_AuditUniverse' 'LastAuditDate' '<Field Type="DateTime" DisplayName="Last Audit Date" Name="LastAuditDate" StaticName="LastAuditDate" Group="IAMS" Required="FALSE" Format="DateOnly" />' 'Last Audit Date'
Ensure-Field 'IA_AuditUniverse' 'AuditFrequency' '<Field Type="Choice" DisplayName="Audit Frequency" Name="AuditFrequency" StaticName="AuditFrequency" Group="IAMS" Required="FALSE" Format="Dropdown"><CHOICES><CHOICE>Annual</CHOICE><CHOICE>18 Months</CHOICE><CHOICE>2 Years</CHOICE><CHOICE>3 Years</CHOICE></CHOICES></Field>' 'Audit Frequency'
Ensure-Field 'IA_AuditUniverse' 'NextAuditDate' '<Field Type="DateTime" DisplayName="Next Audit Date" Name="NextAuditDate" StaticName="NextAuditDate" Group="IAMS" Required="FALSE" Format="DateOnly" />' 'Next Audit Date'
Ensure-Field 'IA_AuditUniverse' 'UniverseStatus' '<Field Type="Choice" DisplayName="Status" Name="UniverseStatus" StaticName="UniverseStatus" Group="IAMS" Required="FALSE" Format="Dropdown"><CHOICES><CHOICE>Active</CHOICE><CHOICE>Retired</CHOICE><CHOICE>On Hold</CHOICE></CHOICES><Default>Active</Default></Field>' 'Status'
Set-PnPField -List 'IA_RiskRegister' -Identity 'Title' -Values @{Title='Risk Title'} | Out-Null
Ensure-Field 'IA_RiskRegister' 'RiskID' '<Field Type="Text" DisplayName="Risk ID" Name="RiskID" StaticName="RiskID" Group="IAMS" Required="FALSE" Indexed="TRUE" MaxLength="255" />' 'Risk ID'
Ensure-Field 'IA_RiskRegister' 'RiskDescription' '<Field Type="Note" DisplayName="Risk Description" Name="RiskDescription" StaticName="RiskDescription" Group="IAMS" Required="FALSE" NumLines="6" RichText="FALSE" />' 'Risk Description'
Ensure-Field 'IA_RiskRegister' 'AuditArea' '<Field Type="Lookup" DisplayName="Audit Area" Name="AuditArea" StaticName="AuditArea" Group="IAMS" Required="TRUE" Indexed="TRUE" List="@@LIST:IA_AuditUniverse@@" ShowField="Title" />' 'Audit Area'
Ensure-Field 'IA_RiskRegister' 'Entity' '<Field Type="Lookup" DisplayName="Entity" Name="Entity" StaticName="Entity" Group="IAMS" Required="FALSE" Indexed="TRUE" List="@@LIST:IA_Entities@@" ShowField="Title" />' 'Entity'
Ensure-Field 'IA_RiskRegister' 'RiskCategory' '<Field Type="Choice" DisplayName="Risk Category" Name="RiskCategory" StaticName="RiskCategory" Group="IAMS" Required="FALSE" Format="Dropdown"><CHOICES><CHOICE>Strategic</CHOICE><CHOICE>Operational</CHOICE><CHOICE>Financial</CHOICE><CHOICE>Compliance</CHOICE><CHOICE>IT &amp; Cyber</CHOICE><CHOICE>Fraud</CHOICE><CHOICE>Reputational</CHOICE><CHOICE>HSE</CHOICE></CHOICES></Field>' 'Risk Category'
Ensure-Field 'IA_RiskRegister' 'Likelihood' '<Field Type="Number" DisplayName="Likelihood" Name="Likelihood" StaticName="Likelihood" Group="IAMS" Required="TRUE" Min="1" Max="5"></Field>' 'Likelihood'
Ensure-Field 'IA_RiskRegister' 'ImpactScore' '<Field Type="Number" DisplayName="Impact" Name="ImpactScore" StaticName="ImpactScore" Group="IAMS" Required="TRUE" Min="1" Max="5"></Field>' 'Impact'
Ensure-Field 'IA_RiskRegister' 'InherentRisk' '<Field Type="Calculated" DisplayName="Inherent Risk" Name="InherentRisk" StaticName="InherentRisk" Group="IAMS" Required="FALSE" ResultType="Number" ReadOnly="TRUE"><Formula>=[Likelihood]*[Impact]</Formula><FieldRefs><FieldRef Name="Likelihood" /><FieldRef Name="ImpactScore" /></FieldRefs></Field>' 'Inherent Risk'
Ensure-Field 'IA_RiskRegister' 'ControlRating' '<Field Type="Number" DisplayName="Control Rating" Name="ControlRating" StaticName="ControlRating" Group="IAMS" Required="TRUE" Min="1" Max="5"></Field>' 'Control Rating'
Ensure-Field 'IA_RiskRegister' 'ResidualRisk' '<Field Type="Calculated" DisplayName="Residual Risk" Name="ResidualRisk" StaticName="ResidualRisk" Group="IAMS" Required="FALSE" ResultType="Number" ReadOnly="TRUE"><Formula>=ROUND([Inherent Risk]*[Control Rating]/5,1)</Formula><FieldRefs><FieldRef Name="InherentRisk" /><FieldRef Name="ControlRating" /></FieldRefs></Field>' 'Residual Risk'
Ensure-Field 'IA_RiskRegister' 'RiskOwner' '<Field Type="User" DisplayName="Risk Owner" Name="RiskOwner" StaticName="RiskOwner" Group="IAMS" Required="FALSE" List="UserInfo" ShowField="ImnName" UserSelectionMode="PeopleOnly" />' 'Risk Owner'
Ensure-Field 'IA_RiskRegister' 'RiskStatus' '<Field Type="Choice" DisplayName="Status" Name="RiskStatus" StaticName="RiskStatus" Group="IAMS" Required="FALSE" Format="Dropdown"><CHOICES><CHOICE>Open</CHOICE><CHOICE>Mitigated</CHOICE><CHOICE>Accepted</CHOICE><CHOICE>Closed</CHOICE></CHOICES><Default>Open</Default></Field>' 'Status'
Set-PnPField -List 'IA_AuditPlan' -Identity 'Title' -Values @{Title='Audit Title'} | Out-Null
Ensure-Field 'IA_AuditPlan' 'AuditRef' '<Field Type="Text" DisplayName="Audit Ref" Name="AuditRef" StaticName="AuditRef" Group="IAMS" Required="FALSE" Indexed="TRUE" MaxLength="255" />' 'Audit Ref'
Ensure-Field 'IA_AuditPlan' 'PlanYear' '<Field Type="Number" DisplayName="Plan Year" Name="PlanYear" StaticName="PlanYear" Group="IAMS" Required="FALSE" Indexed="TRUE" Min="2020" Max="2100"></Field>' 'Plan Year'
Ensure-Field 'IA_AuditPlan' 'AuditArea' '<Field Type="Lookup" DisplayName="Audit Area" Name="AuditArea" StaticName="AuditArea" Group="IAMS" Required="TRUE" Indexed="TRUE" List="@@LIST:IA_AuditUniverse@@" ShowField="Title" />' 'Audit Area'
Ensure-Field 'IA_AuditPlan' 'Entity' '<Field Type="LookupMulti" DisplayName="Entity" Name="Entity" StaticName="Entity" Group="IAMS" Required="FALSE" List="@@LIST:IA_Entities@@" ShowField="Title" Mult="TRUE" />' 'Entity'
Ensure-Field 'IA_AuditPlan' 'AuditType' '<Field Type="Choice" DisplayName="Audit Type" Name="AuditType" StaticName="AuditType" Group="IAMS" Required="FALSE" Format="Dropdown"><CHOICES><CHOICE>Financial</CHOICE><CHOICE>Operational</CHOICE><CHOICE>Compliance</CHOICE><CHOICE>IT</CHOICE><CHOICE>Special Investigation</CHOICE><CHOICE>Follow-up</CHOICE><CHOICE>Advisory</CHOICE></CHOICES></Field>' 'Audit Type'
Ensure-Field 'IA_AuditPlan' 'PlannedStart' '<Field Type="DateTime" DisplayName="Planned Start" Name="PlannedStart" StaticName="PlannedStart" Group="IAMS" Required="TRUE" Format="DateOnly" />' 'Planned Start'
Ensure-Field 'IA_AuditPlan' 'PlannedFinish' '<Field Type="DateTime" DisplayName="Planned Finish" Name="PlannedFinish" StaticName="PlannedFinish" Group="IAMS" Required="TRUE" Format="DateOnly" />' 'Planned Finish'
Ensure-Field 'IA_AuditPlan' 'RiskScore' '<Field Type="Number" DisplayName="Risk Score" Name="RiskScore" StaticName="RiskScore" Group="IAMS" Required="FALSE"></Field>' 'Risk Score'
Ensure-Field 'IA_AuditPlan' 'AssignedAuditor' '<Field Type="User" DisplayName="Assigned Auditor" Name="AssignedAuditor" StaticName="AssignedAuditor" Group="IAMS" Required="FALSE" List="UserInfo" ShowField="ImnName" UserSelectionMode="PeopleOnly" />' 'Assigned Auditor'
Ensure-Field 'IA_AuditPlan' 'AuditManager' '<Field Type="User" DisplayName="Audit Manager" Name="AuditManager" StaticName="AuditManager" Group="IAMS" Required="FALSE" List="UserInfo" ShowField="ImnName" UserSelectionMode="PeopleOnly" />' 'Audit Manager'
Ensure-Field 'IA_AuditPlan' 'BudgetHours' '<Field Type="Number" DisplayName="Budget Hours" Name="BudgetHours" StaticName="BudgetHours" Group="IAMS" Required="FALSE" Min="0"></Field>' 'Budget Hours'
Ensure-Field 'IA_AuditPlan' 'ActualHours' '<Field Type="Number" DisplayName="Actual Hours" Name="ActualHours" StaticName="ActualHours" Group="IAMS" Required="FALSE" Min="0"></Field>' 'Actual Hours'
Ensure-Field 'IA_AuditPlan' 'AuditStatus' '<Field Type="Choice" DisplayName="Audit Status" Name="AuditStatus" StaticName="AuditStatus" Group="IAMS" Required="FALSE" Indexed="TRUE" Format="Dropdown"><CHOICES><CHOICE>Planned</CHOICE><CHOICE>In Progress</CHOICE><CHOICE>Fieldwork</CHOICE><CHOICE>Reporting</CHOICE><CHOICE>Completed</CHOICE><CHOICE>Deferred</CHOICE><CHOICE>Cancelled</CHOICE></CHOICES><Default>Planned</Default></Field>' 'Audit Status'
Ensure-Field 'IA_AuditPlan' 'ApprovalStatus' '<Field Type="Choice" DisplayName="Approval Status" Name="ApprovalStatus" StaticName="ApprovalStatus" Group="IAMS" Required="FALSE" Indexed="TRUE" Format="Dropdown"><CHOICES><CHOICE>Draft</CHOICE><CHOICE>Pending Manager Review</CHOICE><CHOICE>Pending Owner Approval</CHOICE><CHOICE>Approved</CHOICE><CHOICE>Rejected</CHOICE></CHOICES><Default>Draft</Default></Field>' 'Approval Status'
Ensure-Field 'IA_AuditPlan' 'DeferralReason' '<Field Type="Note" DisplayName="Deferral / Cancellation Reason" Name="DeferralReason" StaticName="DeferralReason" Group="IAMS" Required="FALSE" NumLines="6" RichText="FALSE" />' 'Deferral / Cancellation Reason'
Set-PnPField -List 'IA_Engagements' -Identity 'Title' -Values @{Title='Engagement Title'} | Out-Null
Ensure-Field 'IA_Engagements' 'EngagementID' '<Field Type="Text" DisplayName="Engagement ID" Name="EngagementID" StaticName="EngagementID" Group="IAMS" Required="FALSE" Indexed="TRUE" MaxLength="255" />' 'Engagement ID'
Ensure-Field 'IA_Engagements' 'AuditPlanItem' '<Field Type="Lookup" DisplayName="Audit Plan Item" Name="AuditPlanItem" StaticName="AuditPlanItem" Group="IAMS" Required="TRUE" Indexed="TRUE" List="@@LIST:IA_AuditPlan@@" ShowField="Title" />' 'Audit Plan Item'
Ensure-Field 'IA_Engagements' 'Entity' '<Field Type="LookupMulti" DisplayName="Entity" Name="Entity" StaticName="Entity" Group="IAMS" Required="FALSE" List="@@LIST:IA_Entities@@" ShowField="Title" Mult="TRUE" />' 'Entity'
Ensure-Field 'IA_Engagements' 'EngagementScope' '<Field Type="Note" DisplayName="Engagement Scope" Name="EngagementScope" StaticName="EngagementScope" Group="IAMS" Required="FALSE" NumLines="6" RichText="FALSE" />' 'Engagement Scope'
Ensure-Field 'IA_Engagements' 'AuditObjective' '<Field Type="Note" DisplayName="Audit Objective" Name="AuditObjective" StaticName="AuditObjective" Group="IAMS" Required="FALSE" NumLines="6" RichText="FALSE" />' 'Audit Objective'
Ensure-Field 'IA_Engagements' 'LeadAuditor' '<Field Type="User" DisplayName="Lead Auditor" Name="LeadAuditor" StaticName="LeadAuditor" Group="IAMS" Required="FALSE" Indexed="TRUE" List="UserInfo" ShowField="ImnName" UserSelectionMode="PeopleOnly" />' 'Lead Auditor'
Ensure-Field 'IA_Engagements' 'TeamMembers' '<Field Type="UserMulti" DisplayName="Team Members" Name="TeamMembers" StaticName="TeamMembers" Group="IAMS" Required="FALSE" List="UserInfo" ShowField="ImnName" UserSelectionMode="PeopleOnly" Mult="TRUE" />' 'Team Members'
Ensure-Field 'IA_Engagements' 'ActualStart' '<Field Type="DateTime" DisplayName="Start Date" Name="ActualStart" StaticName="ActualStart" Group="IAMS" Required="FALSE" Format="DateOnly" />' 'Start Date'
Ensure-Field 'IA_Engagements' 'ActualEnd' '<Field Type="DateTime" DisplayName="End Date" Name="ActualEnd" StaticName="ActualEnd" Group="IAMS" Required="FALSE" Format="DateOnly" />' 'End Date'
Ensure-Field 'IA_Engagements' 'Stage' '<Field Type="Choice" DisplayName="Stage" Name="Stage" StaticName="Stage" Group="IAMS" Required="FALSE" Indexed="TRUE" Format="Dropdown"><CHOICES><CHOICE>Planning</CHOICE><CHOICE>Kick-off</CHOICE><CHOICE>Walkthroughs</CHOICE><CHOICE>Fieldwork</CHOICE><CHOICE>Fieldwork Complete</CHOICE><CHOICE>Testing</CHOICE><CHOICE>Draft Report</CHOICE><CHOICE>Management Responses</CHOICE><CHOICE>Reporting</CHOICE><CHOICE>Final Report</CHOICE><CHOICE>Closed</CHOICE></CHOICES><Default>Planning</Default></Field>' 'Stage'
Ensure-Field 'IA_Engagements' 'OverallOpinion' '<Field Type="Choice" DisplayName="Overall Opinion" Name="OverallOpinion" StaticName="OverallOpinion" Group="IAMS" Required="FALSE" Format="Dropdown"><CHOICES><CHOICE>Satisfactory</CHOICE><CHOICE>Needs Improvement</CHOICE><CHOICE>Unsatisfactory</CHOICE><CHOICE>Not Rated</CHOICE></CHOICES></Field>' 'Overall Opinion'
Ensure-Field 'IA_Engagements' 'EngagementFolderUrl' '<Field Type="URL" DisplayName="Engagement Folder" Name="EngagementFolderUrl" StaticName="EngagementFolderUrl" Group="IAMS" Required="FALSE" Format="Hyperlink" />' 'Engagement Folder'
Ensure-Field 'IA_Engagements' 'Engagement_x0020_Type' '<Field Type="Choice" DisplayName="Engagement Type" Name="Engagement_x0020_Type" StaticName="Engagement_x0020_Type" Group="IAMS" Required="FALSE" Format="Dropdown"><CHOICES><CHOICE>Financial</CHOICE><CHOICE>Operational</CHOICE><CHOICE>Compliance</CHOICE><CHOICE>IT</CHOICE><CHOICE>Special Investigation</CHOICE><CHOICE>Follow-up</CHOICE><CHOICE>Advisory</CHOICE></CHOICES></Field>' 'Engagement Type'
Ensure-Field 'IA_Engagements' 'BudgetedHours' '<Field Type="Number" DisplayName="Budgeted Hours" Name="BudgetedHours" StaticName="BudgetedHours" Group="IAMS" Required="FALSE" Min="0"></Field>' 'Budgeted Hours'
Ensure-Field 'IA_Engagements' 'EngActualHours' '<Field Type="Number" DisplayName="Actual Hours" Name="EngActualHours" StaticName="EngActualHours" Group="IAMS" Required="FALSE" Min="0"></Field>' 'Actual Hours'
Ensure-Field 'IA_Engagements' 'PlanningType' '<Field Type="Choice" DisplayName="Planning Type" Name="PlanningType" StaticName="PlanningType" Group="IAMS" Required="FALSE" Format="Dropdown"><CHOICES><CHOICE>Planned</CHOICE><CHOICE>Unplanned</CHOICE></CHOICES><Default>Planned</Default></Field>' 'Planning Type'
Ensure-Field 'IA_Engagements' 'AuditManager' '<Field Type="User" DisplayName="Audit Manager" Name="AuditManager" StaticName="AuditManager" Group="IAMS" Required="FALSE" List="UserInfo" ShowField="ImnName" UserSelectionMode="PeopleOnly" />' 'Audit Manager'
Set-PnPField -List 'IA_Milestones' -Identity 'Title' -Values @{Title='Milestone'} | Out-Null
Ensure-Field 'IA_Milestones' 'Engagement' '<Field Type="Lookup" DisplayName="Engagement" Name="Engagement" StaticName="Engagement" Group="IAMS" Required="TRUE" Indexed="TRUE" List="@@LIST:IA_Engagements@@" ShowField="Title" />' 'Engagement'
Ensure-Field 'IA_Milestones' 'MilestoneType' '<Field Type="Choice" DisplayName="Type" Name="MilestoneType" StaticName="MilestoneType" Group="IAMS" Required="FALSE" Format="Dropdown"><CHOICES><CHOICE>Kick-off</CHOICE><CHOICE>Walkthroughs</CHOICE><CHOICE>Fieldwork Complete</CHOICE><CHOICE>Draft Report</CHOICE><CHOICE>Management Responses</CHOICE><CHOICE>Final Report</CHOICE><CHOICE>Closure</CHOICE></CHOICES></Field>' 'Type'
Ensure-Field 'IA_Milestones' 'DueDate' '<Field Type="DateTime" DisplayName="Due Date" Name="DueDate" StaticName="DueDate" Group="IAMS" Required="TRUE" Format="DateOnly" />' 'Due Date'
Ensure-Field 'IA_Milestones' 'CompletedDate' '<Field Type="DateTime" DisplayName="Completed Date" Name="CompletedDate" StaticName="CompletedDate" Group="IAMS" Required="FALSE" Format="DateOnly" />' 'Completed Date'
Ensure-Field 'IA_Milestones' 'MilestoneOwner' '<Field Type="User" DisplayName="Owner" Name="MilestoneOwner" StaticName="MilestoneOwner" Group="IAMS" Required="FALSE" List="UserInfo" ShowField="ImnName" UserSelectionMode="PeopleOnly" />' 'Owner'
Ensure-Field 'IA_Milestones' 'MilestoneStatus' '<Field Type="Choice" DisplayName="Status" Name="MilestoneStatus" StaticName="MilestoneStatus" Group="IAMS" Required="FALSE" Format="Dropdown"><CHOICES><CHOICE>Not Started</CHOICE><CHOICE>In Progress</CHOICE><CHOICE>Complete</CHOICE><CHOICE>Late</CHOICE></CHOICES><Default>Not Started</Default></Field>' 'Status'
Set-PnPField -List 'IA_Findings' -Identity 'Title' -Values @{Title='Finding Title'} | Out-Null
Ensure-Field 'IA_Findings' 'FindingID' '<Field Type="Text" DisplayName="Finding ID" Name="FindingID" StaticName="FindingID" Group="IAMS" Required="FALSE" Indexed="TRUE" MaxLength="255" />' 'Finding ID'
Ensure-Field 'IA_Findings' 'Engagement' '<Field Type="Lookup" DisplayName="Engagement" Name="Engagement" StaticName="Engagement" Group="IAMS" Required="TRUE" Indexed="TRUE" List="@@LIST:IA_Engagements@@" ShowField="Title" />' 'Engagement'
Ensure-Field 'IA_Findings' 'Entity' '<Field Type="Lookup" DisplayName="Entity" Name="Entity" StaticName="Entity" Group="IAMS" Required="FALSE" Indexed="TRUE" List="@@LIST:IA_Entities@@" ShowField="Title" />' 'Entity'
Ensure-Field 'IA_Findings' 'Department' '<Field Type="Lookup" DisplayName="Department" Name="Department" StaticName="Department" Group="IAMS" Required="FALSE" Indexed="TRUE" List="@@LIST:IA_Departments@@" ShowField="Title" />' 'Department'
Ensure-Field 'IA_Findings' 'Observation' '<Field Type="Note" DisplayName="Observation" Name="Observation" StaticName="Observation" Group="IAMS" Required="FALSE" NumLines="6" RichText="FALSE" />' 'Observation'
Ensure-Field 'IA_Findings' 'RootCause' '<Field Type="Note" DisplayName="Root Cause" Name="RootCause" StaticName="RootCause" Group="IAMS" Required="FALSE" NumLines="6" RichText="FALSE" />' 'Root Cause'
Ensure-Field 'IA_Findings' 'RiskCategory' '<Field Type="Choice" DisplayName="Risk Category" Name="RiskCategory" StaticName="RiskCategory" Group="IAMS" Required="FALSE" Format="Dropdown"><CHOICES><CHOICE>Strategic</CHOICE><CHOICE>Operational</CHOICE><CHOICE>Financial</CHOICE><CHOICE>Compliance</CHOICE><CHOICE>IT &amp; Cyber</CHOICE><CHOICE>Fraud</CHOICE><CHOICE>Reputational</CHOICE><CHOICE>HSE</CHOICE></CHOICES></Field>' 'Risk Category'
Ensure-Field 'IA_Findings' 'ImpactDescription' '<Field Type="Note" DisplayName="Impact" Name="ImpactDescription" StaticName="ImpactDescription" Group="IAMS" Required="FALSE" NumLines="6" RichText="FALSE" />' 'Impact'
Ensure-Field 'IA_Findings' 'Recommendation' '<Field Type="Note" DisplayName="Recommendation" Name="Recommendation" StaticName="Recommendation" Group="IAMS" Required="FALSE" NumLines="6" RichText="FALSE" />' 'Recommendation'
Ensure-Field 'IA_Findings' 'Rating' '<Field Type="Choice" DisplayName="Rating" Name="Rating" StaticName="Rating" Group="IAMS" Required="TRUE" Indexed="TRUE" Format="Dropdown"><CHOICES><CHOICE>Critical</CHOICE><CHOICE>High</CHOICE><CHOICE>Medium</CHOICE><CHOICE>Low</CHOICE></CHOICES></Field>' 'Rating'
Ensure-Field 'IA_Findings' 'WorkflowStage' '<Field Type="Choice" DisplayName="Workflow Stage" Name="WorkflowStage" StaticName="WorkflowStage" Group="IAMS" Required="FALSE" Indexed="TRUE" Format="Dropdown"><CHOICES><CHOICE>Draft</CHOICE><CHOICE>Manager Review</CHOICE><CHOICE>Management Response</CHOICE><CHOICE>Audit Review</CHOICE><CHOICE>HoIA Approval</CHOICE><CHOICE>Issued</CHOICE><CHOICE>Closed</CHOICE></CHOICES><Default>Draft</Default></Field>' 'Workflow Stage'
Ensure-Field 'IA_Findings' 'AgreementStatus' '<Field Type="Choice" DisplayName="Management Agreement" Name="AgreementStatus" StaticName="AgreementStatus" Group="IAMS" Required="FALSE" Format="Dropdown"><CHOICES><CHOICE>Pending</CHOICE><CHOICE>Agreed</CHOICE><CHOICE>Partially Agreed</CHOICE><CHOICE>Disagreed</CHOICE></CHOICES><Default>Pending</Default></Field>' 'Management Agreement'
Ensure-Field 'IA_Findings' 'ManagementResponse' '<Field Type="Note" DisplayName="Management Response" Name="ManagementResponse" StaticName="ManagementResponse" Group="IAMS" Required="FALSE" NumLines="6" RichText="FALSE" />' 'Management Response'
Ensure-Field 'IA_Findings' 'ResponsibleManager' '<Field Type="User" DisplayName="Responsible Manager" Name="ResponsibleManager" StaticName="ResponsibleManager" Group="IAMS" Required="FALSE" Indexed="TRUE" List="UserInfo" ShowField="ImnName" UserSelectionMode="PeopleOnly" />' 'Responsible Manager'
Ensure-Field 'IA_Findings' 'DateIssued' '<Field Type="DateTime" DisplayName="Date Issued" Name="DateIssued" StaticName="DateIssued" Group="IAMS" Required="FALSE" Format="DateOnly" />' 'Date Issued'
Ensure-Field 'IA_Findings' 'OriginalDueDate' '<Field Type="DateTime" DisplayName="Original Due Date" Name="OriginalDueDate" StaticName="OriginalDueDate" Group="IAMS" Required="FALSE" Format="DateOnly" />' 'Original Due Date'
Ensure-Field 'IA_Findings' 'DueDate' '<Field Type="DateTime" DisplayName="Current Due Date" Name="DueDate" StaticName="DueDate" Group="IAMS" Required="FALSE" Indexed="TRUE" Format="DateOnly" />' 'Current Due Date'
Ensure-Field 'IA_Findings' 'ExtensionCount' '<Field Type="Number" DisplayName="Extension Count" Name="ExtensionCount" StaticName="ExtensionCount" Group="IAMS" Required="FALSE" Min="0"><Default>0</Default></Field>' 'Extension Count'
Ensure-Field 'IA_Findings' 'FindingStatus' '<Field Type="Choice" DisplayName="Status" Name="FindingStatus" StaticName="FindingStatus" Group="IAMS" Required="FALSE" Indexed="TRUE" Format="Dropdown"><CHOICES><CHOICE>Open</CHOICE><CHOICE>In Progress</CHOICE><CHOICE>Pending Validation</CHOICE><CHOICE>Closed</CHOICE><CHOICE>Re-opened</CHOICE><CHOICE>Risk Accepted</CHOICE></CHOICES><Default>Open</Default></Field>' 'Status'
Ensure-Field 'IA_Findings' 'ClosedDate' '<Field Type="DateTime" DisplayName="Closed Date" Name="ClosedDate" StaticName="ClosedDate" Group="IAMS" Required="FALSE" Format="DateOnly" />' 'Closed Date'
Ensure-Field 'IA_Findings' 'LastProcessedStage' '<Field Type="Text" DisplayName="Last Processed Stage" Name="LastProcessedStage" StaticName="LastProcessedStage" Group="IAMS" Required="FALSE" MaxLength="255" />' 'Last Processed Stage'
Ensure-Field 'IA_Findings' 'Compliance_x0020_Result' '<Field Type="Choice" DisplayName="Compliance Result" Name="Compliance_x0020_Result" StaticName="Compliance_x0020_Result" Group="IAMS" Required="FALSE" Format="Dropdown"><CHOICES><CHOICE>Compliant</CHOICE><CHOICE>Non-compliant</CHOICE><CHOICE>N/A</CHOICE></CHOICES></Field>' 'Compliance Result'
Ensure-Field 'IA_Findings' 'MgmtAcceptance' '<Field Type="Choice" DisplayName="Management Acceptance" Name="MgmtAcceptance" StaticName="MgmtAcceptance" Group="IAMS" Required="FALSE" Format="Dropdown"><CHOICES><CHOICE>Pending</CHOICE><CHOICE>Accepted</CHOICE><CHOICE>Partially Accepted</CHOICE><CHOICE>Not Accepted</CHOICE></CHOICES><Default>Pending</Default></Field>' 'Management Acceptance'
Ensure-Field 'IA_Findings' 'MgmtResponseDate' '<Field Type="DateTime" DisplayName="Management Response Date" Name="MgmtResponseDate" StaticName="MgmtResponseDate" Group="IAMS" Required="FALSE" Format="DateOnly" />' 'Management Response Date'
Ensure-Field 'IA_Findings' 'MgmtAcceptanceComments' '<Field Type="Note" DisplayName="Management Acceptance Comments" Name="MgmtAcceptanceComments" StaticName="MgmtAcceptanceComments" Group="IAMS" Required="FALSE" NumLines="6" RichText="FALSE" />' 'Management Acceptance Comments'
Set-PnPField -List 'IA_ActionPlans' -Identity 'Title' -Values @{Title='Action Title'} | Out-Null
Ensure-Field 'IA_ActionPlans' 'CAPAID' '<Field Type="Text" DisplayName="Action ID" Name="CAPAID" StaticName="CAPAID" Group="IAMS" Required="FALSE" Indexed="TRUE" MaxLength="255" />' 'Action ID'
Ensure-Field 'IA_ActionPlans' 'Finding' '<Field Type="Lookup" DisplayName="Finding" Name="Finding" StaticName="Finding" Group="IAMS" Required="TRUE" Indexed="TRUE" List="@@LIST:IA_Findings@@" ShowField="Title" />' 'Finding'
Ensure-Field 'IA_ActionPlans' 'Entity' '<Field Type="Lookup" DisplayName="Entity" Name="Entity" StaticName="Entity" Group="IAMS" Required="FALSE" Indexed="TRUE" List="@@LIST:IA_Entities@@" ShowField="Title" />' 'Entity'
Ensure-Field 'IA_ActionPlans' 'ActionDescription' '<Field Type="Note" DisplayName="Action Description" Name="ActionDescription" StaticName="ActionDescription" Group="IAMS" Required="FALSE" NumLines="6" RichText="FALSE" />' 'Action Description'
Ensure-Field 'IA_ActionPlans' 'ActionOwner' '<Field Type="User" DisplayName="Owner" Name="ActionOwner" StaticName="ActionOwner" Group="IAMS" Required="TRUE" Indexed="TRUE" List="UserInfo" ShowField="ImnName" UserSelectionMode="PeopleOnly" />' 'Owner'
Ensure-Field 'IA_ActionPlans' 'DueDate' '<Field Type="DateTime" DisplayName="Due Date" Name="DueDate" StaticName="DueDate" Group="IAMS" Required="TRUE" Indexed="TRUE" Format="DateOnly" />' 'Due Date'
Ensure-Field 'IA_ActionPlans' 'CompletionPct' '<Field Type="Number" DisplayName="Completion %" Name="CompletionPct" StaticName="CompletionPct" Group="IAMS" Required="FALSE" Min="0" Max="100"><Default>0</Default></Field>' 'Completion %'
Ensure-Field 'IA_ActionPlans' 'EvidenceUploaded' '<Field Type="Boolean" DisplayName="Evidence Uploaded" Name="EvidenceUploaded" StaticName="EvidenceUploaded" Group="IAMS" Required="FALSE"><Default>0</Default></Field>' 'Evidence Uploaded'
Ensure-Field 'IA_ActionPlans' 'ValidationStatus' '<Field Type="Choice" DisplayName="Validation Status" Name="ValidationStatus" StaticName="ValidationStatus" Group="IAMS" Required="FALSE" Indexed="TRUE" Format="Dropdown"><CHOICES><CHOICE>Not Started</CHOICE><CHOICE>Submitted</CHOICE><CHOICE>Under Review</CHOICE><CHOICE>Validated</CHOICE><CHOICE>Rejected</CHOICE></CHOICES><Default>Not Started</Default></Field>' 'Validation Status'
Ensure-Field 'IA_ActionPlans' 'FollowUpAuditor' '<Field Type="User" DisplayName="Follow-up Auditor" Name="FollowUpAuditor" StaticName="FollowUpAuditor" Group="IAMS" Required="FALSE" List="UserInfo" ShowField="ImnName" UserSelectionMode="PeopleOnly" />' 'Follow-up Auditor'
Ensure-Field 'IA_ActionPlans' 'FindingRating' '<Field Type="Choice" DisplayName="Finding Rating" Name="FindingRating" StaticName="FindingRating" Group="IAMS" Required="FALSE" Indexed="TRUE" Format="Dropdown"><CHOICES><CHOICE>Critical</CHOICE><CHOICE>High</CHOICE><CHOICE>Medium</CHOICE><CHOICE>Low</CHOICE></CHOICES></Field>' 'Finding Rating'
Ensure-Field 'IA_ActionPlans' 'ActionStatus' '<Field Type="Choice" DisplayName="Status" Name="ActionStatus" StaticName="ActionStatus" Group="IAMS" Required="FALSE" Indexed="TRUE" Format="Dropdown"><CHOICES><CHOICE>Open</CHOICE><CHOICE>In Progress</CHOICE><CHOICE>Complete - Awaiting Validation</CHOICE><CHOICE>Closed</CHOICE><CHOICE>Overdue</CHOICE></CHOICES><Default>Open</Default></Field>' 'Status'
Ensure-Field 'IA_ActionPlans' 'ReminderStage' '<Field Type="Choice" DisplayName="Reminder Stage" Name="ReminderStage" StaticName="ReminderStage" Group="IAMS" Required="FALSE" Format="Dropdown"><CHOICES><CHOICE>None</CHOICE><CHOICE>Reminder 30d</CHOICE><CHOICE>Reminder 15d</CHOICE><CHOICE>Escalated - Dept Head</CHOICE><CHOICE>Escalated - CEO</CHOICE></CHOICES><Default>None</Default></Field>' 'Reminder Stage'
Ensure-Field 'IA_ActionPlans' 'CompletedDate' '<Field Type="DateTime" DisplayName="Actual Completion Date" Name="CompletedDate" StaticName="CompletedDate" Group="IAMS" Required="FALSE" Format="DateOnly" />' 'Actual Completion Date'
Ensure-Field 'IA_ActionPlans' 'ExtensionCount' '<Field Type="Number" DisplayName="ExtensionCount" Name="ExtensionCount" StaticName="ExtensionCount" Group="IAMS" Required="FALSE" Min="0"></Field>' 'ExtensionCount'
Ensure-Field 'IA_ActionPlans' 'OriginalDueDate' '<Field Type="DateTime" DisplayName="OriginalDueDate" Name="OriginalDueDate" StaticName="OriginalDueDate" Group="IAMS" Required="FALSE" Format="DateOnly" />' 'OriginalDueDate'
Ensure-Field 'IA_ActionPlans' 'ClosureProcessed' '<Field Type="Boolean" DisplayName="ClosureProcessed" Name="ClosureProcessed" StaticName="ClosureProcessed" Group="IAMS" Required="FALSE"><Default>0</Default></Field>' 'ClosureProcessed'
Set-PnPField -List 'IA_FollowUps' -Identity 'Title' -Values @{Title='Review Title'} | Out-Null
Ensure-Field 'IA_FollowUps' 'Finding' '<Field Type="Lookup" DisplayName="Finding" Name="Finding" StaticName="Finding" Group="IAMS" Required="TRUE" Indexed="TRUE" List="@@LIST:IA_Findings@@" ShowField="Title" />' 'Finding'
Ensure-Field 'IA_FollowUps' 'Action' '<Field Type="Lookup" DisplayName="Action" Name="Action" StaticName="Action" Group="IAMS" Required="FALSE" Indexed="TRUE" List="@@LIST:IA_ActionPlans@@" ShowField="Title" />' 'Action'
Ensure-Field 'IA_FollowUps' 'Reviewer' '<Field Type="User" DisplayName="Reviewer" Name="Reviewer" StaticName="Reviewer" Group="IAMS" Required="TRUE" List="UserInfo" ShowField="ImnName" UserSelectionMode="PeopleOnly" />' 'Reviewer'
Ensure-Field 'IA_FollowUps' 'ReviewDate' '<Field Type="DateTime" DisplayName="Review Date" Name="ReviewDate" StaticName="ReviewDate" Group="IAMS" Required="FALSE" Format="DateOnly" />' 'Review Date'
Ensure-Field 'IA_FollowUps' 'Outcome' '<Field Type="Choice" DisplayName="Outcome" Name="Outcome" StaticName="Outcome" Group="IAMS" Required="FALSE" Format="Dropdown"><CHOICES><CHOICE>Implemented</CHOICE><CHOICE>Partially Implemented</CHOICE><CHOICE>Not Implemented</CHOICE><CHOICE>Re-opened</CHOICE><CHOICE>Closed</CHOICE></CHOICES></Field>' 'Outcome'
Ensure-Field 'IA_FollowUps' 'TestingNotes' '<Field Type="Note" DisplayName="Testing Notes" Name="TestingNotes" StaticName="TestingNotes" Group="IAMS" Required="FALSE" NumLines="6" RichText="FALSE" />' 'Testing Notes'
Ensure-Field 'IA_FollowUps' 'ValidationDocUrl' '<Field Type="URL" DisplayName="Validation Document" Name="ValidationDocUrl" StaticName="ValidationDocUrl" Group="IAMS" Required="FALSE" Format="Hyperlink" />' 'Validation Document'
Set-PnPField -List 'IA_CSARegister' -Identity 'Title' -Values @{Title='Form Name'} | Out-Null
Ensure-Field 'IA_CSARegister' 'CSAID' '<Field Type="Text" DisplayName="CSA ID" Name="CSAID" StaticName="CSAID" Group="IAMS" Required="FALSE" Indexed="TRUE" MaxLength="255" />' 'CSA ID'
Ensure-Field 'IA_CSARegister' 'Entity' '<Field Type="Lookup" DisplayName="Entity" Name="Entity" StaticName="Entity" Group="IAMS" Required="FALSE" Indexed="TRUE" List="@@LIST:IA_Entities@@" ShowField="Title" />' 'Entity'
Ensure-Field 'IA_CSARegister' 'Department' '<Field Type="Lookup" DisplayName="Department" Name="Department" StaticName="Department" Group="IAMS" Required="FALSE" Indexed="TRUE" List="@@LIST:IA_Departments@@" ShowField="Title" />' 'Department'
Ensure-Field 'IA_CSARegister' 'AssessmentPeriod' '<Field Type="Text" DisplayName="Assessment Period" Name="AssessmentPeriod" StaticName="AssessmentPeriod" Group="IAMS" Required="FALSE" MaxLength="255" />' 'Assessment Period'
Ensure-Field 'IA_CSARegister' 'SubmissionDate' '<Field Type="DateTime" DisplayName="Submission Date" Name="SubmissionDate" StaticName="SubmissionDate" Group="IAMS" Required="FALSE" Format="DateOnly" />' 'Submission Date'
Ensure-Field 'IA_CSARegister' 'SubmittedBy' '<Field Type="User" DisplayName="Submitted By" Name="SubmittedBy" StaticName="SubmittedBy" Group="IAMS" Required="FALSE" List="UserInfo" ShowField="ImnName" UserSelectionMode="PeopleOnly" />' 'Submitted By'
Ensure-Field 'IA_CSARegister' 'Score' '<Field Type="Number" DisplayName="Score" Name="Score" StaticName="Score" Group="IAMS" Required="FALSE" Min="0" Max="100"></Field>' 'Score'
Ensure-Field 'IA_CSARegister' 'Result' '<Field Type="Choice" DisplayName="Result" Name="Result" StaticName="Result" Group="IAMS" Required="FALSE" Format="Dropdown"><CHOICES><CHOICE>Satisfactory</CHOICE><CHOICE>Needs Attention</CHOICE><CHOICE>Unsatisfactory</CHOICE></CHOICES></Field>' 'Result'
Ensure-Field 'IA_CSARegister' 'FormResponseId' '<Field Type="Text" DisplayName="Forms Response ID" Name="FormResponseId" StaticName="FormResponseId" Group="IAMS" Required="FALSE" Indexed="TRUE" MaxLength="255" />' 'Forms Response ID'
Ensure-Field 'IA_CSARegister' 'RelatedAudit' '<Field Type="Lookup" DisplayName="Related Audit" Name="RelatedAudit" StaticName="RelatedAudit" Group="IAMS" Required="FALSE" List="@@LIST:IA_AuditPlan@@" ShowField="Title" />' 'Related Audit'
Ensure-Field 'IA_CSARegister' 'AttachmentsUrl' '<Field Type="URL" DisplayName="Attachments Folder" Name="AttachmentsUrl" StaticName="AttachmentsUrl" Group="IAMS" Required="FALSE" Format="Hyperlink" />' 'Attachments Folder'
Set-PnPField -List 'IA_AuditLog' -Identity 'Title' -Values @{Title='Event'} | Out-Null
Ensure-Field 'IA_AuditLog' 'SourceList' '<Field Type="Text" DisplayName="Source List" Name="SourceList" StaticName="SourceList" Group="IAMS" Required="FALSE" Indexed="TRUE" MaxLength="255" />' 'Source List'
Ensure-Field 'IA_AuditLog' 'SourceItemId' '<Field Type="Number" DisplayName="Source Item ID" Name="SourceItemId" StaticName="SourceItemId" Group="IAMS" Required="FALSE" Indexed="TRUE"></Field>' 'Source Item ID'
Ensure-Field 'IA_AuditLog' 'EventType' '<Field Type="Choice" DisplayName="Event Type" Name="EventType" StaticName="EventType" Group="IAMS" Required="FALSE" Format="Dropdown"><CHOICES><CHOICE>Created</CHOICE><CHOICE>Stage Change</CHOICE><CHOICE>Approval</CHOICE><CHOICE>Rejection</CHOICE><CHOICE>Due Date Extension</CHOICE><CHOICE>Closure</CHOICE><CHOICE>Re-open</CHOICE><CHOICE>Escalation</CHOICE></CHOICES></Field>' 'Event Type'
Ensure-Field 'IA_AuditLog' 'EventBy' '<Field Type="User" DisplayName="By" Name="EventBy" StaticName="EventBy" Group="IAMS" Required="FALSE" List="UserInfo" ShowField="ImnName" UserSelectionMode="PeopleOnly" />' 'By'
Ensure-Field 'IA_AuditLog' 'EventDetails' '<Field Type="Note" DisplayName="Details" Name="EventDetails" StaticName="EventDetails" Group="IAMS" Required="FALSE" NumLines="6" RichText="FALSE" />' 'Details'
Set-PnPField -List 'IA_Config' -Identity 'Title' -Values @{Title='Key'} | Out-Null
Ensure-Field 'IA_Config' 'ConfigValue' '<Field Type="Text" DisplayName="Value" Name="ConfigValue" StaticName="ConfigValue" Group="IAMS" Required="TRUE" MaxLength="255" />' 'Value'
Ensure-Field 'IA_Config' 'ConfigDescription' '<Field Type="Text" DisplayName="Description" Name="ConfigDescription" StaticName="ConfigDescription" Group="IAMS" Required="FALSE" MaxLength="255" />' 'Description'
Set-PnPField -List 'IA_Questionnaires' -Identity 'Title' -Values @{Title='Questionnaire Name'} | Out-Null
Ensure-Field 'IA_Questionnaires' 'QuestionnaireID' '<Field Type="Text" DisplayName="Questionnaire ID" Name="QuestionnaireID" StaticName="QuestionnaireID" Group="IAMS" Required="FALSE" Indexed="TRUE" MaxLength="255" />' 'Questionnaire ID'
Ensure-Field 'IA_Questionnaires' 'Engagement' '<Field Type="Lookup" DisplayName="Engagement" Name="Engagement" StaticName="Engagement" Group="IAMS" Required="TRUE" Indexed="TRUE" List="@@LIST:IA_Engagements@@" ShowField="Title" />' 'Engagement'
Ensure-Field 'IA_Questionnaires' 'AuditType' '<Field Type="Choice" DisplayName="Audit Type" Name="AuditType" StaticName="AuditType" Group="IAMS" Required="FALSE" Format="Dropdown"><CHOICES><CHOICE>Financial</CHOICE><CHOICE>Operational</CHOICE><CHOICE>Compliance</CHOICE><CHOICE>IT</CHOICE><CHOICE>Special Investigation</CHOICE><CHOICE>Follow-up</CHOICE><CHOICE>Advisory</CHOICE></CHOICES></Field>' 'Audit Type'
Ensure-Field 'IA_Questionnaires' 'TemplateVersion' '<Field Type="Text" DisplayName="Template Version" Name="TemplateVersion" StaticName="TemplateVersion" Group="IAMS" Required="FALSE" MaxLength="255" />' 'Template Version'
Ensure-Field 'IA_Questionnaires' 'Scope' '<Field Type="Note" DisplayName="Scope" Name="Scope" StaticName="Scope" Group="IAMS" Required="FALSE" NumLines="6" RichText="FALSE" />' 'Scope'
Ensure-Field 'IA_Questionnaires' 'QuestionnaireStatus' '<Field Type="Choice" DisplayName="Status" Name="QuestionnaireStatus" StaticName="QuestionnaireStatus" Group="IAMS" Required="FALSE" Indexed="TRUE" Format="Dropdown"><CHOICES><CHOICE>Draft</CHOICE><CHOICE>Issued</CHOICE><CHOICE>In Progress</CHOICE><CHOICE>Under Review</CHOICE><CHOICE>Returned</CHOICE><CHOICE>Accepted</CHOICE><CHOICE>Closed</CHOICE></CHOICES><Default>Draft</Default></Field>' 'Status'
Ensure-Field 'IA_Questionnaires' 'Round' '<Field Type="Number" DisplayName="Round" Name="Round" StaticName="Round" Group="IAMS" Required="FALSE"><Default>1</Default></Field>' 'Round'
Ensure-Field 'IA_Questionnaires' 'IssuedDate' '<Field Type="DateTime" DisplayName="Issued Date" Name="IssuedDate" StaticName="IssuedDate" Group="IAMS" Required="FALSE" Format="DateOnly" />' 'Issued Date'
Ensure-Field 'IA_Questionnaires' 'PreparedBy' '<Field Type="User" DisplayName="Prepared By" Name="PreparedBy" StaticName="PreparedBy" Group="IAMS" Required="FALSE" List="UserInfo" ShowField="ImnName" UserSelectionMode="PeopleOnly" />' 'Prepared By'
Ensure-Field 'IA_Questionnaires' 'Reviewer' '<Field Type="User" DisplayName="Reviewer" Name="Reviewer" StaticName="Reviewer" Group="IAMS" Required="FALSE" List="UserInfo" ShowField="ImnName" UserSelectionMode="PeopleOnly" />' 'Reviewer'
Ensure-Field 'IA_Questionnaires' 'SourceFileUrl' '<Field Type="URL" DisplayName="Source File" Name="SourceFileUrl" StaticName="SourceFileUrl" Group="IAMS" Required="FALSE" Format="Hyperlink" />' 'Source File'
Ensure-Field 'IA_Questionnaires' 'QuestionCount' '<Field Type="Number" DisplayName="Question Count" Name="QuestionCount" StaticName="QuestionCount" Group="IAMS" Required="FALSE"></Field>' 'Question Count'
Set-PnPField -List 'IA_QnrSections' -Identity 'Title' -Values @{Title='Section Title'} | Out-Null
Ensure-Field 'IA_QnrSections' 'Questionnaire' '<Field Type="Lookup" DisplayName="Questionnaire" Name="Questionnaire" StaticName="Questionnaire" Group="IAMS" Required="TRUE" Indexed="TRUE" List="@@LIST:IA_Questionnaires@@" ShowField="Title" />' 'Questionnaire'
Ensure-Field 'IA_QnrSections' 'SectionNo' '<Field Type="Number" DisplayName="Section No" Name="SectionNo" StaticName="SectionNo" Group="IAMS" Required="FALSE"></Field>' 'Section No'
Ensure-Field 'IA_QnrSections' 'Assignee' '<Field Type="User" DisplayName="Assignee" Name="Assignee" StaticName="Assignee" Group="IAMS" Required="FALSE" List="UserInfo" ShowField="ImnName" UserSelectionMode="PeopleOnly" />' 'Assignee'
Ensure-Field 'IA_QnrSections' 'DueDate' '<Field Type="DateTime" DisplayName="Due Date" Name="DueDate" StaticName="DueDate" Group="IAMS" Required="FALSE" Format="DateOnly" />' 'Due Date'
Ensure-Field 'IA_QnrSections' 'SectionStatus' '<Field Type="Choice" DisplayName="Section Status" Name="SectionStatus" StaticName="SectionStatus" Group="IAMS" Required="FALSE" Indexed="TRUE" Format="Dropdown"><CHOICES><CHOICE>Not started</CHOICE><CHOICE>In progress</CHOICE><CHOICE>Submitted</CHOICE><CHOICE>Returned</CHOICE><CHOICE>Accepted</CHOICE></CHOICES><Default>Not started</Default></Field>' 'Section Status'
Ensure-Field 'IA_QnrSections' 'SubmittedDate' '<Field Type="DateTime" DisplayName="Submitted Date" Name="SubmittedDate" StaticName="SubmittedDate" Group="IAMS" Required="FALSE" Format="DateOnly" />' 'Submitted Date'
Ensure-Field 'IA_QnrSections' 'QuestionCount' '<Field Type="Number" DisplayName="Question Count" Name="QuestionCount" StaticName="QuestionCount" Group="IAMS" Required="FALSE"></Field>' 'Question Count'
Set-PnPField -List 'IA_QnrItems' -Identity 'Title' -Values @{Title='Ref'} | Out-Null
Ensure-Field 'IA_QnrItems' 'Questionnaire' '<Field Type="Lookup" DisplayName="Questionnaire" Name="Questionnaire" StaticName="Questionnaire" Group="IAMS" Required="TRUE" Indexed="TRUE" List="@@LIST:IA_Questionnaires@@" ShowField="Title" />' 'Questionnaire'
Ensure-Field 'IA_QnrItems' 'Section' '<Field Type="Lookup" DisplayName="Section" Name="Section" StaticName="Section" Group="IAMS" Required="TRUE" Indexed="TRUE" List="@@LIST:IA_QnrSections@@" ShowField="Title" />' 'Section'
Ensure-Field 'IA_QnrItems' 'SortOrder' '<Field Type="Number" DisplayName="Sort Order" Name="SortOrder" StaticName="SortOrder" Group="IAMS" Required="FALSE"></Field>' 'Sort Order'
Ensure-Field 'IA_QnrItems' 'Question' '<Field Type="Note" DisplayName="Question" Name="Question" StaticName="Question" Group="IAMS" Required="FALSE" NumLines="6" RichText="FALSE" />' 'Question'
Ensure-Field 'IA_QnrItems' 'AttachmentRequirement' '<Field Type="Note" DisplayName="Attachment Requirement" Name="AttachmentRequirement" StaticName="AttachmentRequirement" Group="IAMS" Required="FALSE" NumLines="6" RichText="FALSE" />' 'Attachment Requirement'
Ensure-Field 'IA_QnrItems' 'EvidenceRule' '<Field Type="Choice" DisplayName="Evidence Rule" Name="EvidenceRule" StaticName="EvidenceRule" Group="IAMS" Required="FALSE" Format="Dropdown"><CHOICES><CHOICE>If Yes</CHOICE><CHOICE>If No</CHOICE><CHOICE>Always</CHOICE><CHOICE>Never</CHOICE></CHOICES><Default>If Yes</Default></Field>' 'Evidence Rule'
Ensure-Field 'IA_QnrItems' 'ExplanationRequiredIfNo' '<Field Type="Boolean" DisplayName="Explanation Required if No" Name="ExplanationRequiredIfNo" StaticName="ExplanationRequiredIfNo" Group="IAMS" Required="FALSE"><Default>1</Default></Field>' 'Explanation Required if No'
Ensure-Field 'IA_QnrItems' 'IsException' '<Field Type="Boolean" DisplayName="Exception Question" Name="IsException" StaticName="IsException" Group="IAMS" Required="FALSE"><Default>0</Default></Field>' 'Exception Question'
Ensure-Field 'IA_QnrItems' 'Answer' '<Field Type="Choice" DisplayName="Answer" Name="Answer" StaticName="Answer" Group="IAMS" Required="FALSE" Format="Dropdown"><CHOICES><CHOICE>Yes</CHOICE><CHOICE>No</CHOICE></CHOICES></Field>' 'Answer'
Ensure-Field 'IA_QnrItems' 'DocumentRef' '<Field Type="Text" DisplayName="Document Ref" Name="DocumentRef" StaticName="DocumentRef" Group="IAMS" Required="FALSE" MaxLength="255" />' 'Document Ref'
Ensure-Field 'IA_QnrItems' 'Explanation' '<Field Type="Note" DisplayName="Explanation" Name="Explanation" StaticName="Explanation" Group="IAMS" Required="FALSE" NumLines="6" RichText="FALSE" />' 'Explanation'
Ensure-Field 'IA_QnrItems' 'ResponsibleOwner' '<Field Type="Text" DisplayName="Responsible Owner" Name="ResponsibleOwner" StaticName="ResponsibleOwner" Group="IAMS" Required="FALSE" MaxLength="255" />' 'Responsible Owner'
Ensure-Field 'IA_QnrItems' 'ReviewStatus' '<Field Type="Choice" DisplayName="Review Status" Name="ReviewStatus" StaticName="ReviewStatus" Group="IAMS" Required="FALSE" Format="Dropdown"><CHOICES><CHOICE>Pending</CHOICE><CHOICE>Accepted</CHOICE><CHOICE>Returned</CHOICE></CHOICES><Default>Pending</Default></Field>' 'Review Status'
Ensure-Field 'IA_QnrItems' 'ReviewerComment' '<Field Type="Note" DisplayName="Reviewer Comment" Name="ReviewerComment" StaticName="ReviewerComment" Group="IAMS" Required="FALSE" NumLines="6" RichText="FALSE" />' 'Reviewer Comment'
Ensure-Field 'IA_QnrItems' 'FindingRaised' '<Field Type="Lookup" DisplayName="Finding Raised" Name="FindingRaised" StaticName="FindingRaised" Group="IAMS" Required="FALSE" List="@@LIST:IA_Findings@@" ShowField="Title" />' 'Finding Raised'
Set-PnPField -List 'IA_QnrUploads' -Identity 'Title' -Values @{Title='Upload Title'} | Out-Null
Ensure-Field 'IA_QnrUploads' 'Engagement' '<Field Type="Lookup" DisplayName="Engagement" Name="Engagement" StaticName="Engagement" Group="IAMS" Required="TRUE" Indexed="TRUE" List="@@LIST:IA_Engagements@@" ShowField="Title" />' 'Engagement'
Ensure-Field 'IA_QnrUploads' 'AuditArea' '<Field Type="Lookup" DisplayName="Audit Area" Name="AuditArea" StaticName="AuditArea" Group="IAMS" Required="FALSE" List="@@LIST:IA_AuditUniverse@@" ShowField="Title" />' 'Audit Area'
Ensure-Field 'IA_QnrUploads' 'UploadStatus' '<Field Type="Choice" DisplayName="Upload Status" Name="UploadStatus" StaticName="UploadStatus" Group="IAMS" Required="FALSE" Format="Dropdown"><CHOICES><CHOICE>Uploaded</CHOICE><CHOICE>Validating</CHOICE><CHOICE>Draft Created</CHOICE><CHOICE>Rejected</CHOICE></CHOICES><Default>Uploaded</Default></Field>' 'Upload Status'
Ensure-Field 'IA_QnrUploads' 'ValidationMessage' '<Field Type="Note" DisplayName="Validation Message" Name="ValidationMessage" StaticName="ValidationMessage" Group="IAMS" Required="FALSE" NumLines="6" RichText="FALSE" />' 'Validation Message'
Ensure-Field 'IA_QnrUploads' 'Questionnaire' '<Field Type="Lookup" DisplayName="Questionnaire" Name="Questionnaire" StaticName="Questionnaire" Group="IAMS" Required="FALSE" List="@@LIST:IA_Questionnaires@@" ShowField="Title" />' 'Questionnaire'
Set-PnPField -List 'Knowledge Index' -Identity 'Title' -Values @{Title='Title'} | Out-Null
Ensure-Field 'Knowledge Index' 'DocGroup' '<Field Type="Choice" DisplayName="DocGroup" Name="DocGroup" StaticName="DocGroup" Group="IAMS" Required="TRUE" Format="Dropdown"><CHOICES><CHOICE>Governance</CHOICE><CHOICE>Methodology</CHOICE><CHOICE>System and templates</CHOICE><CHOICE>Reference</CHOICE></CHOICES></Field>' 'DocGroup'
Ensure-Field 'Knowledge Index' 'Description' '<Field Type="Text" DisplayName="Description" Name="Description" StaticName="Description" Group="IAMS" Required="FALSE" MaxLength="255" />' 'Description'
Ensure-Field 'Knowledge Index' 'DocLink' '<Field Type="URL" DisplayName="DocLink" Name="DocLink" StaticName="DocLink" Group="IAMS" Required="FALSE" Format="Hyperlink" />' 'DocLink'
Ensure-Field 'Knowledge Index' 'IconName' '<Field Type="Text" DisplayName="IconName" Name="IconName" StaticName="IconName" Group="IAMS" Required="FALSE" MaxLength="255" />' 'IconName'
Ensure-Field 'Knowledge Index' 'Version' '<Field Type="Text" DisplayName="Version" Name="Version" StaticName="Version" Group="IAMS" Required="FALSE" MaxLength="255" />' 'Version'
Ensure-Field 'Knowledge Index' 'ReviewDate' '<Field Type="DateTime" DisplayName="ReviewDate" Name="ReviewDate" StaticName="ReviewDate" Group="IAMS" Required="FALSE" Format="DateOnly" />' 'ReviewDate'
Ensure-Field 'Knowledge Index' 'SortOrder' '<Field Type="Number" DisplayName="SortOrder" Name="SortOrder" StaticName="SortOrder" Group="IAMS" Required="FALSE"></Field>' 'SortOrder'
Ensure-Field 'IA_WorkingPapers' 'Engagement' '<Field Type="Lookup" DisplayName="Engagement" Name="Engagement" StaticName="Engagement" Group="IAMS" Required="TRUE" Indexed="TRUE" List="@@LIST:IA_Engagements@@" ShowField="Title" />' 'Engagement'
Ensure-Field 'IA_WorkingPapers' 'Entity' '<Field Type="Lookup" DisplayName="Entity" Name="Entity" StaticName="Entity" Group="IAMS" Required="FALSE" Indexed="TRUE" List="@@LIST:IA_Entities@@" ShowField="Title" />' 'Entity'
Ensure-Field 'IA_WorkingPapers' 'FinancialYear' '<Field Type="Text" DisplayName="Financial Year" Name="FinancialYear" StaticName="FinancialYear" Group="IAMS" Required="FALSE" Indexed="TRUE" MaxLength="255" />' 'Financial Year'
Ensure-Field 'IA_WorkingPapers' 'AuditType' '<Field Type="Choice" DisplayName="Audit Type" Name="AuditType" StaticName="AuditType" Group="IAMS" Required="FALSE" Format="Dropdown"><CHOICES><CHOICE>Financial</CHOICE><CHOICE>Operational</CHOICE><CHOICE>Compliance</CHOICE><CHOICE>IT</CHOICE><CHOICE>Special Investigation</CHOICE><CHOICE>Follow-up</CHOICE><CHOICE>Advisory</CHOICE></CHOICES></Field>' 'Audit Type'
Ensure-Field 'IA_WorkingPapers' 'WPNumber' '<Field Type="Text" DisplayName="Working Paper Number" Name="WPNumber" StaticName="WPNumber" Group="IAMS" Required="FALSE" MaxLength="255" />' 'Working Paper Number'
Ensure-Field 'IA_WorkingPapers' 'PreparedBy' '<Field Type="User" DisplayName="Prepared By" Name="PreparedBy" StaticName="PreparedBy" Group="IAMS" Required="FALSE" List="UserInfo" ShowField="ImnName" UserSelectionMode="PeopleOnly" />' 'Prepared By'
Ensure-Field 'IA_WorkingPapers' 'ReviewedBy' '<Field Type="User" DisplayName="Reviewed By" Name="ReviewedBy" StaticName="ReviewedBy" Group="IAMS" Required="FALSE" List="UserInfo" ShowField="ImnName" UserSelectionMode="PeopleOnly" />' 'Reviewed By'
Ensure-Field 'IA_WorkingPapers' 'ReviewStatus' '<Field Type="Choice" DisplayName="Review Status" Name="ReviewStatus" StaticName="ReviewStatus" Group="IAMS" Required="FALSE" Format="Dropdown"><CHOICES><CHOICE>Draft</CHOICE><CHOICE>Prepared</CHOICE><CHOICE>Reviewed</CHOICE><CHOICE>Cleared</CHOICE></CHOICES><Default>Draft</Default></Field>' 'Review Status'
Ensure-Field 'IA_Evidence' 'Engagement' '<Field Type="Lookup" DisplayName="Engagement" Name="Engagement" StaticName="Engagement" Group="IAMS" Required="TRUE" Indexed="TRUE" List="@@LIST:IA_Engagements@@" ShowField="Title" />' 'Engagement'
Ensure-Field 'IA_Evidence' 'Finding' '<Field Type="Lookup" DisplayName="Finding" Name="Finding" StaticName="Finding" Group="IAMS" Required="FALSE" Indexed="TRUE" List="@@LIST:IA_Findings@@" ShowField="Title" />' 'Finding'
Ensure-Field 'IA_Evidence' 'Action' '<Field Type="Lookup" DisplayName="Action" Name="Action" StaticName="Action" Group="IAMS" Required="FALSE" List="@@LIST:IA_ActionPlans@@" ShowField="Title" />' 'Action'
Ensure-Field 'IA_Evidence' 'EvidenceType' '<Field Type="Choice" DisplayName="Evidence Type" Name="EvidenceType" StaticName="EvidenceType" Group="IAMS" Required="FALSE" Format="Dropdown"><CHOICES><CHOICE>Planning</CHOICE><CHOICE>Walkthrough</CHOICE><CHOICE>Sample</CHOICE><CHOICE>Testing</CHOICE><CHOICE>Management Evidence</CHOICE><CHOICE>Validation</CHOICE></CHOICES></Field>' 'Evidence Type'
Ensure-Field 'IA_Evidence' 'UploadedByUser' '<Field Type="User" DisplayName="Uploaded By" Name="UploadedByUser" StaticName="UploadedByUser" Group="IAMS" Required="FALSE" List="UserInfo" ShowField="ImnName" UserSelectionMode="PeopleOnly" />' 'Uploaded By'
Ensure-Field 'IA_QnrFiles' 'Engagement' '<Field Type="Lookup" DisplayName="Engagement" Name="Engagement" StaticName="Engagement" Group="IAMS" Required="FALSE" Indexed="TRUE" List="@@LIST:IA_Engagements@@" ShowField="Title" />' 'Engagement'
Ensure-Field 'IA_QnrFiles' 'Questionnaire' '<Field Type="Lookup" DisplayName="Questionnaire" Name="Questionnaire" StaticName="Questionnaire" Group="IAMS" Required="FALSE" Indexed="TRUE" List="@@LIST:IA_Questionnaires@@" ShowField="Title" />' 'Questionnaire'
Ensure-Field 'IA_QnrTemplates' 'TemplateVersion' '<Field Type="Text" DisplayName="Template Version" Name="TemplateVersion" StaticName="TemplateVersion" Group="IAMS" Required="FALSE" MaxLength="255" />' 'Template Version'
Ensure-Field 'IA_QnrTemplates' 'Active' '<Field Type="Boolean" DisplayName="Active" Name="Active" StaticName="Active" Group="IAMS" Required="FALSE"><Default>1</Default></Field>' 'Active'
Ensure-Field 'IA_Reports' 'Engagement' '<Field Type="Lookup" DisplayName="Engagement" Name="Engagement" StaticName="Engagement" Group="IAMS" Required="FALSE" Indexed="TRUE" List="@@LIST:IA_Engagements@@" ShowField="Title" />' 'Engagement'
Ensure-Field 'IA_Reports' 'Entity' '<Field Type="Lookup" DisplayName="Entity" Name="Entity" StaticName="Entity" Group="IAMS" Required="FALSE" List="@@LIST:IA_Entities@@" ShowField="Title" />' 'Entity'
Ensure-Field 'IA_Reports' 'ReportType' '<Field Type="Choice" DisplayName="Report Type" Name="ReportType" StaticName="ReportType" Group="IAMS" Required="TRUE" Indexed="TRUE" Format="Dropdown"><CHOICES><CHOICE>Draft Report</CHOICE><CHOICE>Final Report</CHOICE><CHOICE>Follow-Up Report</CHOICE><CHOICE>Quarterly IA Report</CHOICE><CHOICE>Annual IA Report</CHOICE><CHOICE>Outstanding Findings Report</CHOICE><CHOICE>Audit Plan Status</CHOICE></CHOICES></Field>' 'Report Type'
Ensure-Field 'IA_Reports' 'ReportPeriod' '<Field Type="Text" DisplayName="Report Period" Name="ReportPeriod" StaticName="ReportPeriod" Group="IAMS" Required="FALSE" MaxLength="255" />' 'Report Period'
Ensure-Field 'IA_Reports' 'VersionLabel' '<Field Type="Text" DisplayName="Version" Name="VersionLabel" StaticName="VersionLabel" Group="IAMS" Required="FALSE" MaxLength="255" />' 'Version'
Ensure-Field 'IA_Reports' 'ReportStatus' '<Field Type="Choice" DisplayName="Report Status" Name="ReportStatus" StaticName="ReportStatus" Group="IAMS" Required="FALSE" Format="Dropdown"><CHOICES><CHOICE>Draft</CHOICE><CHOICE>In Review</CHOICE><CHOICE>Approved</CHOICE><CHOICE>Issued</CHOICE></CHOICES><Default>Draft</Default></Field>' 'Report Status'

# ---- 3. Versioning, list settings, audit-log append-only text
Set-PnPList -Identity 'IA_Entities' -EnableVersioning $true -MajorVersions 50 | Out-Null
Set-PnPList -Identity 'IA_Departments' -EnableVersioning $true -MajorVersions 50 | Out-Null
Set-PnPList -Identity 'IA_AuditUniverse' -EnableVersioning $true -MajorVersions 50 | Out-Null
Set-PnPList -Identity 'IA_RiskRegister' -EnableVersioning $true -MajorVersions 50 | Out-Null
Set-PnPList -Identity 'IA_AuditPlan' -EnableVersioning $true -MajorVersions 50 | Out-Null
Set-PnPList -Identity 'IA_Engagements' -EnableVersioning $true -MajorVersions 50 | Out-Null
Set-PnPList -Identity 'IA_Milestones' -EnableVersioning $true -MajorVersions 50 | Out-Null
Set-PnPList -Identity 'IA_Findings' -EnableVersioning $true -MajorVersions 50 | Out-Null
Set-PnPList -Identity 'IA_ActionPlans' -EnableVersioning $true -MajorVersions 50 | Out-Null
Set-PnPList -Identity 'IA_FollowUps' -EnableVersioning $true -MajorVersions 50 | Out-Null
Set-PnPList -Identity 'IA_CSARegister' -EnableVersioning $true -MajorVersions 50 | Out-Null
Set-PnPList -Identity 'IA_AuditLog' -EnableVersioning $true -MajorVersions 50 | Out-Null
Set-PnPList -Identity 'IA_Config' -EnableVersioning $true -MajorVersions 50 | Out-Null
Set-PnPList -Identity 'IA_Questionnaires' -EnableVersioning $true -MajorVersions 50 | Out-Null
Set-PnPList -Identity 'IA_QnrSections' -EnableVersioning $true -MajorVersions 50 | Out-Null
Set-PnPList -Identity 'IA_QnrItems' -EnableVersioning $true -MajorVersions 50 | Out-Null
Set-PnPList -Identity 'IA_QnrUploads' -EnableVersioning $true -MajorVersions 50 | Out-Null
Set-PnPList -Identity 'Knowledge Index' -EnableVersioning $true -MajorVersions 50 | Out-Null
Set-PnPList -Identity 'IA_WorkingPapers' -EnableVersioning $true -MajorVersions 50 | Out-Null
Set-PnPList -Identity 'IA_Evidence' -EnableVersioning $true -MajorVersions 50 | Out-Null
Set-PnPList -Identity 'IA_QnrFiles' -EnableVersioning $true -MajorVersions 50 | Out-Null
Set-PnPList -Identity 'IA_QnrTemplates' -EnableVersioning $true -MajorVersions 50 | Out-Null
Set-PnPList -Identity 'Knowledge Documents' -EnableVersioning $true -MajorVersions 50 | Out-Null
Set-PnPList -Identity 'IA_Reports' -EnableVersioning $true -MajorVersions 50 | Out-Null
Set-PnPList -Identity 'IA_AuditLog' -EnableAttachments $false | Out-Null

# ---- 3b. Show the columns in each default view (long text columns left out to keep views readable)
Update-DefaultView 'IA_Entities' @('LinkTitle', 'EntityCode', 'EntityType', 'Country', 'EntityHead', 'EntityCEO', 'Active')
Update-DefaultView 'IA_Departments' @('LinkTitle', 'Entity', 'DepartmentHead', 'Active')
Update-DefaultView 'IA_AuditUniverse' @('LinkTitle', 'AuditAreaID', 'Entity', 'Department', 'ProcessCategory', 'ProcessOwner', 'RiskRating', 'RiskScore', 'LastAuditDate', 'AuditFrequency', 'NextAuditDate', 'UniverseStatus')
Update-DefaultView 'IA_RiskRegister' @('LinkTitle', 'RiskID', 'AuditArea', 'Entity', 'RiskCategory', 'Likelihood', 'ImpactScore', 'InherentRisk', 'ControlRating', 'ResidualRisk', 'RiskOwner', 'RiskStatus')
Update-DefaultView 'IA_AuditPlan' @('LinkTitle', 'AuditRef', 'PlanYear', 'AuditArea', 'Entity', 'AuditType', 'PlannedStart', 'PlannedFinish', 'RiskScore', 'AssignedAuditor', 'AuditManager', 'BudgetHours', 'ActualHours', 'AuditStatus', 'ApprovalStatus')
Update-DefaultView 'IA_Engagements' @('LinkTitle', 'EngagementID', 'AuditPlanItem', 'Entity', 'LeadAuditor', 'TeamMembers', 'ActualStart', 'ActualEnd', 'Stage', 'OverallOpinion', 'EngagementFolderUrl', 'Engagement_x0020_Type', 'BudgetedHours', 'EngActualHours', 'PlanningType', 'AuditManager')
Update-DefaultView 'IA_Milestones' @('LinkTitle', 'Engagement', 'MilestoneType', 'DueDate', 'CompletedDate', 'MilestoneOwner', 'MilestoneStatus')
Update-DefaultView 'IA_Findings' @('LinkTitle', 'FindingID', 'Engagement', 'Entity', 'Department', 'RiskCategory', 'Rating', 'WorkflowStage', 'AgreementStatus', 'ResponsibleManager', 'DateIssued', 'OriginalDueDate', 'DueDate', 'ExtensionCount', 'FindingStatus', 'ClosedDate', 'LastProcessedStage', 'Compliance_x0020_Result', 'MgmtAcceptance', 'MgmtResponseDate')
Update-DefaultView 'IA_ActionPlans' @('LinkTitle', 'CAPAID', 'Finding', 'Entity', 'ActionOwner', 'DueDate', 'CompletionPct', 'EvidenceUploaded', 'ValidationStatus', 'FollowUpAuditor', 'FindingRating', 'ActionStatus', 'ReminderStage', 'CompletedDate', 'ExtensionCount', 'OriginalDueDate', 'ClosureProcessed')
Update-DefaultView 'IA_FollowUps' @('LinkTitle', 'Finding', 'Action', 'Reviewer', 'ReviewDate', 'Outcome', 'ValidationDocUrl')
Update-DefaultView 'IA_CSARegister' @('LinkTitle', 'CSAID', 'Entity', 'Department', 'AssessmentPeriod', 'SubmissionDate', 'SubmittedBy', 'Score', 'Result', 'FormResponseId', 'RelatedAudit', 'AttachmentsUrl')
Update-DefaultView 'IA_AuditLog' @('LinkTitle', 'SourceList', 'SourceItemId', 'EventType', 'EventBy')
Update-DefaultView 'IA_Config' @('LinkTitle', 'ConfigValue', 'ConfigDescription')
Update-DefaultView 'IA_Questionnaires' @('LinkTitle', 'QuestionnaireID', 'Engagement', 'AuditType', 'TemplateVersion', 'QuestionnaireStatus', 'Round', 'IssuedDate', 'PreparedBy', 'Reviewer', 'SourceFileUrl', 'QuestionCount')
Update-DefaultView 'IA_QnrSections' @('LinkTitle', 'Questionnaire', 'SectionNo', 'Assignee', 'DueDate', 'SectionStatus', 'SubmittedDate', 'QuestionCount')
Update-DefaultView 'IA_QnrItems' @('LinkTitle', 'Questionnaire', 'Section', 'SortOrder', 'EvidenceRule', 'ExplanationRequiredIfNo', 'IsException', 'Answer', 'DocumentRef', 'ResponsibleOwner', 'ReviewStatus', 'FindingRaised')
Update-DefaultView 'IA_QnrUploads' @('LinkTitle', 'Engagement', 'AuditArea', 'UploadStatus', 'Questionnaire')
Update-DefaultView 'Knowledge Index' @('LinkTitle', 'DocGroup', 'Description', 'DocLink', 'IconName', 'Version', 'ReviewDate', 'SortOrder')
Update-DefaultView 'IA_WorkingPapers' @('DocIcon', 'LinkFilename', 'Engagement', 'Entity', 'FinancialYear', 'AuditType', 'WPNumber', 'PreparedBy', 'ReviewedBy', 'ReviewStatus')
Update-DefaultView 'IA_Evidence' @('DocIcon', 'LinkFilename', 'Engagement', 'Finding', 'Action', 'EvidenceType', 'UploadedByUser')
Update-DefaultView 'IA_QnrFiles' @('DocIcon', 'LinkFilename', 'Engagement', 'Questionnaire')
Update-DefaultView 'IA_QnrTemplates' @('DocIcon', 'LinkFilename', 'TemplateVersion', 'Active')
Update-DefaultView 'Knowledge Documents' @('DocIcon', 'LinkFilename')
Update-DefaultView 'IA_Reports' @('DocIcon', 'LinkFilename', 'Engagement', 'Entity', 'ReportType', 'ReportPeriod', 'VersionLabel', 'ReportStatus')

# ---- 4. Evidence/Working-paper subfolder template (created per engagement by flow WF1; sample root only)
# Subfolders per engagement: Planning, Walkthroughs, Samples, Testing, Reports, Management Evidence

# ---- 5. Seed configuration values
if (-not (Get-PnPListItem -List 'IA_Config' -Query "<View><Query><Where><Eq><FieldRef Name='Title'/><Value Type='Text'>ReminderDays1</Value></Eq></Where></Query></View>")) { Add-PnPListItem -List 'IA_Config' -Values @{Title='ReminderDays1'; ConfigValue='30'; ConfigDescription='First reminder: days before due date'} | Out-Null }
if (-not (Get-PnPListItem -List 'IA_Config' -Query "<View><Query><Where><Eq><FieldRef Name='Title'/><Value Type='Text'>ReminderDays2</Value></Eq></Where></Query></View>")) { Add-PnPListItem -List 'IA_Config' -Values @{Title='ReminderDays2'; ConfigValue='15'; ConfigDescription='Second reminder: days before due date'} | Out-Null }
if (-not (Get-PnPListItem -List 'IA_Config' -Query "<View><Query><Where><Eq><FieldRef Name='Title'/><Value Type='Text'>EscalateCEOAfterDays</Value></Eq></Where></Query></View>")) { Add-PnPListItem -List 'IA_Config' -Values @{Title='EscalateCEOAfterDays'; ConfigValue='30'; ConfigDescription='Days overdue before CEO escalation'} | Out-Null }
if (-not (Get-PnPListItem -List 'IA_Config' -Query "<View><Query><Where><Eq><FieldRef Name='Title'/><Value Type='Text'>GroupCEOEmail</Value></Eq></Where></Query></View>")) { Add-PnPListItem -List 'IA_Config' -Values @{Title='GroupCEOEmail'; ConfigValue='TBD'; ConfigDescription='Fallback CEO email if entity CEO is blank'} | Out-Null }
if (-not (Get-PnPListItem -List 'IA_Config' -Query "<View><Query><Where><Eq><FieldRef Name='Title'/><Value Type='Text'>HeadOfIAEmail</Value></Eq></Where></Query></View>")) { Add-PnPListItem -List 'IA_Config' -Values @{Title='HeadOfIAEmail'; ConfigValue='TBD'; ConfigDescription='Group Head of Internal Audit email'} | Out-Null }
if (-not (Get-PnPListItem -List 'IA_Config' -Query "<View><Query><Where><Eq><FieldRef Name='Title'/><Value Type='Text'>Role.Owner</Value></Eq></Where></Query></View>")) { Add-PnPListItem -List 'IA_Config' -Values @{Title='Role.Owner'; ConfigValue=';'; ConfigDescription='Semicolon-separated emails of people holding the Owner role. Read by the app on start. Format: ;a@x.com;b@x.com;'} | Out-Null }
if (-not (Get-PnPListItem -List 'IA_Config' -Query "<View><Query><Where><Eq><FieldRef Name='Title'/><Value Type='Text'>Role.Manager</Value></Eq></Where></Query></View>")) { Add-PnPListItem -List 'IA_Config' -Values @{Title='Role.Manager'; ConfigValue=';'; ConfigDescription='Semicolon-separated emails of people holding the Manager role. Read by the app on start. Format: ;a@x.com;b@x.com;'} | Out-Null }
if (-not (Get-PnPListItem -List 'IA_Config' -Query "<View><Query><Where><Eq><FieldRef Name='Title'/><Value Type='Text'>Role.Auditor</Value></Eq></Where></Query></View>")) { Add-PnPListItem -List 'IA_Config' -Values @{Title='Role.Auditor'; ConfigValue=';'; ConfigDescription='Semicolon-separated emails of people holding the Auditor role. Read by the app on start. Format: ;a@x.com;b@x.com;'} | Out-Null }
if (-not (Get-PnPListItem -List 'IA_Config' -Query "<View><Query><Where><Eq><FieldRef Name='Title'/><Value Type='Text'>Role.ActionOwner</Value></Eq></Where></Query></View>")) { Add-PnPListItem -List 'IA_Config' -Values @{Title='Role.ActionOwner'; ConfigValue=';'; ConfigDescription='Semicolon-separated emails of people holding the ActionOwner role. Read by the app on start. Format: ;a@x.com;b@x.com;'} | Out-Null }
if (-not (Get-PnPListItem -List 'IA_Config' -Query "<View><Query><Where><Eq><FieldRef Name='Title'/><Value Type='Text'>Role.Executive</Value></Eq></Where></Query></View>")) { Add-PnPListItem -List 'IA_Config' -Values @{Title='Role.Executive'; ConfigValue=';'; ConfigDescription='Semicolon-separated emails of people holding the Executive role. Read by the app on start. Format: ;a@x.com;b@x.com;'} | Out-Null }
if (-not (Get-PnPListItem -List 'IA_Config' -Query "<View><Query><Where><Eq><FieldRef Name='Title'/><Value Type='Text'>Role.BUHead</Value></Eq></Where></Query></View>")) { Add-PnPListItem -List 'IA_Config' -Values @{Title='Role.BUHead'; ConfigValue=';'; ConfigDescription='Semicolon-separated emails of people holding the BUHead role. Read by the app on start. Format: ;a@x.com;b@x.com;'} | Out-Null }
if (-not (Get-PnPListItem -List 'IA_Config' -Query "<View><Query><Where><Eq><FieldRef Name='Title'/><Value Type='Text'>Role.DepartmentHead</Value></Eq></Where></Query></View>")) { Add-PnPListItem -List 'IA_Config' -Values @{Title='Role.DepartmentHead'; ConfigValue=';'; ConfigDescription='Semicolon-separated emails of people holding the DepartmentHead role. Read by the app on start. Format: ;a@x.com;b@x.com;'} | Out-Null }

# ---- 5b. Resource Centre catalogue (Knowledge Index). DocLink is filled in later, once the documents are uploaded.
if (-not (Get-PnPListItem -List 'Knowledge Index' | Where-Object { $_['Title'] -eq 'Internal Audit Charter' })) { Add-PnPListItem -List 'Knowledge Index' -Values @{Title='Internal Audit Charter'; DocGroup='Governance'; Description='Mandate and authority'; IconName='scale'; SortOrder=1} | Out-Null }
if (-not (Get-PnPListItem -List 'Knowledge Index' | Where-Object { $_['Title'] -eq 'Code of Ethics and Independence' })) { Add-PnPListItem -List 'Knowledge Index' -Values @{Title='Code of Ethics and Independence'; DocGroup='Governance'; Description='Conduct and declaration'; IconName='shield'; SortOrder=2} | Out-Null }
if (-not (Get-PnPListItem -List 'Knowledge Index' | Where-Object { $_['Title'] -eq 'Internal Audit Methodology' })) { Add-PnPListItem -List 'Knowledge Index' -Values @{Title='Internal Audit Methodology'; DocGroup='Methodology'; Description='End-to-end approach'; IconName='route'; SortOrder=3} | Out-Null }
if (-not (Get-PnPListItem -List 'Knowledge Index' | Where-Object { $_['Title'] -eq 'Annual Audit Plan and Risk Assessment' })) { Add-PnPListItem -List 'Knowledge Index' -Values @{Title='Annual Audit Plan and Risk Assessment'; DocGroup='Methodology'; Description='How the plan is built'; IconName='calendar'; SortOrder=4} | Out-Null }
if (-not (Get-PnPListItem -List 'Knowledge Index' | Where-Object { $_['Title'] -eq 'Audit Report Rating Guide' })) { Add-PnPListItem -List 'Knowledge Index' -Values @{Title='Audit Report Rating Guide'; DocGroup='Methodology'; Description='Opinion and severity scale'; IconName='chart'; SortOrder=5} | Out-Null }
if (-not (Get-PnPListItem -List 'Knowledge Index' | Where-Object { $_['Title'] -eq 'Sampling Guide' })) { Add-PnPListItem -List 'Knowledge Index' -Values @{Title='Sampling Guide'; DocGroup='Methodology'; Description='Sample sizes and selection'; IconName='sliders'; SortOrder=6} | Out-Null }
if (-not (Get-PnPListItem -List 'Knowledge Index' | Where-Object { $_['Title'] -eq 'Working-paper Standards' })) { Add-PnPListItem -List 'Knowledge Index' -Values @{Title='Working-paper Standards'; DocGroup='Methodology'; Description='Documentation rules'; IconName='files'; SortOrder=7} | Out-Null }
if (-not (Get-PnPListItem -List 'Knowledge Index' | Where-Object { $_['Title'] -eq 'IMS User Manual' })) { Add-PnPListItem -List 'Knowledge Index' -Values @{Title='IMS User Manual'; DocGroup='System and templates'; Description='Full system guide'; IconName='book'; SortOrder=8} | Out-Null }
if (-not (Get-PnPListItem -List 'Knowledge Index' | Where-Object { $_['Title'] -eq 'Quick-start Guide' })) { Add-PnPListItem -List 'Knowledge Index' -Values @{Title='Quick-start Guide'; DocGroup='System and templates'; Description='One-page guide'; IconName='bolt'; SortOrder=9} | Out-Null }
if (-not (Get-PnPListItem -List 'Knowledge Index' | Where-Object { $_['Title'] -eq 'Questionnaire Templates' })) { Add-PnPListItem -List 'Knowledge Index' -Values @{Title='Questionnaire Templates'; DocGroup='System and templates'; Description='Linked to Questionnaires tab'; IconName='clipboard'; SortOrder=10} | Out-Null }
if (-not (Get-PnPListItem -List 'Knowledge Index' | Where-Object { $_['Title'] -eq 'IIA Global Internal Audit Standards' })) { Add-PnPListItem -List 'Knowledge Index' -Values @{Title='IIA Global Internal Audit Standards'; DocGroup='Reference'; Description='Professional standards'; IconName='bank'; SortOrder=11} | Out-Null }
if (-not (Get-PnPListItem -List 'Knowledge Index' | Where-Object { $_['Title'] -eq 'Glossary' })) { Add-PnPListItem -List 'Knowledge Index' -Values @{Title='Glossary'; DocGroup='Reference'; Description='CAPA, Follow-Up, Residual risk'; IconName='abc'; SortOrder=12} | Out-Null }
if (-not (Get-PnPListItem -List 'Knowledge Index' | Where-Object { $_['Title'] -eq 'Contacts' })) { Add-PnPListItem -List 'Knowledge Index' -Values @{Title='Contacts'; DocGroup='Reference'; Description='Who to call for what'; IconName='contacts'; SortOrder=13} | Out-Null }
if (-not (Get-PnPListItem -List 'Knowledge Index' | Where-Object { $_['Title'] -eq 'What''s New' })) { Add-PnPListItem -List 'Knowledge Index' -Values @{Title='What''s New'; DocGroup='Reference'; Description='IAMS release notes'; IconName='spark'; SortOrder=14} | Out-Null }

# ---- 6. Groups and baseline list-level permissions
# Only UNQUALIFIED permissions are applied. Anything marked '(assigned)', '(own ...)' or 'issued only' in the Security sheet
# is intentionally NOT granted here; it is applied at folder/item level by flows WF1/WF3 so users never see more than intended.
if (-not (Get-PnPGroup -Identity 'IA_Owners' -ErrorAction SilentlyContinue)) { New-PnPGroup -Title 'IA_Owners' -Description 'Group Head of IA' | Out-Null }
if (-not (Get-PnPGroup -Identity 'IA_Managers' -ErrorAction SilentlyContinue)) { New-PnPGroup -Title 'IA_Managers' -Description 'Audit Managers' | Out-Null }
if (-not (Get-PnPGroup -Identity 'IA_Auditors' -ErrorAction SilentlyContinue)) { New-PnPGroup -Title 'IA_Auditors' -Description 'Auditors' | Out-Null }
if (-not (Get-PnPGroup -Identity 'IA_ActionOwners' -ErrorAction SilentlyContinue)) { New-PnPGroup -Title 'IA_ActionOwners' -Description 'Action Owners / Management' | Out-Null }
if (-not (Get-PnPGroup -Identity 'IA_Executives' -ErrorAction SilentlyContinue)) { New-PnPGroup -Title 'IA_Executives' -Description 'Executives / Audit Committee' | Out-Null }
if (-not (Get-PnPGroup -Identity 'IA_BUHeads' -ErrorAction SilentlyContinue)) { New-PnPGroup -Title 'IA_BUHeads' -Description 'Business Unit Heads' | Out-Null }
if (-not (Get-PnPGroup -Identity 'IA_DepartmentHeads' -ErrorAction SilentlyContinue)) { New-PnPGroup -Title 'IA_DepartmentHeads' -Description 'Department Heads' | Out-Null }
Set-PnPList -Identity 'IA_ActionPlans' -BreakRoleInheritance -CopyRoleAssignments:$false -ClearSubscopes | Out-Null
Set-PnPListPermission -Identity 'IA_ActionPlans' -Group 'IA_Owners' -AddRole 'Full Control'
Set-PnPListPermission -Identity 'IA_ActionPlans' -Group 'IA_Managers' -AddRole 'Edit'
Set-PnPListPermission -Identity 'IA_ActionPlans' -Group 'IA_Auditors' -AddRole 'Contribute'
Set-PnPListPermission -Identity 'IA_ActionPlans' -Group 'IA_Executives' -AddRole 'Read'
Set-PnPList -Identity 'IA_AuditLog' -BreakRoleInheritance -CopyRoleAssignments:$false -ClearSubscopes | Out-Null
Set-PnPListPermission -Identity 'IA_AuditLog' -Group 'IA_Owners' -AddRole 'Read'
Set-PnPListPermission -Identity 'IA_AuditLog' -Group 'IA_Managers' -AddRole 'Read'
Set-PnPList -Identity 'IA_AuditPlan' -BreakRoleInheritance -CopyRoleAssignments:$false -ClearSubscopes | Out-Null
Set-PnPListPermission -Identity 'IA_AuditPlan' -Group 'IA_Owners' -AddRole 'Full Control'
Set-PnPListPermission -Identity 'IA_AuditPlan' -Group 'IA_Managers' -AddRole 'Edit'
Set-PnPListPermission -Identity 'IA_AuditPlan' -Group 'IA_Executives' -AddRole 'Read'
Set-PnPList -Identity 'IA_AuditUniverse' -BreakRoleInheritance -CopyRoleAssignments:$false -ClearSubscopes | Out-Null
Set-PnPListPermission -Identity 'IA_AuditUniverse' -Group 'IA_Owners' -AddRole 'Full Control'
Set-PnPListPermission -Identity 'IA_AuditUniverse' -Group 'IA_Managers' -AddRole 'Edit'
Set-PnPListPermission -Identity 'IA_AuditUniverse' -Group 'IA_Auditors' -AddRole 'Read'
Set-PnPListPermission -Identity 'IA_AuditUniverse' -Group 'IA_Executives' -AddRole 'Read'
Set-PnPList -Identity 'IA_CSARegister' -BreakRoleInheritance -CopyRoleAssignments:$false -ClearSubscopes | Out-Null
Set-PnPListPermission -Identity 'IA_CSARegister' -Group 'IA_Owners' -AddRole 'Full Control'
Set-PnPListPermission -Identity 'IA_CSARegister' -Group 'IA_Managers' -AddRole 'Edit'
Set-PnPListPermission -Identity 'IA_CSARegister' -Group 'IA_Auditors' -AddRole 'Read'
Set-PnPListPermission -Identity 'IA_CSARegister' -Group 'IA_Executives' -AddRole 'Read'
Set-PnPList -Identity 'IA_Config' -BreakRoleInheritance -CopyRoleAssignments:$false -ClearSubscopes | Out-Null
Set-PnPListPermission -Identity 'IA_Config' -Group 'IA_Owners' -AddRole 'Full Control'
Set-PnPListPermission -Identity 'IA_Config' -Group 'IA_Managers' -AddRole 'Edit'
Set-PnPList -Identity 'IA_Departments' -BreakRoleInheritance -CopyRoleAssignments:$false -ClearSubscopes | Out-Null
Set-PnPListPermission -Identity 'IA_Departments' -Group 'IA_Owners' -AddRole 'Full Control'
Set-PnPListPermission -Identity 'IA_Departments' -Group 'IA_Managers' -AddRole 'Edit'
Set-PnPListPermission -Identity 'IA_Departments' -Group 'IA_Auditors' -AddRole 'Read'
Set-PnPListPermission -Identity 'IA_Departments' -Group 'IA_ActionOwners' -AddRole 'Read'
Set-PnPListPermission -Identity 'IA_Departments' -Group 'IA_Executives' -AddRole 'Read'
Set-PnPListPermission -Identity 'IA_Departments' -Group 'IA_BUHeads' -AddRole 'Read'
Set-PnPListPermission -Identity 'IA_Departments' -Group 'IA_DepartmentHeads' -AddRole 'Read'
Set-PnPList -Identity 'IA_Engagements' -BreakRoleInheritance -CopyRoleAssignments:$false -ClearSubscopes | Out-Null
Set-PnPListPermission -Identity 'IA_Engagements' -Group 'IA_Owners' -AddRole 'Full Control'
Set-PnPListPermission -Identity 'IA_Engagements' -Group 'IA_Managers' -AddRole 'Edit'
Set-PnPListPermission -Identity 'IA_Engagements' -Group 'IA_Executives' -AddRole 'Read'
Set-PnPList -Identity 'IA_Entities' -BreakRoleInheritance -CopyRoleAssignments:$false -ClearSubscopes | Out-Null
Set-PnPListPermission -Identity 'IA_Entities' -Group 'IA_Owners' -AddRole 'Full Control'
Set-PnPListPermission -Identity 'IA_Entities' -Group 'IA_Managers' -AddRole 'Edit'
Set-PnPListPermission -Identity 'IA_Entities' -Group 'IA_Auditors' -AddRole 'Read'
Set-PnPListPermission -Identity 'IA_Entities' -Group 'IA_ActionOwners' -AddRole 'Read'
Set-PnPListPermission -Identity 'IA_Entities' -Group 'IA_Executives' -AddRole 'Read'
Set-PnPListPermission -Identity 'IA_Entities' -Group 'IA_BUHeads' -AddRole 'Read'
Set-PnPListPermission -Identity 'IA_Entities' -Group 'IA_DepartmentHeads' -AddRole 'Read'
Set-PnPList -Identity 'IA_Evidence' -BreakRoleInheritance -CopyRoleAssignments:$false -ClearSubscopes | Out-Null
Set-PnPListPermission -Identity 'IA_Evidence' -Group 'IA_Owners' -AddRole 'Full Control'
Set-PnPListPermission -Identity 'IA_Evidence' -Group 'IA_Managers' -AddRole 'Edit'
Set-PnPListPermission -Identity 'IA_Evidence' -Group 'IA_Auditors' -AddRole 'Contribute'
Set-PnPList -Identity 'IA_Findings' -BreakRoleInheritance -CopyRoleAssignments:$false -ClearSubscopes | Out-Null
Set-PnPListPermission -Identity 'IA_Findings' -Group 'IA_Owners' -AddRole 'Full Control'
Set-PnPListPermission -Identity 'IA_Findings' -Group 'IA_Managers' -AddRole 'Edit'
Set-PnPListPermission -Identity 'IA_Findings' -Group 'IA_Auditors' -AddRole 'Contribute'
Set-PnPListPermission -Identity 'IA_Findings' -Group 'IA_Executives' -AddRole 'Read'
Set-PnPList -Identity 'IA_FollowUps' -BreakRoleInheritance -CopyRoleAssignments:$false -ClearSubscopes | Out-Null
Set-PnPListPermission -Identity 'IA_FollowUps' -Group 'IA_Owners' -AddRole 'Full Control'
Set-PnPListPermission -Identity 'IA_FollowUps' -Group 'IA_Managers' -AddRole 'Edit'
Set-PnPListPermission -Identity 'IA_FollowUps' -Group 'IA_Auditors' -AddRole 'Contribute'
Set-PnPListPermission -Identity 'IA_FollowUps' -Group 'IA_Executives' -AddRole 'Read'
Set-PnPList -Identity 'IA_Milestones' -BreakRoleInheritance -CopyRoleAssignments:$false -ClearSubscopes | Out-Null
Set-PnPListPermission -Identity 'IA_Milestones' -Group 'IA_Owners' -AddRole 'Full Control'
Set-PnPListPermission -Identity 'IA_Milestones' -Group 'IA_Managers' -AddRole 'Edit'
Set-PnPListPermission -Identity 'IA_Milestones' -Group 'IA_Executives' -AddRole 'Read'
Set-PnPList -Identity 'IA_Reports' -BreakRoleInheritance -CopyRoleAssignments:$false -ClearSubscopes | Out-Null
Set-PnPListPermission -Identity 'IA_Reports' -Group 'IA_Owners' -AddRole 'Full Control'
Set-PnPListPermission -Identity 'IA_Reports' -Group 'IA_Managers' -AddRole 'Edit'
Set-PnPListPermission -Identity 'IA_Reports' -Group 'IA_Auditors' -AddRole 'Read'
Set-PnPListPermission -Identity 'IA_Reports' -Group 'IA_Executives' -AddRole 'Read'
Set-PnPList -Identity 'IA_RiskRegister' -BreakRoleInheritance -CopyRoleAssignments:$false -ClearSubscopes | Out-Null
Set-PnPListPermission -Identity 'IA_RiskRegister' -Group 'IA_Owners' -AddRole 'Full Control'
Set-PnPListPermission -Identity 'IA_RiskRegister' -Group 'IA_Managers' -AddRole 'Edit'
Set-PnPListPermission -Identity 'IA_RiskRegister' -Group 'IA_Auditors' -AddRole 'Contribute'
Set-PnPListPermission -Identity 'IA_RiskRegister' -Group 'IA_Executives' -AddRole 'Read'
Set-PnPList -Identity 'IA_WorkingPapers' -BreakRoleInheritance -CopyRoleAssignments:$false -ClearSubscopes | Out-Null
Set-PnPListPermission -Identity 'IA_WorkingPapers' -Group 'IA_Owners' -AddRole 'Full Control'
Set-PnPListPermission -Identity 'IA_WorkingPapers' -Group 'IA_Managers' -AddRole 'Edit'
Set-PnPListPermission -Identity 'IA_WorkingPapers' -Group 'IA_Auditors' -AddRole 'Contribute'

# ---- 7. Friendly display titles (done last so lookups above resolve by internal name)
Set-PnPList -Identity 'IA_Entities' -Title 'Entities' | Out-Null
Set-PnPList -Identity 'IA_Departments' -Title 'Departments' | Out-Null
Set-PnPList -Identity 'IA_AuditUniverse' -Title 'Audit Universe' | Out-Null
Set-PnPList -Identity 'IA_RiskRegister' -Title 'Risk Register' | Out-Null
Set-PnPList -Identity 'IA_AuditPlan' -Title 'Annual Audit Plan' | Out-Null
Set-PnPList -Identity 'IA_Engagements' -Title 'Audit Engagements' | Out-Null
Set-PnPList -Identity 'IA_Milestones' -Title 'Engagement Milestones' | Out-Null
Set-PnPList -Identity 'IA_Findings' -Title 'Audit Findings Register' | Out-Null
Set-PnPList -Identity 'IA_ActionPlans' -Title 'Corrective Action Tracker' | Out-Null
Set-PnPList -Identity 'IA_FollowUps' -Title 'Follow-Up Reviews' | Out-Null
Set-PnPList -Identity 'IA_CSARegister' -Title 'Self Assessment Register' | Out-Null
Set-PnPList -Identity 'IA_AuditLog' -Title 'Audit Trail' | Out-Null
Set-PnPList -Identity 'IA_Config' -Title 'IA Configuration' | Out-Null
Set-PnPList -Identity 'IA_Questionnaires' -Title 'Audit Questionnaires' | Out-Null
Set-PnPList -Identity 'IA_QnrSections' -Title 'Questionnaire Sections' | Out-Null
Set-PnPList -Identity 'IA_QnrItems' -Title 'Questionnaire Items' | Out-Null
Set-PnPList -Identity 'IA_QnrUploads' -Title 'Questionnaire Uploads' | Out-Null
Set-PnPList -Identity 'Knowledge Index' -Title 'Knowledge Index' | Out-Null
Set-PnPList -Identity 'IA_WorkingPapers' -Title 'Audit Working Papers' | Out-Null
Set-PnPList -Identity 'IA_Evidence' -Title 'Evidence Repository' | Out-Null
Set-PnPList -Identity 'IA_QnrFiles' -Title 'Questionnaire Files' | Out-Null
Set-PnPList -Identity 'IA_QnrTemplates' -Title 'Questionnaire Templates' | Out-Null
Set-PnPList -Identity 'Knowledge Documents' -Title 'Knowledge Documents' | Out-Null
Set-PnPList -Identity 'IA_Reports' -Title 'Reports Library' | Out-Null

Write-Host 'IAMS provisioning complete. Next: add members to IA_* groups, set Entity CEO/Dept Head data, build flows WF0-WF7.'

<#
 MHAO IAMS - prepare the Power Automate solution for YOUR tenant.
 The repo copy (solutions/IAMSAllFlows) is sanitised: the site address is YOURTENANT.sharepoint.com and every list
 is a token (@@LIST:IA_Findings@@). This script reads the real list IDs from YOUR site (after Provision-IAMS.ps1
 has created it), fills them in, and writes IAMSAllFlows_ready.zip, which you import in Power Automate.

 Usage:  .\Prepare-FlowSolution.ps1 -SiteUrl https://contoso.sharepoint.com/sites/InternalAudit -ClientId <Entra app id>
 Needs:  PnP.PowerShell (same app registration as Provision-IAMS.ps1). Also replaces the 'user@example.com' placeholder
         with -DefaultEmail (the address that receives flow notices / acts as fallback approver).
#>
param(
  [Parameter(Mandatory=$true)][string]$SiteUrl,
  [Parameter(Mandatory=$true)][string]$ClientId,
  [Parameter(Mandatory=$true)][string]$DefaultEmail,
  [string]$Out = (Join-Path $PSScriptRoot 'IAMSAllFlows_ready.zip')
)
$ErrorActionPreference = 'Stop'
Connect-PnPOnline -Url $SiteUrl -Interactive -ClientId $ClientId
$work = Join-Path ([IO.Path]::GetTempPath()) ('iams_flows_' + [guid]::NewGuid())
Copy-Item (Join-Path $PSScriptRoot 'solutions\IAMSAllFlows') $work -Recurse
$lists = Get-PnPList -Includes RootFolder
$map = @{}
foreach ($l in $lists) { $map[$l.RootFolder.Name] = $l.Id.ToString() }
$tenantSite = [regex]::Match($SiteUrl, '^https://[^/]+').Value -replace '^https://',''
$sitePath = ([Uri]$SiteUrl).AbsolutePath
$missing = @()
Get-ChildItem $work -Recurse -File | ForEach-Object {
  $t = [IO.File]::ReadAllText($_.FullName)
  $t = [regex]::Replace($t, '@@LIST:([^@]+)@@', { param($m) $n = $m.Groups[1].Value; if ($map.ContainsKey($n)) { $map[$n] } else { $script:missing += $n; $m.Value } })
  $t = $t.Replace('https://YOURTENANT.sharepoint.com/sites/InternalAuditTest', $SiteUrl).Replace('YOURTENANT.sharepoint.com', $tenantSite).Replace('/sites/InternalAuditTest', $sitePath).Replace('user@example.com', $DefaultEmail)
  [IO.File]::WriteAllText($_.FullName, $t, (New-Object Text.UTF8Encoding($false)))
}
if ($missing) { throw "Lists not found on the site (run Provision-IAMS.ps1 first): $(($missing | Select-Object -Unique) -join ', ')" }
if (Test-Path $Out) { Remove-Item $Out }
Compress-Archive -Path (Join-Path $work '*') -DestinationPath $Out
Remove-Item $work -Recurse -Force
Write-Host "Done: $Out  -> Power Automate > Solutions > Import solution"

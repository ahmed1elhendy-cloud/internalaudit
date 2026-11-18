<#
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
{
 "entities": [
  {
   "Title": "MHAO Group",
   "EntityCode": "MHAO",
   "EntityType": "Parent",
   "Country": "UAE",
   "EntityHead": null,
   "EntityCEO": null,
   "Active": true
  },
  {
   "Title": "AVIS UAE Rent A Car",
   "EntityCode": "AVIS",
   "EntityType": "Subsidiary",
   "Country": "UAE",
   "EntityHead": null,
   "EntityCEO": null,
   "Active": true
  },
  {
   "Title": "AVIS Emirates for Luxury Transportation",
   "EntityCode": "AEFLT",
   "EntityType": "Subsidiary",
   "Country": "UAE",
   "EntityHead": null,
   "EntityCEO": null,
   "Active": true
  },
  {
   "Title": "Al Otaiba General Transport",
   "EntityCode": "AOGT",
   "EntityType": "Subsidiary",
   "Country": "UAE",
   "EntityHead": null,
   "EntityCEO": null,
   "Active": true
  },
  {
   "Title": "Bright Spark Auto Repairing",
   "EntityCode": "BSAR",
   "EntityType": "Subsidiary",
   "Country": "UAE",
   "EntityHead": null,
   "EntityCEO": null,
   "Active": true
  },
  {
   "Title": "MHAO Mobility",
   "EntityCode": "MOB",
   "EntityType": "Subsidiary",
   "Country": "UAE",
   "EntityHead": null,
   "EntityCEO": null,
   "Active": true
  },
  {
   "Title": "Alomotech Technology LLC",
   "EntityCode": "ALMO",
   "EntityType": "Subsidiary",
   "Country": "UAE",
   "EntityHead": null,
   "EntityCEO": null,
   "Active": true
  },
  {
   "Title": "Corporate Connection",
   "EntityCode": "CC",
   "EntityType": "Subsidiary",
   "Country": "UAE",
   "EntityHead": null,
   "EntityCEO": null,
   "Active": true
  },
  {
   "Title": "Xerox Emirates",
   "EntityCode": "XEJV",
   "EntityType": "Joint Venture",
   "Country": "UAE",
   "EntityHead": null,
   "EntityCEO": null,
   "Active": true
  },
  {
   "Title": "Homewide LLC",
   "EntityCode": "HW",
   "EntityType": "Subsidiary",
   "Country": "UAE",
   "EntityHead": null,
   "EntityCEO": null,
   "Active": true
  },
  {
   "Title": "Al Otaiba Ferretti",
   "EntityCode": "AOF",
   "EntityType": "Subsidiary",
   "Country": "UAE",
   "EntityHead": null,
   "EntityCEO": null,
   "Active": true
  },
  {
   "Title": "MAFS",
   "EntityCode": "MAFS",
   "EntityType": "Subsidiary",
   "Country": "UAE",
   "EntityHead": null,
   "EntityCEO": null,
   "Active": true
  },
  {
   "Title": "MHAO Real Estate",
   "EntityCode": "MHAOREI",
   "EntityType": "Subsidiary",
   "Country": "UAE",
   "EntityHead": null,
   "EntityCEO": null,
   "Active": true
  },
  {
   "Title": "MHAO Investment LLC",
   "EntityCode": "MHAOI",
   "EntityType": "Subsidiary",
   "Country": "UAE",
   "EntityHead": null,
   "EntityCEO": null,
   "Active": true
  },
  {
   "Title": "La Romana",
   "EntityCode": "LAR",
   "EntityType": "Subsidiary",
   "Country": "UAE",
   "EntityHead": null,
   "EntityCEO": null,
   "Active": true
  },
  {
   "Title": "Trucillo",
   "EntityCode": "TRU",
   "EntityType": "Subsidiary",
   "Country": "UAE",
   "EntityHead": null,
   "EntityCEO": null,
   "Active": true
  },
  {
   "Title": "Central Kitchen (CookHQ)",
   "EntityCode": "CHQ",
   "EntityType": "Subsidiary",
   "Country": "UAE",
   "EntityHead": null,
   "EntityCEO": null,
   "Active": true
  },
  {
   "Title": "Arabian Horeca",
   "EntityCode": "AHG",
   "EntityType": "Subsidiary",
   "Country": "UAE",
   "EntityHead": null,
   "EntityCEO": null,
   "Active": true
  },
  {
   "Title": "Al Jimi Organica",
   "EntityCode": "AJO",
   "EntityType": "Subsidiary",
   "Country": "UAE",
   "EntityHead": null,
   "EntityCEO": null,
   "Active": true
  }
 ],
 "departments": [
  {
   "Title": "Audit",
   "Entity": "MHAO Group",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Finance",
   "Entity": "MHAO Group",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Human Resources",
   "Entity": "MHAO Group",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Legal",
   "Entity": "MHAO Group",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Central Procurement",
   "Entity": "MHAO Group",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Quality & Operational Excellence",
   "Entity": "MHAO Group",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Service Excellence",
   "Entity": "MHAO Group",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Family Office",
   "Entity": "MHAO Group",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Brand Protection",
   "Entity": "MHAO Group",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "PRO",
   "Entity": "MHAO Group",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Administration",
   "Entity": "MHAO Group",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Government Affairs",
   "Entity": "MHAO Group",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Information Technology",
   "Entity": "MHAO Group",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Marketing",
   "Entity": "MHAO Group",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Chairman / MD Office",
   "Entity": "MHAO Group",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Rental Operations",
   "Entity": "AVIS UAE Rent A Car",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Fleet Operations",
   "Entity": "AVIS UAE Rent A Car",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Customer Experience",
   "Entity": "AVIS UAE Rent A Car",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Sales & Marketing",
   "Entity": "AVIS UAE Rent A Car",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Finance",
   "Entity": "AVIS UAE Rent A Car",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Human Resources",
   "Entity": "AVIS UAE Rent A Car",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Operations",
   "Entity": "AVIS Emirates for Luxury Transportation",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Fleet Operations",
   "Entity": "AVIS Emirates for Luxury Transportation",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Customer Experience",
   "Entity": "AVIS Emirates for Luxury Transportation",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Sales & Marketing",
   "Entity": "AVIS Emirates for Luxury Transportation",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Finance",
   "Entity": "AVIS Emirates for Luxury Transportation",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Human Resources",
   "Entity": "AVIS Emirates for Luxury Transportation",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Operations",
   "Entity": "Al Otaiba General Transport",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Fleet",
   "Entity": "Al Otaiba General Transport",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Sales",
   "Entity": "Al Otaiba General Transport",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "QHSE",
   "Entity": "Al Otaiba General Transport",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Finance",
   "Entity": "Al Otaiba General Transport",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Human Resources",
   "Entity": "Al Otaiba General Transport",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Operations",
   "Entity": "Bright Spark Auto Repairing",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Customer Experience",
   "Entity": "Bright Spark Auto Repairing",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Used Cars",
   "Entity": "Bright Spark Auto Repairing",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Finance",
   "Entity": "Bright Spark Auto Repairing",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Human Resources",
   "Entity": "Bright Spark Auto Repairing",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Operations",
   "Entity": "MHAO Mobility",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Sales",
   "Entity": "MHAO Mobility",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Finance",
   "Entity": "MHAO Mobility",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Human Resources",
   "Entity": "MHAO Mobility",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Software",
   "Entity": "Alomotech Technology LLC",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Application",
   "Entity": "Alomotech Technology LLC",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Data & Analytics",
   "Entity": "Alomotech Technology LLC",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Infrastructure",
   "Entity": "Alomotech Technology LLC",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "BA/QA",
   "Entity": "Alomotech Technology LLC",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "BD & Sales",
   "Entity": "Alomotech Technology LLC",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Finance",
   "Entity": "Alomotech Technology LLC",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Human Resources",
   "Entity": "Alomotech Technology LLC",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Administration",
   "Entity": "Alomotech Technology LLC",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Sales",
   "Entity": "Corporate Connection",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Service",
   "Entity": "Corporate Connection",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Solutions",
   "Entity": "Corporate Connection",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Digital Transformation",
   "Entity": "Corporate Connection",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Finance",
   "Entity": "Corporate Connection",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Human Resources",
   "Entity": "Corporate Connection",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Channel Sales",
   "Entity": "Homewide LLC",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Retail & E-commerce",
   "Entity": "Homewide LLC",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Projects & KD",
   "Entity": "Homewide LLC",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Marketing",
   "Entity": "Homewide LLC",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Logistics",
   "Entity": "Homewide LLC",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Service",
   "Entity": "Homewide LLC",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Finance",
   "Entity": "Homewide LLC",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Human Resources",
   "Entity": "Homewide LLC",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Business Development",
   "Entity": "Al Otaiba Ferretti",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Design & Estimation",
   "Entity": "Al Otaiba Ferretti",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Production",
   "Entity": "Al Otaiba Ferretti",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Operations",
   "Entity": "Al Otaiba Ferretti",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Finance",
   "Entity": "Al Otaiba Ferretti",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Human Resources",
   "Entity": "Al Otaiba Ferretti",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Operations",
   "Entity": "MAFS",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Civil Engineering",
   "Entity": "MAFS",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "MEP",
   "Entity": "MAFS",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Finance",
   "Entity": "MAFS",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Human Resources",
   "Entity": "MAFS",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Finance",
   "Entity": "MHAO Investment LLC",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Marketing & Events",
   "Entity": "MHAO Investment LLC",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Warehouse",
   "Entity": "MHAO Investment LLC",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "IT Support",
   "Entity": "MHAO Investment LLC",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Technical Services",
   "Entity": "MHAO Investment LLC",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Training & Quality",
   "Entity": "MHAO Investment LLC",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Human Resources",
   "Entity": "MHAO Investment LLC",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Operations",
   "Entity": "La Romana",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Training & Quality",
   "Entity": "La Romana",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "F&B Admin",
   "Entity": "La Romana",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Operations",
   "Entity": "Trucillo",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Operations",
   "Entity": "Central Kitchen (CookHQ)",
   "DepartmentHead": null,
   "Active": true
  },
  {
   "Title": "Production",
   "Entity": "Central Kitchen (CookHQ)",
   "DepartmentHead": null,
   "Active": true
  }
 ],
 "universe": [
  {
   "Title": "Central Procurement",
   "AuditAreaID": "AU-0001",
   "Entity": "MHAO Group",
   "Department": "Central Procurement",
   "ProcessCategory": "Procurement",
   "ProcessOwner": null,
   "RiskRating": "Medium",
   "RiskScore": null,
   "LastAuditDate": null,
   "AuditFrequency": "2 Years",
   "UniverseStatus": "Active"
  },
  {
   "Title": "Corporate Human Resources",
   "AuditAreaID": "AU-0002",
   "Entity": "MHAO Group",
   "Department": "Human Resources",
   "ProcessCategory": "HR & Payroll",
   "ProcessOwner": null,
   "RiskRating": "Medium",
   "RiskScore": null,
   "LastAuditDate": null,
   "AuditFrequency": "2 Years",
   "UniverseStatus": "Active"
  },
  {
   "Title": "Corporate Finance",
   "AuditAreaID": "AU-0003",
   "Entity": "MHAO Group",
   "Department": "Finance",
   "ProcessCategory": "Finance",
   "ProcessOwner": null,
   "RiskRating": "Medium",
   "RiskScore": null,
   "LastAuditDate": null,
   "AuditFrequency": "2 Years",
   "UniverseStatus": "Active"
  },
  {
   "Title": "Administration",
   "AuditAreaID": "AU-0004",
   "Entity": "MHAO Group",
   "Department": "Administration",
   "ProcessCategory": "Operations",
   "ProcessOwner": null,
   "RiskRating": "Medium",
   "RiskScore": null,
   "LastAuditDate": null,
   "AuditFrequency": "2 Years",
   "UniverseStatus": "Active"
  },
  {
   "Title": "Admin & Government Affairs",
   "AuditAreaID": "AU-0005",
   "Entity": "MHAO Group",
   "Department": "Government Affairs",
   "ProcessCategory": "Legal & Compliance",
   "ProcessOwner": null,
   "RiskRating": null,
   "RiskScore": null,
   "LastAuditDate": null,
   "AuditFrequency": null,
   "UniverseStatus": "Active"
  },
  {
   "Title": "IT Policies & Systems",
   "AuditAreaID": "AU-0006",
   "Entity": "MHAO Group",
   "Department": "Information Technology",
   "ProcessCategory": "IT",
   "ProcessOwner": null,
   "RiskRating": null,
   "RiskScore": null,
   "LastAuditDate": null,
   "AuditFrequency": null,
   "UniverseStatus": "Active"
  },
  {
   "Title": "Corporate Governance & Authority Matrix",
   "AuditAreaID": "AU-0007",
   "Entity": "MHAO Group",
   "Department": "Legal",
   "ProcessCategory": "Legal & Compliance",
   "ProcessOwner": null,
   "RiskRating": null,
   "RiskScore": null,
   "LastAuditDate": null,
   "AuditFrequency": null,
   "UniverseStatus": "Active"
  },
  {
   "Title": "Treasury, Funds Transfers & Bank Loans",
   "AuditAreaID": "AU-0008",
   "Entity": "MHAO Group",
   "Department": "Finance",
   "ProcessCategory": "Treasury",
   "ProcessOwner": null,
   "RiskRating": null,
   "RiskScore": null,
   "LastAuditDate": null,
   "AuditFrequency": null,
   "UniverseStatus": "Active"
  },
  {
   "Title": "Corporate Marketing",
   "AuditAreaID": "AU-0009",
   "Entity": "MHAO Group",
   "Department": "Marketing",
   "ProcessCategory": "Sales",
   "ProcessOwner": null,
   "RiskRating": null,
   "RiskScore": null,
   "LastAuditDate": null,
   "AuditFrequency": null,
   "UniverseStatus": "Active"
  },
  {
   "Title": "Leasing / Rental Operations",
   "AuditAreaID": "AU-0010",
   "Entity": "AVIS UAE Rent A Car",
   "Department": "Rental Operations",
   "ProcessCategory": "Operations",
   "ProcessOwner": null,
   "RiskRating": "Medium",
   "RiskScore": null,
   "LastAuditDate": null,
   "AuditFrequency": "2 Years",
   "UniverseStatus": "Active"
  },
  {
   "Title": "Back Office Operations",
   "AuditAreaID": "AU-0011",
   "Entity": "AVIS UAE Rent A Car",
   "Department": "Rental Operations",
   "ProcessCategory": "Operations",
   "ProcessOwner": null,
   "RiskRating": "Medium",
   "RiskScore": null,
   "LastAuditDate": null,
   "AuditFrequency": "2 Years",
   "UniverseStatus": "Active"
  },
  {
   "Title": "Online Bookings",
   "AuditAreaID": "AU-0012",
   "Entity": "AVIS UAE Rent A Car",
   "Department": "Customer Experience",
   "ProcessCategory": "Sales",
   "ProcessOwner": null,
   "RiskRating": "Medium",
   "RiskScore": null,
   "LastAuditDate": null,
   "AuditFrequency": "2 Years",
   "UniverseStatus": "Active"
  },
  {
   "Title": "Fleet Management",
   "AuditAreaID": "AU-0013",
   "Entity": "AVIS UAE Rent A Car",
   "Department": "Fleet Operations",
   "ProcessCategory": "Operations",
   "ProcessOwner": null,
   "RiskRating": "Medium",
   "RiskScore": null,
   "LastAuditDate": null,
   "AuditFrequency": "2 Years",
   "UniverseStatus": "Active"
  },
  {
   "Title": "De-fleeting Operations",
   "AuditAreaID": "AU-0014",
   "Entity": "AVIS UAE Rent A Car",
   "Department": "Fleet Operations",
   "ProcessCategory": "Operations",
   "ProcessOwner": null,
   "RiskRating": "Medium",
   "RiskScore": null,
   "LastAuditDate": null,
   "AuditFrequency": "2 Years",
   "UniverseStatus": "Active"
  },
  {
   "Title": "Customer Service Operations",
   "AuditAreaID": "AU-0015",
   "Entity": "AVIS UAE Rent A Car",
   "Department": "Customer Experience",
   "ProcessCategory": "Operations",
   "ProcessOwner": null,
   "RiskRating": "Medium",
   "RiskScore": null,
   "LastAuditDate": null,
   "AuditFrequency": "2 Years",
   "UniverseStatus": "Active"
  },
  {
   "Title": "Finance",
   "AuditAreaID": "AU-0016",
   "Entity": "AVIS UAE Rent A Car",
   "Department": "Finance",
   "ProcessCategory": "Finance",
   "ProcessOwner": null,
   "RiskRating": "Medium",
   "RiskScore": null,
   "LastAuditDate": null,
   "AuditFrequency": "2 Years",
   "UniverseStatus": "Active"
  },
  {
   "Title": "Business Development & Sales",
   "AuditAreaID": "AU-0017",
   "Entity": "Al Otaiba General Transport",
   "Department": "Sales",
   "ProcessCategory": "Sales",
   "ProcessOwner": null,
   "RiskRating": "Medium",
   "RiskScore": null,
   "LastAuditDate": null,
   "AuditFrequency": "2 Years",
   "UniverseStatus": "Active"
  },
  {
   "Title": "Fleet Management",
   "AuditAreaID": "AU-0018",
   "Entity": "Al Otaiba General Transport",
   "Department": "Fleet",
   "ProcessCategory": "Operations",
   "ProcessOwner": null,
   "RiskRating": "Medium",
   "RiskScore": null,
   "LastAuditDate": null,
   "AuditFrequency": "2 Years",
   "UniverseStatus": "Active"
  },
  {
   "Title": "De-fleeting Operations",
   "AuditAreaID": "AU-0019",
   "Entity": "Al Otaiba General Transport",
   "Department": "Fleet",
   "ProcessCategory": "Operations",
   "ProcessOwner": null,
   "RiskRating": "Medium",
   "RiskScore": null,
   "LastAuditDate": null,
   "AuditFrequency": "2 Years",
   "UniverseStatus": "Active"
  },
  {
   "Title": "Customer Service Operations",
   "AuditAreaID": "AU-0020",
   "Entity": "Al Otaiba General Transport",
   "Department": "Operations",
   "ProcessCategory": "Operations",
   "ProcessOwner": null,
   "RiskRating": "Medium",
   "RiskScore": null,
   "LastAuditDate": null,
   "AuditFrequency": "2 Years",
   "UniverseStatus": "Active"
  },
  {
   "Title": "Finance",
   "AuditAreaID": "AU-0021",
   "Entity": "Al Otaiba General Transport",
   "Department": "Finance",
   "ProcessCategory": "Finance",
   "ProcessOwner": null,
   "RiskRating": "Medium",
   "RiskScore": null,
   "LastAuditDate": null,
   "AuditFrequency": "2 Years",
   "UniverseStatus": "Active"
  },
  {
   "Title": "Business Development & Sales",
   "AuditAreaID": "AU-0022",
   "Entity": "Bright Spark Auto Repairing",
   "Department": null,
   "ProcessCategory": "Sales",
   "ProcessOwner": null,
   "RiskRating": "High",
   "RiskScore": null,
   "LastAuditDate": null,
   "AuditFrequency": "Annual",
   "UniverseStatus": "Active"
  },
  {
   "Title": "Service Operations",
   "AuditAreaID": "AU-0023",
   "Entity": "Bright Spark Auto Repairing",
   "Department": "Operations",
   "ProcessCategory": "Operations",
   "ProcessOwner": null,
   "RiskRating": "High",
   "RiskScore": null,
   "LastAuditDate": null,
   "AuditFrequency": "Annual",
   "UniverseStatus": "Active"
  },
  {
   "Title": "Inventory Management",
   "AuditAreaID": "AU-0024",
   "Entity": "Bright Spark Auto Repairing",
   "Department": "Operations",
   "ProcessCategory": "Operations",
   "ProcessOwner": null,
   "RiskRating": "High",
   "RiskScore": null,
   "LastAuditDate": null,
   "AuditFrequency": "Annual",
   "UniverseStatus": "Active"
  },
  {
   "Title": "Scrap & Procurement Operations",
   "AuditAreaID": "AU-0025",
   "Entity": "Bright Spark Auto Repairing",
   "Department": "Operations",
   "ProcessCategory": "Procurement",
   "ProcessOwner": null,
   "RiskRating": "High",
   "RiskScore": null,
   "LastAuditDate": null,
   "AuditFrequency": "Annual",
   "UniverseStatus": "Active"
  },
  {
   "Title": "Finance",
   "AuditAreaID": "AU-0026",
   "Entity": "Bright Spark Auto Repairing",
   "Department": "Finance",
   "ProcessCategory": "Finance",
   "ProcessOwner": null,
   "RiskRating": "High",
   "RiskScore": null,
   "LastAuditDate": null,
   "AuditFrequency": "Annual",
   "UniverseStatus": "Active"
  },
  {
   "Title": "Business Development & Sales",
   "AuditAreaID": "AU-0027",
   "Entity": "Homewide LLC",
   "Department": "Channel Sales",
   "ProcessCategory": "Sales",
   "ProcessOwner": null,
   "RiskRating": "High",
   "RiskScore": null,
   "LastAuditDate": null,
   "AuditFrequency": "Annual",
   "UniverseStatus": "Active"
  },
  {
   "Title": "Distribution Sales",
   "AuditAreaID": "AU-0028",
   "Entity": "Homewide LLC",
   "Department": "Channel Sales",
   "ProcessCategory": "Sales",
   "ProcessOwner": null,
   "RiskRating": "High",
   "RiskScore": null,
   "LastAuditDate": null,
   "AuditFrequency": "Annual",
   "UniverseStatus": "Active"
  },
  {
   "Title": "Service Operations",
   "AuditAreaID": "AU-0029",
   "Entity": "Homewide LLC",
   "Department": "Service",
   "ProcessCategory": "Operations",
   "ProcessOwner": null,
   "RiskRating": "High",
   "RiskScore": null,
   "LastAuditDate": null,
   "AuditFrequency": "Annual",
   "UniverseStatus": "Active"
  },
  {
   "Title": "Retail Stores Operations",
   "AuditAreaID": "AU-0030",
   "Entity": "Homewide LLC",
   "Department": "Retail & E-commerce",
   "ProcessCategory": "Operations",
   "ProcessOwner": null,
   "RiskRating": "High",
   "RiskScore": null,
   "LastAuditDate": null,
   "AuditFrequency": "Annual",
   "UniverseStatus": "Active"
  },
  {
   "Title": "Inventory Management",
   "AuditAreaID": "AU-0031",
   "Entity": "Homewide LLC",
   "Department": "Logistics",
   "ProcessCategory": "Operations",
   "ProcessOwner": null,
   "RiskRating": "High",
   "RiskScore": null,
   "LastAuditDate": null,
   "AuditFrequency": "Annual",
   "UniverseStatus": "Active"
  },
  {
   "Title": "Procurement & Warehouse Operations",
   "AuditAreaID": "AU-0032",
   "Entity": "Homewide LLC",
   "Department": "Logistics",
   "ProcessCategory": "Procurement",
   "ProcessOwner": null,
   "RiskRating": "High",
   "RiskScore": null,
   "LastAuditDate": null,
   "AuditFrequency": "Annual",
   "UniverseStatus": "Active"
  },
  {
   "Title": "Finance",
   "AuditAreaID": "AU-0033",
   "Entity": "Homewide LLC",
   "Department": "Finance",
   "ProcessCategory": "Finance",
   "ProcessOwner": null,
   "RiskRating": "High",
   "RiskScore": null,
   "LastAuditDate": null,
   "AuditFrequency": "Annual",
   "UniverseStatus": "Active"
  },
  {
   "Title": "Managed Print Services",
   "AuditAreaID": "AU-0034",
   "Entity": "Corporate Connection",
   "Department": "Service",
   "ProcessCategory": "Operations",
   "ProcessOwner": null,
   "RiskRating": "Medium",
   "RiskScore": null,
   "LastAuditDate": null,
   "AuditFrequency": "2 Years",
   "UniverseStatus": "Active"
  },
  {
   "Title": "Software Services",
   "AuditAreaID": "AU-0035",
   "Entity": "Corporate Connection",
   "Department": "Solutions",
   "ProcessCategory": "Operations",
   "ProcessOwner": null,
   "RiskRating": "Medium",
   "RiskScore": null,
   "LastAuditDate": null,
   "AuditFrequency": "2 Years",
   "UniverseStatus": "Active"
  },
  {
   "Title": "Inventory Management",
   "AuditAreaID": "AU-0036",
   "Entity": "Corporate Connection",
   "Department": "Service",
   "ProcessCategory": "Operations",
   "ProcessOwner": null,
   "RiskRating": "Medium",
   "RiskScore": null,
   "LastAuditDate": null,
   "AuditFrequency": "2 Years",
   "UniverseStatus": "Active"
  },
  {
   "Title": "Finance",
   "AuditAreaID": "AU-0037",
   "Entity": "Corporate Connection",
   "Department": "Finance",
   "ProcessCategory": "Finance",
   "ProcessOwner": null,
   "RiskRating": "Medium",
   "RiskScore": null,
   "LastAuditDate": null,
   "AuditFrequency": "2 Years",
   "UniverseStatus": "Active"
  },
  {
   "Title": "Business Development & Sales",
   "AuditAreaID": "AU-0038",
   "Entity": "Arabian Horeca",
   "Department": null,
   "ProcessCategory": "Sales",
   "ProcessOwner": null,
   "RiskRating": "High",
   "RiskScore": null,
   "LastAuditDate": null,
   "AuditFrequency": "Annual",
   "UniverseStatus": "Active"
  },
  {
   "Title": "Retail Stores Operations",
   "AuditAreaID": "AU-0039",
   "Entity": "Arabian Horeca",
   "Department": null,
   "ProcessCategory": "Operations",
   "ProcessOwner": null,
   "RiskRating": "High",
   "RiskScore": null,
   "LastAuditDate": null,
   "AuditFrequency": "Annual",
   "UniverseStatus": "Active"
  },
  {
   "Title": "Back Office Operations",
   "AuditAreaID": "AU-0040",
   "Entity": "Arabian Horeca",
   "Department": null,
   "ProcessCategory": "Operations",
   "ProcessOwner": null,
   "RiskRating": "High",
   "RiskScore": null,
   "LastAuditDate": null,
   "AuditFrequency": "Annual",
   "UniverseStatus": "Active"
  },
  {
   "Title": "Inventory Management",
   "AuditAreaID": "AU-0041",
   "Entity": "Arabian Horeca",
   "Department": null,
   "ProcessCategory": "Operations",
   "ProcessOwner": null,
   "RiskRating": "High",
   "RiskScore": null,
   "LastAuditDate": null,
   "AuditFrequency": "Annual",
   "UniverseStatus": "Active"
  },
  {
   "Title": "Finance",
   "AuditAreaID": "AU-0042",
   "Entity": "Arabian Horeca",
   "Department": null,
   "ProcessCategory": "Finance",
   "ProcessOwner": null,
   "RiskRating": "High",
   "RiskScore": null,
   "LastAuditDate": null,
   "AuditFrequency": "Annual",
   "UniverseStatus": "Active"
  },
  {
   "Title": "Technology Services",
   "AuditAreaID": "AU-0043",
   "Entity": "Xerox Emirates",
   "Department": null,
   "ProcessCategory": "Operations",
   "ProcessOwner": null,
   "RiskRating": "High",
   "RiskScore": null,
   "LastAuditDate": null,
   "AuditFrequency": "Annual",
   "UniverseStatus": "Active"
  },
  {
   "Title": "Digital Services",
   "AuditAreaID": "AU-0044",
   "Entity": "Xerox Emirates",
   "Department": null,
   "ProcessCategory": "Operations",
   "ProcessOwner": null,
   "RiskRating": "High",
   "RiskScore": null,
   "LastAuditDate": null,
   "AuditFrequency": "Annual",
   "UniverseStatus": "Active"
  },
  {
   "Title": "Inventory Management",
   "AuditAreaID": "AU-0045",
   "Entity": "Xerox Emirates",
   "Department": null,
   "ProcessCategory": "Operations",
   "ProcessOwner": null,
   "RiskRating": "High",
   "RiskScore": null,
   "LastAuditDate": null,
   "AuditFrequency": "Annual",
   "UniverseStatus": "Active"
  },
  {
   "Title": "Finance",
   "AuditAreaID": "AU-0046",
   "Entity": "Xerox Emirates",
   "Department": null,
   "ProcessCategory": "Finance",
   "ProcessOwner": null,
   "RiskRating": "High",
   "RiskScore": null,
   "LastAuditDate": null,
   "AuditFrequency": "Annual",
   "UniverseStatus": "Active"
  },
  {
   "Title": "Business Development & Sales",
   "AuditAreaID": "AU-0047",
   "Entity": "Al Otaiba Ferretti",
   "Department": "Business Development",
   "ProcessCategory": "Sales",
   "ProcessOwner": null,
   "RiskRating": "Medium",
   "RiskScore": null,
   "LastAuditDate": null,
   "AuditFrequency": "2 Years",
   "UniverseStatus": "Active"
  },
  {
   "Title": "Operations",
   "AuditAreaID": "AU-0048",
   "Entity": "Al Otaiba Ferretti",
   "Department": "Operations",
   "ProcessCategory": "Operations",
   "ProcessOwner": null,
   "RiskRating": "Medium",
   "RiskScore": null,
   "LastAuditDate": null,
   "AuditFrequency": "2 Years",
   "UniverseStatus": "Active"
  },
  {
   "Title": "Finance",
   "AuditAreaID": "AU-0049",
   "Entity": "Al Otaiba Ferretti",
   "Department": "Finance",
   "ProcessCategory": "Finance",
   "ProcessOwner": null,
   "RiskRating": "Medium",
   "RiskScore": null,
   "LastAuditDate": null,
   "AuditFrequency": "2 Years",
   "UniverseStatus": "Active"
  },
  {
   "Title": "Business Development & Sales",
   "AuditAreaID": "AU-0050",
   "Entity": "Alomotech Technology LLC",
   "Department": "BD & Sales",
   "ProcessCategory": "Sales",
   "ProcessOwner": null,
   "RiskRating": "Low",
   "RiskScore": null,
   "LastAuditDate": null,
   "AuditFrequency": "3 Years",
   "UniverseStatus": "Active"
  },
  {
   "Title": "Operations",
   "AuditAreaID": "AU-0051",
   "Entity": "Alomotech Technology LLC",
   "Department": "Software",
   "ProcessCategory": "Operations",
   "ProcessOwner": null,
   "RiskRating": "Low",
   "RiskScore": null,
   "LastAuditDate": null,
   "AuditFrequency": "3 Years",
   "UniverseStatus": "Active"
  },
  {
   "Title": "Finance",
   "AuditAreaID": "AU-0052",
   "Entity": "Alomotech Technology LLC",
   "Department": "Finance",
   "ProcessCategory": "Finance",
   "ProcessOwner": null,
   "RiskRating": "Low",
   "RiskScore": null,
   "LastAuditDate": null,
   "AuditFrequency": "3 Years",
   "UniverseStatus": "Active"
  }
 ],
 "config": {
  "ReminderDays1": "30",
  "ReminderDays2": "15",
  "EscalateCEOAfterDays": "30"
 }
}
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

import json,uuid,zipfile,os,shutil
SITE="https://YOURTENANT.sharepoint.com/sites/InternalAuditTest"
L={"Findings":"fae117a9-0d20-4b8c-a7d0-f2097e547552","Tracker":"8a4ff1fe-8df1-4c5f-bf2f-02ae8546c833","FollowUps":"d3bc1182-aa55-48b7-98b3-ab3565c17fba","Trail":"a3558d0b-1af4-408b-8d69-85ad37c92e24","Config":"1c72ad0d-74e7-4cb5-81c2-6134625a98a8","Engagements":"04ab1436-1f78-4eba-b458-58741cb1d83a","Universe":"f4c91b22-7bf2-4d4e-adb4-e6def6889ee8","Risk":"e14549ff-0650-4901-acbc-4176606166f5","Plan":"a1d8a9b6-d145-47c4-bcd0-d9cebc06f4b9"}
SP="shared_sharepointonline";OL="shared_office365"
AP="shared_approvals"
CR={SP:"new_sharedsharepointonline_iams",OL:"new_sharedoffice365_iams",AP:"new_sharedapprovals_iams"}
def spi(op,params,trigger=False):
    d={"host":{"connectionName":SP,"operationId":op,"apiId":"/providers/Microsoft.PowerApps/apis/"+SP},"parameters":params,"authentication":"@parameters('$authentication')"}
    return d
def sp_action(op,params,after=None):
    return {"runAfter":after or {},"type":"OpenApiConnection","inputs":spi(op,params)}
def mail(to,subj,body,after=None):
    return {"runAfter":after or {},"type":"OpenApiConnection","inputs":{"host":{"connectionName":OL,"operationId":"SendEmailV2","apiId":"/providers/Microsoft.PowerApps/apis/"+OL},"parameters":{"emailMessage/To":to,"emailMessage/Subject":subj,"emailMessage/Body":body,"emailMessage/Importance":"Normal"},"authentication":"@parameters('$authentication')"}}
def trigger(op,table,minutes=1):
    return {"type":"OpenApiConnectionNotification" if False else "OpenApiConnection","recurrence":{"frequency":"Minute","interval":minutes},"inputs":spi(op,{"dataset":SITE,"table":L[table]}),"splitOn":"@triggerOutputs()?['body/value']","metadata":{}}
def flow_json(triggers,actions,uses):
    refs={k:{"runtimeSource":"embedded","connection":{"connectionReferenceLogicalName":CR[k]},"api":{"name":k}} for k in uses}
    return {"properties":{"connectionReferences":refs,"definition":{"$schema":"https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#","contentVersion":"1.0.0.0","parameters":{"$connections":{"defaultValue":{},"type":"Object"},"$authentication":{"defaultValue":{},"type":"SecureObject"}},"triggers":triggers,"actions":actions},"templateName":""},"schemaVersion":"1.0.0.0"}
def build(solname,flows,out):
    """flows: list of (name,flowjson,uses)"""
    d="/tmp/pk_"+solname;shutil.rmtree(d,ignore_errors=True);os.makedirs(d+"/Workflows")
    roots="";wfx="";files=[]
    for name,fj,uses in flows:
        fid=str(uuid.uuid5(uuid.NAMESPACE_DNS,"mhao-iams-"+name))
        fn=f"Workflows/{name}-{fid.upper()}.json";open(d+"/"+fn,"w").write(json.dumps(fj));files.append(fn)
        roots+=f'<RootComponent type="29" id="{{{fid}}}" behavior="0"/>'
        wfx+=f'<Workflow WorkflowId="{{{fid}}}" Name="{name}"><JsonFileName>/{fn}</JsonFileName><Type>1</Type><Subprocess>0</Subprocess><Category>5</Category><Mode>0</Mode><Scope>4</Scope><OnDemand>0</OnDemand><TriggerOnCreate>0</TriggerOnCreate><TriggerOnDelete>0</TriggerOnDelete><AsyncAutodelete>0</AsyncAutodelete><SyncWorkflowLogOnFailure>0</SyncWorkflowLogOnFailure><StateCode>0</StateCode><StatusCode>1</StatusCode><RunAs>1</RunAs><IsTransacted>1</IsTransacted><IntroducedVersion>1.0</IntroducedVersion><IsCustomizable>1</IsCustomizable><BusinessProcessType>0</BusinessProcessType><IsCustomProcessingStepAllowedForOtherPublishers>1</IsCustomProcessingStepAllowedForOtherPublishers><PrimaryEntity>none</PrimaryEntity><LocalizedNames><LocalizedName languagecode="1033" description="{name}"/></LocalizedNames></Workflow>'
    crx="".join(f'<connectionreference connectionreferencelogicalname="{v}"><connectionreferencedisplayname>{k.replace("shared_","")} IAMS</connectionreferencedisplayname><connectorid>/providers/Microsoft.PowerApps/apis/{k}</connectorid><iscustomizable>1</iscustomizable><statecode>0</statecode><statuscode>1</statuscode></connectionreference>' for k,v in CR.items())
    open(d+"/[Content_Types].xml","w").write('<?xml version="1.0" encoding="utf-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="xml" ContentType="application/octet-stream"/><Default Extension="json" ContentType="application/octet-stream"/></Types>')
    open(d+"/solution.xml","w").write(f'<?xml version="1.0" encoding="utf-8"?><ImportExportXml version="9.2.0.0" SolutionPackageVersion="9.2" languagecode="1033" generatedBy="CrmLive" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><SolutionManifest><UniqueName>{solname}</UniqueName><LocalizedNames><LocalizedName description="{solname}" languagecode="1033"/></LocalizedNames><Descriptions/><Version>1.0.0.0</Version><Managed>0</Managed><Publisher><UniqueName>mhaoiams</UniqueName><LocalizedNames><LocalizedName description="MHAO IAMS" languagecode="1033"/></LocalizedNames><Descriptions/><EMailAddress xsi:nil="true"/><SupportingWebsiteUrl xsi:nil="true"/><CustomizationPrefix>iams</CustomizationPrefix><CustomizationOptionValuePrefix>10000</CustomizationOptionValuePrefix><Addresses><Address><AddressNumber>1</AddressNumber><AddressTypeCode>1</AddressTypeCode></Address></Addresses></Publisher><RootComponents>{roots}</RootComponents><MissingDependencies/></SolutionManifest></ImportExportXml>')
    open(d+"/customizations.xml","w").write(f'<?xml version="1.0" encoding="utf-8"?><ImportExportXml xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><Entities></Entities><Roles></Roles><Workflows>{wfx}</Workflows><FieldSecurityProfiles></FieldSecurityProfiles><Templates/><EntityMaps/><EntityRelationships/><OrganizationSettings/><optionsets/><CustomControls/><EntityDataProviders/><connectionreferences>{crx}</connectionreferences><Languages><Language>1033</Language></Languages></ImportExportXml>')
    z=zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED)
    for f in ["[Content_Types].xml","solution.xml","customizations.xml"]+files: z.write(d+"/"+f,f)
    z.close()

def approval(title,to,details,after=None):
    return {"runAfter":after or {},"type":"OpenApiConnectionWebhook","inputs":{"host":{"connectionName":AP,"operationId":"StartAndWaitForAnApproval","apiId":"/providers/Microsoft.PowerApps/apis/"+AP},"parameters":{"approvalType":"Basic","WebhookApprovalCreationInput/title":title,"WebhookApprovalCreationInput/assignedTo":to,"WebhookApprovalCreationInput/details":details,"WebhookApprovalCreationInput/enableNotifications":True,"WebhookApprovalCreationInput/enableReassignment":True},"authentication":"@parameters('$authentication')"}}
def merge(listexpr,idexpr,body,after=None):
    return sp_action("HttpRequest",{"dataset":SITE,"parameters/method":"POST","parameters/uri":"_api/web/lists(guid'%s')/items(@{%s})"%(listexpr,idexpr),"parameters/headers":{"Accept":"application/json;odata=nometadata","Content-Type":"application/json;odata=nometadata","X-HTTP-Method":"MERGE","IF-MATCH":"*"},"parameters/body":body},after)
def powerapp_trigger(titles,files=()):
    props={};req=[]
    for i,t in enumerate(titles):
        k="text" if i==0 else "text_%d"%i
        props[k]={"title":t,"type":"string","x-ms-dynamically-added":True,"description":"Please enter "+t,"x-ms-content-hint":"TEXT"};req.append(k)
    for t in files:
        props["file"]={"title":t,"type":"object","x-ms-dynamically-added":True,"description":"Please select file or image","x-ms-content-hint":"FILE","properties":{"name":{"type":"string"},"contentBytes":{"type":"string","format":"byte"}}};req.append("file")
    return {"manual":{"type":"Request","kind":"PowerApp","inputs":{"schema":{"type":"object","properties":props,"required":req}}}}
def respond(props,after=None):
    return {"runAfter":after or {},"type":"Response","kind":"PowerApp","inputs":{"statusCode":200,"body":props,"schema":{"type":"object","properties":{k:{"title":k,"x-ms-dynamically-added":True,"type":"string"} for k in props}}}}

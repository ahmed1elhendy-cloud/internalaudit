from iams_pkg import *
import json
EV="e876c3be-01dc-4bfe-af30-2e1048dc57db";EN="04ab1436-1f78-4eba-b458-58741cb1d83a"
Q="decodeUriComponent('%27')"
ENG="triggerBody()?['text']";ETY="triggerBody()?['text_1']";FN="triggerBody()?['text_2']";AID="triggerBody()?['text_3']";UE="triggerBody()?['text_4']"
H={"Accept":"application/json;odata=nometadata"}
HM={"Accept":"application/json;odata=nometadata","Content-Type":"application/json;odata=nometadata","X-HTTP-Method":"MERGE","IF-MATCH":"*"}
def get(uri,after=None): return sp_action("HttpRequest",{"dataset":SITE,"parameters/method":"GET","parameters/uri":uri,"parameters/headers":H},after)
def mrg(guid,idexpr,body,after=None): return sp_action("HttpRequest",{"dataset":SITE,"parameters/method":"POST","parameters/uri":"@concat('_api/web/lists(guid',%s,'%s',%s,')/items(',%s,')')"%(Q,guid,Q,idexpr),"parameters/headers":HM,"parameters/body":body},after)
S=lambda n:{n:["Succeeded"]}
PATH="concat('/sites/InternalAuditTest/IA_Evidence/',%s,'/',outputs('SubFolder'),'/',outputs('SafeName'))"%ENG
FILEID="body('Get_file_item')?['Id']"
act_ok={
 "SubFolder":{"runAfter":{},"type":"Compose","inputs":"@if(equals(%s,'Walkthrough'),'Walkthroughs',if(equals(%s,'Sample'),'Samples',if(equals(%s,'Validation'),'Management Evidence',if(equals(%s,'Planning'),'Planning',%s))))"%((ETY,)*5)},
 "SafeName":{"runAfter":S("SubFolder"),"type":"Compose","inputs":"@concat(formatDateTime(utcNow(),'yyyyMMdd-HHmmss'),'_',replace(replace(replace(replace(%s,'#','_'),'%%','_'),'&','_'),' ','_'))"%FN},
 "Create_file":sp_action("CreateFile",{"dataset":SITE,"folderPath":"@concat('/IA_Evidence/',%s,'/',outputs('SubFolder'))"%ENG,"name":"@outputs('SafeName')","body":"@base64ToBinary(triggerBody()?['file']?['contentBytes'])"},S("SafeName")),
 "Get_file_item":get("@concat('_api/web/GetFileByServerRelativeUrl(',%s,%s,%s,')/ListItemAllFields?$select=Id,EncodedAbsUrl')"%(Q,PATH,Q),S("Create_file")),
 "Get_engagement":get("@concat('_api/web/lists(guid',%s,'%s',%s,')/items?$filter=EngagementID eq ',%s,%s,%s,'&$top=1&$select=Id')"%(Q,EN,Q,Q,ENG,Q),S("Get_file_item")),
 "Set_file_properties":mrg(EV,FILEID,"@concat('{\"Title\":\"',replace(%s,'\"',''),'\",\"EvidenceType\":\"',%s,'\"',if(empty(body('Get_engagement')?['value']),'',concat(',\"EngagementId\":',first(body('Get_engagement')?['value'])?['Id'])),'}')"%(FN,ETY),S("Get_engagement")),
 "If_has_email":{"runAfter":S("Set_file_properties"),"type":"If","expression":{"not":{"equals":["@empty(%s)"%UE,True]}},"actions":{
   "Ensure_user":sp_action("HttpRequest",{"dataset":SITE,"parameters/method":"POST","parameters/uri":"_api/web/ensureuser","parameters/headers":{"Accept":"application/json;odata=nometadata","Content-Type":"application/json;odata=nometadata"},"parameters/body":"@concat('{\"logonName\":\"i:0#.f|membership|',%s,'\"}')"%UE}),
   "Set_uploader":mrg(EV,FILEID,"@concat('{\"UploadedByUserId\":',body('Ensure_user')?['Id'],'}')",S("Ensure_user"))},"else":{"actions":{}}},
 "If_action_linked":{"runAfter":S("If_has_email"),"type":"If","expression":{"greater":["@int(coalesce(%s,'0'))"%AID,0]},"actions":{
   "Get_action":get("@concat('_api/web/lists(guid',%s,'8a4ff1fe-8df1-4c5f-bf2f-02ae8546c833',%s,')/items(',%s,')?$select=Id,FindingId')"%(Q,Q,AID)),
   "Link_file_to_action":mrg(EV,FILEID,"@concat('{\"ActionId\":',%s,if(equals(coalesce(body('Get_action')?['FindingId'],0),0),'',concat(',\"FindingId\":',body('Get_action')?['FindingId'])),'}')"%AID,S("Get_action")),
   "Flag_action_evidence":mrg("8a4ff1fe-8df1-4c5f-bf2f-02ae8546c833","int(%s)"%AID,'{"EvidenceUploaded":true}',S("Link_file_to_action"))},"else":{"actions":{}}},
 "Audit_upload":sp_action("PostItem",{"dataset":SITE,"table":L["Trail"],"item/Title":"@concat('Evidence uploaded: ',outputs('SafeName'))","item/SourceList":"Evidence Repository","item/SourceItemId":"@int(%s)"%FILEID,"item/EventType/Value":"Created","item/EventDetails":"@concat('Engagement ',%s,' | ',%s,' | by ',coalesce(%s,'n/a'))"%(ENG,ETY,UE)},S("If_action_linked")),
 "Respond_ok":respond({"result":"Uploaded","url":"@{body('Get_file_item')?['EncodedAbsUrl']}"},S("Audit_upload"))}
exts="'pdf','docx','doc','xlsx','xls','pptx','jpg','jpeg','png','msg','csv','zip','txt'"
act9={"Check_extension":{"runAfter":{},"type":"If","expression":{"equals":["@contains(createArray(%s),toLower(last(split(%s,'.'))))"%(exts,FN),True]},"actions":act_ok,
  "else":{"actions":{"Respond_bad_type":respond({"result":"Error: file type not allowed. Allowed: pdf, docx, xlsx, pptx, jpg, png, msg, csv, zip, txt.","url":""})}}}}
wf9=("IAMS-WF9-UploadEvidence",flow_json(powerapp_trigger(["EngagementID","EvidenceType","FileName","ActionId","UploaderEmail"],["FileContent"]),act9,[SP]),[SP])
build("IAMSBatch3",[wf9],"/home/claude/IAMS_Batch3_Solution.zip")
print('ok')

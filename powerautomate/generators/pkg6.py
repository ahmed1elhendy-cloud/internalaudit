from iams_pkg import *
import json
EX="shared_excelonlinebusiness"
CR[EX]="new_sharedexcelonlinebusiness_iams"
L.update({"Quest":"83755970-a247-4158-8596-828a1c018b0d","Sect":"bca5e5be-5d61-4c41-ae8f-ed723c5fa24f","QItems":"00ee8d40-e110-4d67-a66c-a85f698db566","Upl":"d99397af-ccc6-43a7-96f5-869dab1350bc"})
Q="decodeUriComponent('%27')"
H={"Accept":"application/json;odata=nometadata"}
HM={"Accept":"application/json;odata=nometadata","Content-Type":"application/json;odata=nometadata","X-HTTP-Method":"MERGE","IF-MATCH":"*"}
HP={"Accept":"application/json;odata=nometadata","Content-Type":"application/json;odata=nometadata"}
S=lambda n:{n:["Succeeded"]}
T="triggerOutputs()?['body/"
UID=T+"ID']"
DRIVE="b!ZyhvBs7i2USynWqrxnEF-30z8_RaXtFKvjDreHG1LGKjJuz55_coTKXtzxcksj_I"
def post(key,body,after=None): return sp_action("HttpRequest",{"dataset":SITE,"parameters/method":"POST","parameters/uri":"@concat('_api/web/lists(guid',%s,'%s',%s,')/items')"%(Q,L[key],Q),"parameters/headers":HP,"parameters/body":body},after)
def mrg(key,idexpr,body,after=None): return sp_action("HttpRequest",{"dataset":SITE,"parameters/method":"POST","parameters/uri":"@concat('_api/web/lists(guid',%s,'%s',%s,')/items(',%s,')')"%(Q,L[key],Q,idexpr),"parameters/headers":HM,"parameters/body":body},after)
def get(uri,after=None): return sp_action("HttpRequest",{"dataset":SITE,"parameters/method":"GET","parameters/uri":uri,"parameters/headers":H},after)
FN="outputs('FileName')"
rows="body('List_question_rows')?['value']"
core={
 "Get_attachments":get("@concat('_api/web/lists(guid',%s,'%s',%s,')/items(',%s,')/AttachmentFiles?$select=FileName,ServerRelativeUrl')"%(Q,L["Upl"],Q,UID),S("Set_validating")),
 "FileName":{"runAfter":S("Get_attachments"),"type":"Compose","inputs":"@concat('QU-',%s,'-',first(body('Get_attachments')?['value'])?['FileName'])"%UID},
 "Get_attachment_content":sp_action("GetFileContentByPath",{"dataset":SITE,"path":"@replace(first(body('Get_attachments')?['value'])?['ServerRelativeUrl'],'/sites/InternalAuditTest','')","inferContentType":True},S("FileName")),
 "Save_file":sp_action("CreateFile",{"dataset":SITE,"folderPath":"/IA_QnrFiles","name":"@outputs('FileName')","body":"@body('Get_attachment_content')"},S("Get_attachment_content")),
 "List_question_rows":{"runAfter":S("Save_file"),"type":"OpenApiConnection","inputs":{"host":{"connectionName":EX,"operationId":"GetItems","apiId":"/providers/Microsoft.PowerApps/apis/"+EX},"parameters":{"source":SITE,"drive":DRIVE,"file":"@concat('/',outputs('FileName'))","table":"tblQuestions"},"authentication":"@parameters('$authentication')"}},
 "Question_rows":{"runAfter":S("List_question_rows"),"type":"Query","inputs":{"from":"@"+rows,"where":"@and(not(empty(item()?['Section No'])),not(empty(item()?['Audit Question'])))"}},
 "Check_has_rows":{"runAfter":S("Question_rows"),"type":"If","expression":{"greater":["@length(body('Question_rows'))",0]},"actions":{
   "Create_questionnaire":post("Quest","@json(concat('{\"Title\":\"',replace(%sTitle'],'\"',''),'\",\"EngagementId\":',%sEngagement/Id'],',\"QuestionnaireStatus\":\"Draft\",\"Round\":1,\"QuestionCount\":',length(body('Question_rows')),'}'))"%(T,T)),
   "Section_list":{"runAfter":S("Create_questionnaire"),"type":"Select","inputs":{"from":"@body('Question_rows')","select":{"no":"@int(item()?['Section No'])","title":"@item()?['Section Title']"}}},
   "Distinct_sections":{"runAfter":S("Section_list"),"type":"Compose","inputs":"@union(body('Section_list'),body('Section_list'))"},
   "Each_section":{"runAfter":S("Distinct_sections"),"type":"Foreach","foreach":"@outputs('Distinct_sections')","actions":{
      "Section_rows":{"runAfter":{},"type":"Query","inputs":{"from":"@body('Question_rows')","where":"@equals(int(item()?['Section No']),items('Each_section')?['no'])"}},
      "Create_section":post("Sect","@json(concat('{\"Title\":\"',replace(coalesce(items('Each_section')?['title'],'Section'),'\"',''),'\",\"QuestionnaireId\":',body('Create_questionnaire')?['Id'],',\"SectionNo\":',items('Each_section')?['no'],',\"SectionStatus\":\"Not started\",\"QuestionCount\":',length(body('Section_rows')),'}'))",S("Section_rows")),
      "Reset_counter":{"runAfter":S("Create_section"),"type":"SetVariable","inputs":{"name":"seq","value":0}},
      "Each_question":{"runAfter":S("Reset_counter"),"type":"Foreach","foreach":"@body('Section_rows')","runtimeConfiguration":{"concurrency":{"repetitions":1}},"actions":{
         "Bump_counter":{"runAfter":{},"type":"IncrementVariable","inputs":{"name":"seq","value":1}},
         "Create_item":post("QItems","@json(concat('{\"Title\":\"',replace(string(coalesce(items('Each_question')?['Ref'],concat(items('Each_section')?['no'],'.',variables('seq')))),'\"',''),'\",\"QuestionnaireId\":',body('Create_questionnaire')?['Id'],',\"SectionId\":',body('Create_section')?['Id'],',\"SortOrder\":',variables('seq'),',\"Question\":\"',replace(replace(string(items('Each_question')?['Audit Question']),'\"',''),decodeUriComponent('%0A'),' '),'\",\"AttachmentRequirement\":\"',replace(replace(coalesce(string(items('Each_question')?['Attachment Requirement']),''),'\"',''),decodeUriComponent('%0A'),' '),'\",\"EvidenceRule\":\"',if(contains(createArray('If Yes','If No','Always','Never'),string(items('Each_question')?['Evidence Rule'])),string(items('Each_question')?['Evidence Rule']),'Never'),'\",\"ExplanationRequiredIfNo\":',if(equals(toLower(string(coalesce(items('Each_question')?['Explanation Required if No'],'no'))),'yes'),'true','false'),',\"IsException\":',if(equals(toLower(string(coalesce(items('Each_question')?['Exception Question'],'no'))),'yes'),'true','false'),',\"ReviewStatus\":\"Pending\"}'))",S("Bump_counter"))}}}},
   "Mark_draft_created":mrg("Upl",UID,"@concat('{\"UploadStatus\":\"Draft Created\",\"QuestionnaireId\":',body('Create_questionnaire')?['Id'],',\"ValidationMessage\":\"Imported ',length(outputs('Distinct_sections')),' sections, ',length(body('Question_rows')),' questions.\"}')",S("Each_section"))},
   "else":{"actions":{"Mark_empty":mrg("Upl",UID,'{"UploadStatus":"Rejected","ValidationMessage":"No question rows found in table tblQuestions (needs Section No and Audit Question)."}')}}}}
acts={
 "Set_validating":sp_action("HttpRequest",{"dataset":SITE,"parameters/method":"POST","parameters/uri":"@concat('_api/web/lists(guid',%s,'%s',%s,')/items(',%s,')')"%(Q,L["Upl"],Q,UID),"parameters/headers":HM,"parameters/body":'{"UploadStatus":"Validating"}'}),
 "Import_scope":{"runAfter":S("Set_validating"),"type":"Scope","actions":core},
 "Handle_failure":mrg("Upl",UID,"@concat('{\"UploadStatus\":\"Rejected\",\"ValidationMessage\":\"Import failed: ',replace(replace(coalesce(string(result('Import_scope')),'error'),'\"',''),decodeUriComponent('%0A'),' ')[0:240],'\"}')" if False else '{"UploadStatus":"Rejected","ValidationMessage":"Import failed - check the file is the MHAO template with table tblQuestions, then upload again."}',{"Import_scope":["Failed","TimedOut"]})}
# core's first action runs after Set_validating in the outer scope; inside scope make it start fresh
core["Get_attachments"]["runAfter"]={}
trig={"When_a_questionnaire_upload_is_created":trigger("GetOnUpdatedItems","Upl")}
act={"Seq":{"runAfter":{},"type":"InitializeVariable","inputs":{"variables":[{"name":"seq","type":"integer","value":0}]}},
 "If_new_upload":{"runAfter":S("Seq"),"type":"If","expression":{"equals":["@%sUploadStatus/Value']"%T,"Uploaded"]},"actions":acts,"else":{"actions":{}}}}
wf=("IAMS-WF2d-QuestionnaireUploadImport",flow_json(trig,act,[SP,EX]),[SP,EX])
build("IAMSBatch6",[wf],"/home/claude/IAMS_Batch6_Solution.zip")
print('ok')

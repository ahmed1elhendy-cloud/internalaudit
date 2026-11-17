from iams_pkg import *
import json
L.update({"QItems":"00ee8d40-e110-4d67-a66c-a85f698db566","Quest":"83755970-a247-4158-8596-828a1c018b0d"})
Q="decodeUriComponent('%27')"
H={"Accept":"application/json;odata=nometadata"}
HM={"Accept":"application/json;odata=nometadata","Content-Type":"application/json;odata=nometadata","X-HTTP-Method":"MERGE","IF-MATCH":"*"}
HP={"Accept":"application/json;odata=nometadata","Content-Type":"application/json;odata=nometadata"}
S=lambda n:{n:["Succeeded"]}
T="triggerOutputs()?['body/"
def get(uri,after=None): return sp_action("HttpRequest",{"dataset":SITE,"parameters/method":"GET","parameters/uri":uri,"parameters/headers":H},after)
def lid(key): return "@concat('_api/web/lists(guid',%s,'%s',%s,')/items"%(Q,L[key],Q)
# ---- WF2c: accepted exception -> draft finding ----
cond={"and":[{"equals":["@%sIsException']"%T,True]},{"equals":["@%sReviewStatus/Value']"%T,"Accepted"]},{"equals":["@empty(%sFindingRaised/Id'])"%T,True]}]}
acts={
 "Get_questionnaire":get("@concat('_api/web/lists(guid',%s,'%s',%s,')/items(',%sQuestionnaire/Id'],')?$select=Id,EngagementId,QuestionnaireID')"%(Q,L["Quest"],Q,T)),
 "Finding_body":{"runAfter":S("Get_questionnaire"),"type":"Compose","inputs":{
    "Title":"@concat('Questionnaire exception ',%sTitle'],': ',substring(coalesce(%sQuestion'],'(no text)'),0,min(length(coalesce(%sQuestion'],'(no text)')),150)))"%(T,T,T),
    "EngagementId":"@body('Get_questionnaire')?['EngagementId']",
    "Observation":"@concat('Raised from questionnaire ',body('Get_questionnaire')?['QuestionnaireID'],' question ',%sTitle'],'.',decodeUriComponent('%%0A'),'Question: ',coalesce(%sQuestion'],''),decodeUriComponent('%%0A'),'Answer: ',coalesce(%sAnswer/Value'],''),decodeUriComponent('%%0A'),'Auditee explanation: ',coalesce(%sExplanation'],''),decodeUriComponent('%%0A'),'Reviewer comment: ',coalesce(%sReviewerComment'],''))"%(T,T,T,T,T),
    "Rating":"Medium","WorkflowStage":"Draft","AgreementStatus":"Pending"}},
 "Create_draft_finding":sp_action("HttpRequest",{"dataset":SITE,"parameters/method":"POST","parameters/uri":lid("Findings")+"')","parameters/headers":HP,"parameters/body":"@outputs('Finding_body')"},S("Finding_body")),
 "Link_finding":sp_action("HttpRequest",{"dataset":SITE,"parameters/method":"POST","parameters/uri":"@concat('_api/web/lists(guid',%s,'%s',%s,')/items(',%sID'],')')"%(Q,L["QItems"],Q,T),"parameters/headers":HM,"parameters/body":"@concat('{\"FindingRaisedId\":',body('Create_draft_finding')?['Id'],'}')"},S("Create_draft_finding")),
 "Audit_finding_raised":sp_action("PostItem",{"dataset":SITE,"table":L["Trail"],"item/Title":"@concat('Draft finding raised from questionnaire item ',%sTitle'])"%T,"item/SourceList":"Questionnaire Items","item/SourceItemId":"@int(%sID'])"%T,"item/EventType/Value":"Created","item/EventDetails":"@concat('Finding item ',body('Create_draft_finding')?['Id'],' created as Draft (rating Medium, to be set by auditor)')"},S("Link_finding")),
 "Mail_finding":{"runAfter":S("Audit_finding_raised"),"type":"OpenApiConnection","inputs":{"host":{"connectionName":OL,"operationId":"SendEmailV2","apiId":"/providers/Microsoft.PowerApps/apis/"+OL},"parameters":{"emailMessage/To":"user@example.com","emailMessage/Subject":"@concat('Draft finding created from questionnaire item ',%sTitle'])"%T,"emailMessage/Body":"@concat('<p>An accepted exception on question <b>',%sTitle'],'</b> created draft finding #',body('Create_draft_finding')?['Id'],'. Please review the rating and wording.</p>')"%T,"emailMessage/Importance":"Normal"},"authentication":"@parameters('$authentication')"}}}
trig={"When_a_questionnaire_item_is_created_or_modified":trigger("GetOnUpdatedItems","QItems")}
act={"If_accepted_exception":{"runAfter":{},"type":"If","expression":cond,"actions":acts,"else":{"actions":{}}}}
wf=("IAMS-WF2c-ExceptionToFinding",flow_json(trig,act,[SP,OL]),[SP,OL])
build("IAMSBatch5",[wf],"/home/claude/IAMS_Batch5_Solution.zip")
print('ok')

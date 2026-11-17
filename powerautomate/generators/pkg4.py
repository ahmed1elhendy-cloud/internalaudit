from iams_pkg import *
import json
L.update({"Quest":"83755970-a247-4158-8596-828a1c018b0d","Sect":"bca5e5be-5d61-4c41-ae8f-ed723c5fa24f","QItems":"00ee8d40-e110-4d67-a66c-a85f698db566"})
Q="decodeUriComponent('%27')"
H={"Accept":"application/json;odata=nometadata"}
HM={"Accept":"application/json;odata=nometadata","Content-Type":"application/json;odata=nometadata","X-HTTP-Method":"MERGE","IF-MATCH":"*"}
ME="user@example.com"   # test mode: all notices go to Ahmed
S=lambda n:{n:["Succeeded"]}
def get(uri,after=None): return sp_action("HttpRequest",{"dataset":SITE,"parameters/method":"GET","parameters/uri":uri,"parameters/headers":H},after)
def mrg(key,idexpr,body,after=None): return sp_action("HttpRequest",{"dataset":SITE,"parameters/method":"POST","parameters/uri":"@concat('_api/web/lists(guid',%s,'%s',%s,')/items(',%s,')')"%(Q,L[key],Q,idexpr),"parameters/headers":HM,"parameters/body":body},after)
import re
def lst(key,query):
    parts=re.split(r"@\{(.*?)\}(?=[&]|$)",query)
    q="'"+parts[0]+"'"
    for i in range(1,len(parts),2): q+=","+parts[i]+",'"+parts[i+1]+"'"
    return "@concat('_api/web/lists(guid',%s,'%s',%s,')/items?',%s)"%(Q,L[key],Q,q)
def audit(title,src,idexpr,ev,det,after):
    return sp_action("PostItem",{"dataset":SITE,"table":L["Trail"],"item/Title":title,"item/SourceList":src,"item/SourceItemId":"@int(%s)"%idexpr,"item/EventType/Value":ev,"item/EventDetails":det},after)
T="triggerOutputs()?['body/"
# ---------- WF2a: Questionnaire issued / closed ----------
QID=T+"ID']";QST=T+"QuestionnaireStatus/Value']"
issue_actions={
 "Stamp_issued":mrg("Quest","@"+QID.replace("@","") if False else QID,'@concat(\'{"IssuedDate":"\',utcNow(),\'"}\')'),
 "Get_sections_issue":get(lst("Sect","$filter=QuestionnaireId eq @{%s}&$select=Id,Title,SectionNo,DueDate,Assignee/Title&$expand=Assignee&$orderby=SectionNo"%QID),S("Stamp_issued")),
 "Each_section":{"runAfter":S("Get_sections_issue"),"type":"Foreach","foreach":"@body('Get_sections_issue')?['value']","actions":{
    "Mail_section":mail(ME,"@concat('Questionnaire issued: ',triggerOutputs()?['body/Title'],' - section ',items('Each_section')?['Title'])","@concat('<p>Questionnaire <b>',outputs('QstCode'),'</b> has been issued.</p><p>Section: <b>',items('Each_section')?['Title'],'</b><br>Assignee: ',coalesce(items('Each_section')?['Assignee']?['Title'],'(not assigned)'),'<br>Due: ',coalesce(items('Each_section')?['DueDate'],'(not set)'),'</p>')")}},
 "Audit_issued":audit("@concat('Questionnaire issued: ',outputs('QstCode'))","Audit Questionnaires","@"+QID if False else QID,"Stage Change","@concat('Issued round ',coalesce(%s,1))"%(T+"Round']"),S("Each_section"))}
closed_actions={
 "Get_existing_closure":get(lst("Trail","$filter=SourceItemId eq @{%s} and EventType eq %sClosure%s and SourceList eq %sAudit Questionnaires%s&$select=Id"%(QID,"'","'","'","'")) if False else "@concat('_api/web/lists(guid',%s,'%s',%s,')/items?$filter=SourceItemId eq ',%s,' and EventType eq ',%s,'Closure',%s,' and SourceList eq ',%s,'Audit Questionnaires',%s,'&$select=Id')"%(Q,L["Trail"],Q,QID,Q,Q,Q,Q)),
 "If_not_logged":{"runAfter":S("Get_existing_closure"),"type":"If","expression":{"equals":["@length(body('Get_existing_closure')?['value'])",0]},"actions":{
   "Audit_closed":audit("@concat('Questionnaire closed: ',%s)"%(T+"QuestionnaireID']"),"Audit Questionnaires",QID,"Closure","Questionnaire closed",{}),
   "Mail_closed":mail(ME,"@concat('Questionnaire closed: ',triggerOutputs()?['body/QuestionnaireID'])","@concat('<p>Questionnaire <b>',triggerOutputs()?['body/Title'],'</b> was closed.</p>')",S("Audit_closed"))},"else":{"actions":{}}}}
trig_q={"When_a_questionnaire_is_created_or_modified":trigger("GetOnUpdatedItems","Quest")}
QCODE="coalesce(%s,concat('QST-',formatDateTime(utcNow(),'yyyy'),'-',substring(concat('0000',string(%s)),sub(length(concat('0000',string(%s))),4),4)))"%(T+"QuestionnaireID']",QID,QID)
act_q={"QstCode":{"runAfter":{},"type":"Compose","inputs":"@"+QCODE},
 "If_no_code":{"runAfter":S("QstCode"),"type":"If","expression":{"equals":["@empty(%s)"%(T+"QuestionnaireID']"),True]},"actions":{"Set_code":mrg("Quest",QID,"@concat('{\"QuestionnaireID\":\"',outputs('QstCode'),'\"}')")},"else":{"actions":{}}},
 "Route_by_status":{"runAfter":{"If_no_code":["Succeeded"]},"type":"Switch","expression":"@%s"%QST,"cases":{
  "Issued":{"case":"Issued","actions":{"If_not_yet_stamped":{"runAfter":{},"type":"If","expression":{"equals":["@empty(%s)"%(T+"IssuedDate']"),True]},"actions":issue_actions,"else":{"actions":{}}}}},
  "Closed":{"case":"Closed","actions":closed_actions}},"default":{"actions":{}}}}
wfq1=("IAMS-WF2a-QuestionnaireIssueClose",flow_json(trig_q,act_q,[SP,OL]),[SP,OL])

# ---------- WF2b: Section submitted / returned / accepted -> validate + recompute questionnaire status ----------
SID=T+"ID']";SST=T+"SectionStatus/Value']";SQ=T+"Questionnaire/Id']"
# validation of a newly submitted section
BADF="@filter(body('Get_section_items')?['value'], or(empty(item()?['Answer']), and(equals(item()?['Answer'],'No'), equals(item()?['ExplanationRequiredIfNo'],true), empty(item()?['Explanation']))))"
submit_actions={
 "Get_section_items":get(lst("QItems","$filter=SectionId eq @{%s}&$top=500&$select=Id,Title,Answer,Explanation,ExplanationRequiredIfNo,ReviewStatus"%SID)),
 "Find_incomplete":{"runAfter":S("Get_section_items"),"type":"Query","inputs":{"from":"@body('Get_section_items')?['value']","where":"@or(empty(item()?['Answer']), and(equals(item()?['Answer'],'No'), equals(item()?['ExplanationRequiredIfNo'],true), empty(item()?['Explanation'])))"}},
 "If_complete":{"runAfter":S("Find_incomplete"),"type":"If","expression":{"equals":["@length(body('Find_incomplete'))",0]},
  "actions":{
   "Stamp_submitted":mrg("Sect",SID,'@concat(\'{"SubmittedDate":"\',utcNow(),\'"}\')'),
   "Each_returned_item":{"runAfter":S("Stamp_submitted"),"type":"Foreach","foreach":"@body('Get_section_items')?['value']","actions":{
      "If_item_was_returned":{"runAfter":{},"type":"If","expression":{"equals":["@items('Each_returned_item')?['ReviewStatus']","Returned"]},"actions":{"Reset_item_review":mrg("QItems","items('Each_returned_item')?['Id']",'{"ReviewStatus":"Pending"}')},"else":{"actions":{}}}}},
   "Mail_submitted":mail(ME,"@concat('Section submitted for review: ',%sTitle'])"%T,"@concat('<p>Section <b>',%sTitle'],'</b> has been submitted and is ready for review.</p>')"%T,S("Each_returned_item")),
   "Audit_submitted":audit("@concat('Section submitted: ',%sTitle'])"%T,"Questionnaire Sections",SID,"Stage Change","Section submitted for review",S("Mail_submitted"))},
  "else":{"actions":{
   "Reopen_section":mrg("Sect",SID,'{"SectionStatus":"In progress"}'),
   "Mail_incomplete":mail(ME,"@concat('Section returned to draft (incomplete): ',%sTitle'])"%T,"@concat('<p>Section <b>',%sTitle'],'</b> was not submitted: ',string(length(body('Find_incomplete'))),' question(s) are unanswered or missing a required explanation.</p>')"%T,S("Reopen_section"))}}}}
return_actions={
 "Clear_submitted_date":mrg("Sect",SID,'{"SubmittedDate":null}'),
 "Mail_returned":mail(ME,"@concat('Section returned for correction: ',%sTitle'])"%T,"@concat('<p>Section <b>',%sTitle'],'</b> was returned by the reviewer. Please correct the flagged answers and resubmit.</p>')"%T,S("Clear_submitted_date")),
 "Audit_returned":audit("@concat('Section returned: ',%sTitle'])"%T,"Questionnaire Sections",SID,"Rejection","Section returned by reviewer",S("Mail_returned"))}
recompute={
 "Get_all_sections":get(lst("Sect","$filter=QuestionnaireId eq @{%s}&$select=Id,SectionStatus"%SQ)),
 "Get_questionnaire":get("@concat('_api/web/lists(guid',%s,'%s',%s,')/items(',%s,')?$select=Id,QuestionnaireStatus')"%(Q,L["Quest"],Q,SQ),S("Get_all_sections")),
 "Count_returned":{"runAfter":S("Get_questionnaire"),"type":"Query","inputs":{"from":"@body('Get_all_sections')?['value']","where":"@equals(item()?['SectionStatus'],'Returned')"}},
 "Count_accepted":{"runAfter":S("Count_returned"),"type":"Query","inputs":{"from":"@body('Get_all_sections')?['value']","where":"@equals(item()?['SectionStatus'],'Accepted')"}},
 "Count_open":{"runAfter":S("Count_accepted"),"type":"Query","inputs":{"from":"@body('Get_all_sections')?['value']","where":"@or(equals(item()?['SectionStatus'],'Submitted'),equals(item()?['SectionStatus'],'Accepted'))"}},
 "Count_started":{"runAfter":S("Count_open"),"type":"Query","inputs":{"from":"@body('Get_all_sections')?['value']","where":"@not(equals(item()?['SectionStatus'],'Not started'))"}},
 "NewStatus":{"runAfter":S("Count_started"),"type":"Compose","inputs":"@if(greater(length(body('Count_returned')),0),'Returned',if(equals(length(body('Count_accepted')),length(body('Get_all_sections')?['value'])),'Accepted',if(equals(length(body('Count_open')),length(body('Get_all_sections')?['value'])),'Under Review',if(greater(length(body('Count_started')),0),'In Progress',body('Get_questionnaire')?['QuestionnaireStatus']))))"},
 "If_status_changes":{"runAfter":S("NewStatus"),"type":"If","expression":{"and":[{"not":{"equals":["@outputs('NewStatus')","@body('Get_questionnaire')?['QuestionnaireStatus']"]}},{"not":{"equals":["@body('Get_questionnaire')?['QuestionnaireStatus']","Closed"]}},{"not":{"equals":["@body('Get_questionnaire')?['QuestionnaireStatus']","Draft"]}}]},"actions":{
   "Update_questionnaire_status":mrg("Quest",SQ,'@concat(\'{"QuestionnaireStatus":"\',outputs(\'NewStatus\'),\'"}\')'),
   "Audit_status":audit("@concat('Questionnaire status: ',body('Get_questionnaire')?['QuestionnaireStatus'],' -> ',outputs('NewStatus'))","Audit Questionnaires",SQ,"Stage Change","@concat('Status changed to ',outputs('NewStatus'))",S("Update_questionnaire_status")),
   "Mail_status":mail(ME,"@concat('Questionnaire status: ',outputs('NewStatus'))","@concat('<p>Questionnaire #',%s,' is now <b>',outputs('NewStatus'),'</b>.</p>')"%SQ,S("Audit_status"))},"else":{"actions":{}}}}
trig_s={"When_a_section_is_created_or_modified":trigger("GetOnUpdatedItems","Sect")}
act_s={
 "Route_section":{"runAfter":{},"type":"Switch","expression":"@%s"%SST,"cases":{
   "Submitted":{"case":"Submitted","actions":{"If_not_yet_submitted":{"runAfter":{},"type":"If","expression":{"equals":["@empty(%s)"%(T+"SubmittedDate']"),True]},"actions":submit_actions,"else":{"actions":{}}}}},
   "Returned":{"case":"Returned","actions":return_actions}},"default":{"actions":{}}},
 "Recompute":{"runAfter":{"Route_section":["Succeeded","Failed","Skipped"]},"type":"Scope","actions":recompute}}
wfq2=("IAMS-WF2b-SectionWorkflow",flow_json(trig_s,act_s,[SP,OL]),[SP,OL])
build("IAMSBatch4",[wfq1,wfq2],"/home/claude/IAMS_Batch4_Solution.zip")
print('ok')

from iams_pkg import *
import json
# ---------- WF7 Universe refresh ----------
RISKPART=r'''@if(empty(body('Get_active_risks')?['value']),'',concat(',"RiskScore":',outputs('Score'),',"RiskRating":"',outputs('Rating'),'"'))'''
NEXTPART=r'''@if(or(empty(items('For_each_area')?['LastAuditDate']),empty(items('For_each_area')?['AuditFrequency/Value'])),'',concat(',"NextAuditDate":"',addToTime(items('For_each_area')?['LastAuditDate'],outputs('Months'),'Month'),'"'))'''
UPDBODY=r'''{"UniverseStatus":"Active"@{outputs('Risk_part')}@{outputs('Next_part')}}'''

Q="decodeUriComponent('%27')"
trig={"Recurrence":{"type":"Recurrence","recurrence":{"frequency":"Month","interval":1,"startTime":"2026-12-01T02:00:00Z","timeZone":"UTC"}}}
foreach_actions={
 "Get_active_risks":sp_action("GetItems",{"dataset":SITE,"table":L["Risk"],"$filter":"@concat('AuditArea/Id eq ',items('For_each_area')?['ID'],' and RiskStatus ne ',%s,'Closed',%s)"%(Q,Q),"$top":500}),
 "Select_scores":{"runAfter":{"Get_active_risks":["Succeeded"]},"type":"Select","inputs":{"from":"@body('Get_active_risks')?['value']","select":"@float(item()?['InherentRisk'])"}},
 "Score":{"runAfter":{"Select_scores":["Succeeded"]},"type":"Compose","inputs":"@if(empty(body('Select_scores')),0,max(body('Select_scores')))"},
 "Rating":{"runAfter":{"Score":["Succeeded"]},"type":"Compose","inputs":"@if(greaterOrEquals(outputs('Score'),15),'Critical',if(greaterOrEquals(outputs('Score'),10),'High',if(greaterOrEquals(outputs('Score'),5),'Medium','Low')))"},
 "Risk_part":{"runAfter":{"Rating":["Succeeded"]},"type":"Compose","inputs":RISKPART},
 "Months":{"runAfter":{"Risk_part":["Succeeded"]},"type":"Compose","inputs":"@if(equals(items('For_each_area')?['AuditFrequency/Value'],'Annual'),12,if(equals(items('For_each_area')?['AuditFrequency/Value'],'18 Months'),18,if(equals(items('For_each_area')?['AuditFrequency/Value'],'2 Years'),24,36)))"},
 "Next_part":{"runAfter":{"Months":["Succeeded"]},"type":"Compose","inputs":NEXTPART},
 "Update_area":merge(L["Universe"],"items('For_each_area')?['ID']",UPDBODY,{"Next_part":["Succeeded"]}),
}
act={
 "Get_active_areas":sp_action("GetItems",{"dataset":SITE,"table":L["Universe"],"$filter":"@concat('UniverseStatus eq ',%s,'Active',%s)"%(Q,Q),"$top":5000}),
 "For_each_area":{"runAfter":{"Get_active_areas":["Succeeded"]},"type":"Foreach","foreach":"@body('Get_active_areas')?['value']","actions":foreach_actions,"runtimeConfiguration":{"concurrency":{"repetitions":1}}},
 "Email_summary":mail("user@example.com","IAMS: audit universe refreshed","<p>Monthly audit universe refresh completed. Areas processed: <b>@{length(body('Get_active_areas')?['value'])}</b>. Risk scores, ratings and next audit dates have been recalculated.</p>",{"For_each_area":["Succeeded"]})}
wf7=("IAMS-WF7-UniverseRefresh",flow_json(trig,act,[SP,OL]),[SP,OL])

# ---------- WF6 Due-date extension ----------
T="triggerBody()?['text']"
IT="triggerBody()?['text']";ID="triggerBody()?['text_1']";ND="triggerBody()?['text_2']";RS="triggerBody()?['text_3']";RQ="triggerBody()?['text_4']"
LIST="if(equals(%s,'Finding'),'%s','%s')"%(IT,L["Findings"],L["Tracker"])
cur_uri="@concat('_api/web/lists(guid',%s,'%s',%s,')/items(',%s,')?$select=Id,Title,DueDate,OriginalDueDate,ExtensionCount,Rating,FindingRating')"%(Q,"",Q,ID)
cur_uri="@concat('_api/web/lists(guid',%s,%s,%s,')/items(',%s,')?$select=Id,Title,DueDate,OriginalDueDate,ExtensionCount')"%(Q,LIST,Q,ID)
Cur="body('Get_current')"
APPBODY=r'''@concat('{"DueDate":"',outputs('NewDue'),'","ExtensionCount":',add(coalesce(body('Get_current')?['ExtensionCount'],0),1),',"OriginalDueDate":"',coalesce(body('Get_current')?['OriginalDueDate'],body('Get_current')?['DueDate']),'"',if(equals(triggerBody()?['text'],'Action'),',"ReminderStage":"None"',''),'}')'''
rating_expr="coalesce(outputs('Rating'),'Low')"
approved_body=APPBODY
def mk_apply(sfx):
  d={
 "Apply_new_due_date":{"runAfter":{},"type":"OpenApiConnection","inputs":{"host":{"connectionName":SP,"operationId":"HttpRequest","apiId":"/providers/Microsoft.PowerApps/apis/"+SP},"parameters":{"dataset":SITE,"parameters/method":"POST","parameters/uri":"@concat('_api/web/lists(guid',%s,%s,%s,')/items(',%s,')')"%(Q,LIST,Q,ID),"parameters/headers":{"Accept":"application/json;odata=nometadata","Content-Type":"application/json;odata=nometadata","X-HTTP-Method":"MERGE","IF-MATCH":"*"},"parameters/body":approved_body},"authentication":"@parameters('$authentication')"}},
 "Audit_approved":sp_action("PostItem",{"dataset":SITE,"table":L["Trail"],"item/Title":"@concat('Due date extended: ',%s?['Title'])"%Cur,"item/SourceList":"@if(equals(%s,'Finding'),'Audit Findings Register','Corrective Action Tracker')"%IT,"item/SourceItemId":"@int(%s)"%ID,"item/EventType/Value":"Due Date Extension","item/EventDetails":"@concat('Old: ',%s?['DueDate'],' New: ',outputs('NewDue'),' Reason: ',%s,' Requested by: ',%s)"%(Cur,RS,RQ)},{"Apply_new_due_date":["Succeeded"]}),
 "Tell_requester":mail("@%s"%RQ,"Due-date extension approved","<p>Your extension request for <b>@{%s?['Title']}</b> was approved. New due date: @{outputs('NewDue')}.</p>"%Cur,{"Audit_approved":["Succeeded"]})}
  r={}
  for k,v in d.items():
    v=json.loads(json.dumps(v).replace('"Apply_new_due_date"','"Apply_new_due_date'+sfx+'"').replace('"Audit_approved"','"Audit_approved'+sfx+'"').replace('"Tell_requester"','"Tell_requester'+sfx+'"'))
    r[k+sfx]=v
  return r
def mk_rej(sfx):
  d={
 "Tell_requester_rejected":mail("@%s"%RQ,"Due-date extension rejected","<p>Your extension request for <b>@{%s?['Title']}</b> was rejected.</p>"%Cur)}
  return json.loads(json.dumps(d).replace('Tell_requester_rejected','Tell_requester_rejected'+sfx))
valid_actions={
 "Respond_submitted":respond({"result":"Submitted for approval. You will be notified by email of the outcome."}),
 "Approval_1_Audit_Manager":dict(approval("@concat('Due-date extension: ',%s?['Title'])"%Cur,"user@example.com","@concat('New due date ',outputs('NewDue'),'. Reason: ',%s)"%RS),runAfter={"Respond_submitted":["Succeeded"]}),
 "If_approved_1":{"runAfter":{"Approval_1_Audit_Manager":["Succeeded"]},"type":"If","expression":{"equals":["@outputs('Approval_1_Audit_Manager')?['body/outcome']","Approve"]},
   "actions":{
     "Get_rating":sp_action("HttpRequest",{"dataset":SITE,"parameters/method":"GET","parameters/uri":"@concat('_api/web/lists(guid',%s,%s,%s,')/items(',%s,')?$select=',if(equals(%s,'Finding'),'Rating','FindingRating'))"%(Q,LIST,Q,ID,IT),"parameters/headers":{"Accept":"application/json;odata=nometadata"}}),
     "Rating":{"runAfter":{"Get_rating":["Succeeded"]},"type":"Compose","inputs":"@coalesce(body('Get_rating')?['Rating'],body('Get_rating')?['FindingRating'],'Low')"},
     "If_high_rating":{"runAfter":{"Rating":["Succeeded"]},"type":"If","expression":{"or":[{"equals":["@outputs('Rating')","Critical"]},{"equals":["@outputs('Rating')","High"]}]},
       "actions":{"Approval_2_Head_of_IA":approval("@concat('2nd approval, due-date extension: ',%s?['Title'])"%Cur,"user@example.com","@concat('High/Critical item. New due date ',outputs('NewDue'),'. Reason: ',%s)"%RS),
          "If_approved_2":{"runAfter":{"Approval_2_Head_of_IA":["Succeeded"]},"type":"If","expression":{"equals":["@outputs('Approval_2_Head_of_IA')?['body/outcome']","Approve"]},"actions":mk_apply("_hi"),"else":{"actions":mk_rej("_hi")}}},
       "else":{"actions":mk_apply("_lo")}}},
   "else":{"actions":mk_rej("_1")}}}
act6={
 "Get_current":sp_action("HttpRequest",{"dataset":SITE,"parameters/method":"GET","parameters/uri":cur_uri,"parameters/headers":{"Accept":"application/json;odata=nometadata"}}),
 "NewDue":{"runAfter":{"Get_current":["Succeeded"]},"type":"Compose","inputs":"@concat(%s,'T08:00:00Z')"%ND},
 "Validate_new_date":{"runAfter":{"NewDue":["Succeeded"]},"type":"If","expression":{"greater":["@ticks(outputs('NewDue'))","@ticks(%s?['DueDate'])"%Cur]},"actions":valid_actions,
   "else":{"actions":{"Respond_invalid":respond({"result":"Error: the new due date must be later than the current due date."})}}}}
wf6=("IAMS-WF6-DueDateExtension",flow_json(powerapp_trigger(["ItemType","ItemId","NewDueDate","Reason","RequesterEmail"]),act6,[SP,OL,AP]),[SP,OL,AP])
build("IAMSBatch2",[wf7,wf6],"/home/claude/IAMS_Batch2_Solution.zip")
print('ok')

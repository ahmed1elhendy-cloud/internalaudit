from iams_pkg import *
import json as _j
def merge(listkey,idexpr,body,after=None):
    return sp_action("HttpRequest",{"dataset":SITE,"parameters/method":"POST","parameters/uri":"_api/web/lists(guid'%s')/items(@{%s})"%(L[listkey],idexpr),"parameters/headers":{"Accept":"application/json;odata=nometadata","Content-Type":"application/json;odata=nometadata","X-HTTP-Method":"MERGE","IF-MATCH":"*"},"parameters/body":body},after)

T="triggerOutputs()?['body/"
ID=T+"ID']"
# WF5c: action closure effects
trig={"When_an_action_is_created_or_modified":trigger("GetOnUpdatedItems","Tracker")}
cond={"and":[{"equals":["@triggerOutputs()?['body/ActionStatus/Value']","Closed"]},{"equals":["@triggerOutputs()?['body/ValidationStatus/Value']","Validated"]},{"equals":["@empty(triggerOutputs()?['body/CompletedDate'])",True]}]}
inner={
 "Stamp_CompletedDate":merge("Tracker","triggerOutputs()?['body/ID']",'{"CompletedDate":"@{utcNow()}"}'),
 "Get_other_open_actions":sp_action("GetItems",{"dataset":SITE,"table":L["Tracker"],"$filter":"@concat('Finding/Id eq ',triggerOutputs()?['body/Finding/Id'],' and ActionStatus ne ',decodeUriComponent('%27'),'Closed',decodeUriComponent('%27'))","$top":100},{"Stamp_CompletedDate":["Succeeded"]}),
 "If_no_other_open_actions":{"runAfter":{"Get_other_open_actions":["Succeeded"]},"type":"If","expression":{"equals":["@length(body('Get_other_open_actions')?['value'])",0]},
   "actions":{"Close_finding":merge("Findings","triggerOutputs()?['body/Finding/Id']",'{"FindingStatus":"Closed","WorkflowStage":"Closed","ClosedDate":"@{utcNow()}","LastProcessedStage":"Closed"}')},"else":{"actions":{}}},
 "Write_audit_log":sp_action("PostItem",{"dataset":SITE,"table":L["Trail"],"item/Title":"@concat('Action closed: ',triggerOutputs()?['body/Title'])","item/SourceList":"Corrective Action Tracker","item/SourceItemId":"@triggerOutputs()?['body/ID']","item/EventType/Value":"Closure","item/EventDetails":"@concat('Action validated and closed. Open actions remaining on finding: ',length(body('Get_other_open_actions')?['value']))"},{"If_no_other_open_actions":["Succeeded"]}),
 "Email_action_owner":mail("@coalesce(triggerOutputs()?['body/ActionOwner/Email'],'user@example.com')","@concat('Action closed: ',triggerOutputs()?['body/Title'])","<p>Your corrective action <b>@{triggerOutputs()?['body/Title']}</b> has been validated by Internal Audit and is now closed. Thank you.</p><p>MHAO Group Internal Audit</p>",{"Write_audit_log":["Succeeded"]})}
act={"Check_closed_and_validated":{"runAfter":{},"type":"If","expression":cond,"actions":inner,"else":{"actions":{}}}}
wf5c=("IAMS-WF5c-ActionClosureEffects",flow_json(trig,act,[SP,OL]),[SP,OL])
# WF5d: review outcome (not implemented / partial)
trig2={"When_a_review_is_created_or_modified":trigger("GetOnUpdatedItems","FollowUps")}
O="@triggerOutputs()?['body/Outcome/Value']"
cond2={"or":[{"equals":[O,"Not Implemented"]},{"equals":[O,"Re-opened"]}]}
reopen={
 "Reopen_finding":merge("Findings","triggerOutputs()?['body/Finding/Id']",'{"FindingStatus":"Re-opened","WorkflowStage":"Issued","LastProcessedStage":"Issued"}'),
 "Audit_reopen":sp_action("PostItem",{"dataset":SITE,"table":L["Trail"],"item/Title":"@concat('Finding re-opened after follow-up: ',triggerOutputs()?['body/Title'])","item/SourceList":"Follow-Up Reviews","item/SourceItemId":"@triggerOutputs()?['body/ID']","item/EventType/Value":"Re-open","item/EventDetails":"@concat('Outcome: ',triggerOutputs()?['body/Outcome/Value'],'. ',coalesce(triggerOutputs()?['body/TestingNotes'],''))"},{"Reopen_finding":["Succeeded"]}),
 "Notify_dept_head":mail("user@example.com","Finding re-opened after follow-up review","<p>A follow-up review concluded <b>@{triggerOutputs()?['body/Outcome/Value']}</b>. The related finding has been re-opened.</p><p>Notes: @{triggerOutputs()?['body/TestingNotes']}</p><p>(Test mode: sent to Head of IA. At go-live this goes to the Department Head.)</p>",{"Audit_reopen":["Succeeded"]})}
partial={
 "Get_action":sp_action("GetItem",{"dataset":SITE,"table":L["Tracker"],"id":"@triggerOutputs()?['body/Action/Id']"}),
 "Email_owner_partial":mail("@coalesce(outputs('Get_action')?['body/ActionOwner/Email'],'user@example.com')","Corrective action only partially implemented","<p>Follow-up testing found your action <b>@{outputs('Get_action')?['body/Title']}</b> only partially implemented. Please complete the outstanding work and resubmit.</p><p>Auditor notes: @{triggerOutputs()?['body/TestingNotes']}</p>",{"Get_action":["Succeeded"]})}
act2={"Outcome_branch":{"runAfter":{},"type":"If","expression":cond2,"actions":reopen,"else":{"actions":{"If_partial":{"runAfter":{},"type":"If","expression":{"equals":[O,"Partially Implemented"]},"actions":partial,"else":{"actions":{}}}}}}}
wf5d=("IAMS-WF5d-ReviewOutcomeNotices",flow_json(trig2,act2,[SP,OL]),[SP,OL])
build("IAMSBatch1",[wf5c,wf5d],"/home/claude/IAMS_Batch1_Solution.zip")
print("ok")

from iams_pkg import *
import json
L.update({"Quest":"83755970-a247-4158-8596-828a1c018b0d","Evid":"e876c3be-01dc-4bfe-af30-2e1048dc57db"})
Q="decodeUriComponent('%27')"
H={"Accept":"application/json;odata=nometadata"}
HM={"Accept":"application/json;odata=nometadata","Content-Type":"application/json;odata=nometadata","X-HTTP-Method":"MERGE","IF-MATCH":"*"}
HP={"Accept":"application/json;odata=nometadata","Content-Type":"application/json;odata=nometadata"}
S=lambda n:{n:["Succeeded"]}
ME="user@example.com"
T="triggerOutputs()?['body/"
def get(uri,after=None): return sp_action("HttpRequest",{"dataset":SITE,"parameters/method":"GET","parameters/uri":uri,"parameters/headers":H},after)
def mrg(key,idexpr,body,after=None): return sp_action("HttpRequest",{"dataset":SITE,"parameters/method":"POST","parameters/uri":"@concat('_api/web/lists(guid',%s,'%s',%s,')/items(',%s,')')"%(Q,L[key],Q,idexpr),"parameters/headers":HM,"parameters/body":body},after)
def lurl(key,rest): return "@concat('_api/web/lists(guid',%s,'%s',%s,')/items?%s')"%(Q,L[key],Q,rest)
def audit(title,src,idexpr,ev,det,after=None):
    return sp_action("PostItem",{"dataset":SITE,"table":L["Trail"],"item/Title":title,"item/SourceList":src,"item/SourceItemId":"@int(%s)"%idexpr,"item/EventType/Value":ev,"item/EventDetails":det},after)
# ================= WF5 v2: follow-up review =================
ID=T+"ID']"
cond5={"and":[{"equals":["@%sActionStatus/Value']"%T,"Complete - Awaiting Validation"]},{"equals":["@%sValidationStatus/Value']"%T,"Not Started"]}]}
ok5={
 "Create_review":sp_action("HttpRequest",{"dataset":SITE,"parameters/method":"POST","parameters/uri":"@concat('_api/web/lists(guid',%s,'%s',%s,')/items')"%(Q,L["FollowUps"],Q),"parameters/headers":HP,
   "parameters/body":"@json(concat('{\"Title\":\"Follow-up: ',replace(%sTitle'],'\"',''),'\",\"FindingId\":',%sFinding/Id'],',\"ActionId\":',%sID'],',\"ReviewDate\":\"',addDays(utcNow(),10),'\"}'))"%(T,T,T)}),
 "If_has_auditor":{"runAfter":S("Create_review"),"type":"If","expression":{"equals":["@empty(%sFollowUpAuditor/Email'])"%T,False]},"actions":{
    "Ensure_auditor":sp_action("HttpRequest",{"dataset":SITE,"parameters/method":"POST","parameters/uri":"_api/web/ensureuser","parameters/headers":HP,"parameters/body":"@concat('{\"logonName\":\"i:0#.f|membership|',%sFollowUpAuditor/Email'],'\"}')"%T}),
    "Set_reviewer":mrg("FollowUps","body('Create_review')?['Id']","@concat('{\"ReviewerId\":',body('Ensure_auditor')?['Id'],'}')",S("Ensure_auditor"))},"else":{"actions":{}}},
 "Mark_submitted":mrg("Tracker",ID,'{"ValidationStatus":"Submitted"}',S("If_has_auditor")),
 "Mail_auditor":mail(ME,"@concat('Follow-up review required: ',%sTitle'])"%T,"@concat('<p>Action <b>',%sTitle'],'</b> (owner marked complete, evidence on file) is ready for validation.</p><p>Review item #',body('Create_review')?['Id'],' was created, review date ',formatDateTime(addDays(utcNow(),10),'yyyy-MM-dd'),'.</p>')"%T,S("Mark_submitted")),
 "Audit_review":audit("@concat('Follow-up review created: ',%sTitle'])"%T,"Corrective Action Tracker",ID,"Stage Change","Action submitted for validation",S("Mail_auditor"))}
bad5={
 "Revert_status":mrg("Tracker",ID,'{"ActionStatus":"In Progress"}'),
 "Mail_evidence_required":mail(ME,"@concat('Evidence required before completion: ',%sTitle'])"%T,"@concat('<p>Action <b>',%sTitle'],'</b> was marked complete but no evidence is on file. It has been returned to In Progress. Please upload evidence and mark it complete again.</p>')"%T,S("Revert_status")),
 "Audit_no_evidence":audit("@concat('Completion rejected, no evidence: ',%sTitle'])"%T,"Corrective Action Tracker",ID,"Rejection","No evidence uploaded for the action",S("Mail_evidence_required"))}
act5={"If_awaiting_validation":{"runAfter":{},"type":"If","expression":cond5,"actions":{
   "Get_evidence":get(lurl("Evid","$filter=ActionId eq @{ID}&$top=1&$select=Id".replace("@{ID}","'+X+'")).replace("'+X+'","',%s,'"%ID)),
   "If_evidence":{"runAfter":S("Get_evidence"),"type":"If","expression":{"greater":["@length(body('Get_evidence')?['value'])",0]},"actions":ok5,"else":{"actions":bad5}}},"else":{"actions":{}}}}
wf5=("IAMS-WF5-FollowUpReview",flow_json({"When_an_action_is_created_or_modified":trigger("GetOnUpdatedItems","Tracker")},act5,[SP,OL]),[SP,OL])
# ================= WF4 v2: reminders + overdue escalation =================
TODAY="outputs('Today')"
def dt(expr): return "concat('datetime',%s,%s,'T00:00:00Z',%s)"%(Q,expr,Q)
def qurl(filt): return "@concat('_api/web/lists(guid',%s,'%s',%s,')/items?$top=500&$select=Id,Title,DueDate,ReminderStage,ActionStatus,FindingRating&$filter=',replace(concat(%s),' ','%%20'))"%(Q,L["Tracker"],Q,filt)
NOTCLOSED="' and ActionStatus ne ',%s,'Closed',%s"%(Q,Q)
def stage(s): return "' and ReminderStage eq ',%s,'%s',%s"%(Q,s,Q)
def notstage(s): return "' and ReminderStage ne ',%s,'%s',%s"%(Q,s,Q)
def loop_actions(name,newstage,subject,extra_status=None,evt=None):
    body='{"ReminderStage":"%s"%s}'%(newstage,(',"ActionStatus":"%s"'%extra_status) if extra_status else "")
    d={"Set_"+name:mrg("Tracker","items('Each_%s')?['Id']"%name,body),
       "Mail_"+name:mail(ME,"@concat('%s: ',items('Each_%s')?['Title'])"%(subject,name),"@concat('<p>Action <b>',items('Each_%s')?['Title'],'</b> is due ',formatDateTime(items('Each_%s')?['DueDate'],'yyyy-MM-dd'),'. Stage: %s.</p>')"%(name,name,newstage),S("Set_"+name))}
    if evt: d["Audit_"+name]=audit("@concat('%s: ',items('Each_%s')?['Title'])"%(subject,name),"Corrective Action Tracker","items('Each_%s')?['Id']"%name,evt,"Stage set to %s"%newstage,S("Mail_"+name))
    return d
def block(name,filt,newstage,subject,extra=None,evt=None,after=None):
    return {"Get_"+name:get(qurl(filt),after),
            "Each_"+name:{"runAfter":S("Get_"+name),"type":"Foreach","foreach":"@body('Get_%s')?['value']"%name,"actions":loop_actions(name,newstage,subject,extra,evt)}}
act4={"Today":{"runAfter":{},"type":"Compose","inputs":"@formatDateTime(convertTimeZone(utcNow(),'UTC','Arabian Standard Time'),'yyyy-MM-dd')"},
 "Plus30":{"runAfter":S("Today"),"type":"Compose","inputs":"@formatDateTime(addDays(outputs('Today'),30),'yyyy-MM-dd')"},
 "Plus15":{"runAfter":S("Plus30"),"type":"Compose","inputs":"@formatDateTime(addDays(outputs('Today'),15),'yyyy-MM-dd')"},
 "Minus30":{"runAfter":S("Plus15"),"type":"Compose","inputs":"@formatDateTime(addDays(outputs('Today'),-30),'yyyy-MM-dd')"}}
f_r1="'DueDate le '," + dt("outputs('Plus30')") + ",' and DueDate ge '," + dt(TODAY) + "," + stage("None") + "," + NOTCLOSED
f_r2="'DueDate le '," + dt("outputs('Plus15')") + ",' and DueDate ge '," + dt(TODAY) + "," + stage("Reminder 30d") + "," + NOTCLOSED
f_l1="'DueDate lt '," + dt(TODAY) + "," + notstage("Escalated - Dept Head") + "," + notstage("Escalated - CEO") + "," + NOTCLOSED
f_l2="'DueDate lt '," + dt("outputs('Minus30')") + "," + notstage("Escalated - CEO") + "," + NOTCLOSED
act4.update(block("R1",f_r1,"Reminder 30d","Action due within 30 days",None,None,S("Minus30")))
act4.update(block("R2",f_r2,"Reminder 15d","Action due within 15 days",None,None,S("Each_R1")))
act4.update(block("L1",f_l1,"Escalated - Dept Head","OVERDUE action (escalated to Dept Head)","Overdue","Escalation",S("Each_R2")))
act4.update(block("L2",f_l2,"Escalated - CEO","OVERDUE 30+ days (escalated to CEO)","Overdue","Escalation",S("Each_L1")))
act4["If_any_escalation"]={"runAfter":S("Each_L2"),"type":"If","expression":{"greater":["@add(length(body('Get_L1')?['value']),length(body('Get_L2')?['value']))",0]},"actions":{
   "Mail_digest":mail(ME,"@concat('IA daily escalation digest ',outputs('Today'))","@concat('<p>Escalated to Dept Head: ',length(body('Get_L1')?['value']),'<br>Escalated to CEO: ',length(body('Get_L2')?['value']),'</p>')")},"else":{"actions":{}}}
trig4={"Recurrence":{"type":"Recurrence","recurrence":{"frequency":"Day","interval":1,"timeZone":"Arabian Standard Time","schedule":{"hours":["7"],"minutes":[0]}}}}
wf4=("IAMS-WF4-ActionReminders",flow_json(trig4,act4,[SP,OL]),[SP,OL])
build("IAMSBatch7",[wf5,wf4],"/home/claude/IAMS_Batch7_Solution.zip")
print('ok')

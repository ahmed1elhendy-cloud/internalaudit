from iams_pkg import *
Q="decodeUriComponent('%27')"
TEST="user@example.com"
PID="triggerBody()?['text']";SUB="triggerBody()?['text_1']"
PL=L["Plan"]
def setst(st,after,extra=""):
    return merge(PL,PID,'{"ApprovalStatus":"%s"%s}'%(st,extra),after)
def cm(n): return "coalesce(first(outputs('%s')?['body/responses'])?['comments'],'(no comment)')"%n
P="body('Get_plan')"
def trail(title,det,after):
    return sp_action("PostItem",{"dataset":SITE,"table":L["Trail"],"item/Title":title,"item/SourceList":"Annual Audit Plan","item/SourceItemId":"@int(%s)"%PID,"item/EventType/Value":"Updated","item/EventDetails":det},after)
S=lambda n:{n:["Succeeded"]}
rej2={
 "Set_Draft_2":setst("Draft",{}),
 "Audit_rej_2":trail("@concat('Plan rejected by Head of IA: ',%s?['Title'])"%P,"@%s"%cm("Approval_2_Head_of_IA"),S("Set_Draft_2")),
 "Email_rej_2":mail(TEST,"@concat('Audit plan item rejected by Head of IA: ',%s?['Title'])"%P,"@concat('<p>The plan item <b>',%s?['Title'],'</b> was rejected by the Head of Internal Audit and returned to Draft.</p><p>Comment: ',%s,'</p><p>Intended recipients (test mode redirects to you): planner ',%s,' and the Audit Manager.</p>')"%(P,cm("Approval_2_Head_of_IA"),SUB),S("Audit_rej_2"))}
ok2={
 "Set_Approved":setst("Approved",{}),
 "Audit_ok":trail("@concat('Plan approved: ',%s?['Title'])"%P,"Approved by Audit Manager and Head of IA. Engagement creation (WF1) follows.",S("Set_Approved")),
 "Email_ok":mail(TEST,"@concat('Audit plan item approved: ',%s?['Title'])"%P,"@concat('<p>The plan item <b>',%s?['Title'],'</b> has been approved by the Audit Manager and the Head of IA. The engagement will be created automatically.</p><p>Intended recipient (test mode redirects to you): planner ',%s,'</p>')"%(P,SUB),S("Audit_ok"))}
ok1={
 "Set_Pending_Owner":setst("Pending Owner Approval",{}),
 "Approval_2_Head_of_IA":dict(approval("@concat('Plan approval (2 of 2, Head of IA): ',%s?['Title'])"%P,TEST,"@concat('Audit Manager approved. Ref ',%s?['AuditRef'],'. Manager comment: ',%s)"%(P,cm("Approval_1_Audit_Manager"))),runAfter=S("Set_Pending_Owner")),
 "If_approved_2":{"runAfter":S("Approval_2_Head_of_IA"),"type":"If","expression":{"equals":["@outputs('Approval_2_Head_of_IA')?['body/outcome']","Approve"]},"actions":ok2,"else":{"actions":rej2}}}
rej1={
 "Set_Draft_1":setst("Draft",{}),
 "Audit_rej_1":trail("@concat('Plan rejected by Audit Manager: ',%s?['Title'])"%P,"@%s"%cm("Approval_1_Audit_Manager"),S("Set_Draft_1")),
 "Email_rej_1":mail(TEST,"@concat('Audit plan item rejected by Audit Manager: ',%s?['Title'])"%P,"@concat('<p>The plan item <b>',%s?['Title'],'</b> was rejected by the Audit Manager and returned to Draft.</p><p>Comment: ',%s,'</p><p>Intended recipient (test mode redirects to you): planner ',%s,'</p>')"%(P,cm("Approval_1_Audit_Manager"),SUB),S("Audit_rej_1"))}
act={
 "Get_plan":sp_action("HttpRequest",{"dataset":SITE,"parameters/method":"GET","parameters/uri":"@concat('_api/web/lists(guid',%s,'%s',%s,')/items(',%s,')?$select=Id,Title,AuditRef,ApprovalStatus')"%(Q,PL,Q,PID),"parameters/headers":{"Accept":"application/json;odata=nometadata"}}),
 "Set_Pending_Manager":setst("Pending Manager Review",S("Get_plan")),
 "Respond_submitted":respond({"result":"Submitted for approval. You will be notified by email of the outcome."},S("Set_Pending_Manager")),
 "Approval_1_Audit_Manager":dict(approval("@concat('Plan approval (1 of 2, Audit Manager): ',%s?['Title'])"%P,TEST,"@concat('Ref ',%s?['AuditRef'],'. Submitted by ',%s)"%(P,SUB)),runAfter=S("Respond_submitted")),
 "If_approved_1":{"runAfter":S("Approval_1_Audit_Manager"),"type":"If","expression":{"equals":["@outputs('Approval_1_Audit_Manager')?['body/outcome']","Approve"]},"actions":ok1,"else":{"actions":rej1}}}
wf=("IAMS-WF1a-PlanApproval",flow_json(powerapp_trigger(["PlanItemId","SubmitterEmail"]),act,[SP,OL,AP]),[SP,OL,AP])
build("IAMSBatch8",[wf],"/home/claude/IAMS_Batch8_Solution.zip")
print("ok")

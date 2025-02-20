import frappe
from jitsi_integration.utils.jitsi_utils import generate_jitsi_meeting_token

def check_meeting_info(room):
    if frappe.db.exists("JitSi Meeting", room):
        jitsi_meeting = frappe.get_doc("JitSi Meeting", room)
        is_participant = [False, "You are not in participants list"]
        for jitsi_participant in jitsi_meeting.participants:
            if jitsi_participant.user == frappe.session.user:
                is_participant = [True, jitsi_meeting.meeting_name]
                break
            
        now_time = frappe.utils.now_datetime()
                
        if is_participant[0] and not jitsi_meeting.from_datetime <= now_time <= jitsi_meeting.to_datetime:
            if jitsi_meeting.from_datetime > now_time:
                return [False, "Meeting is not started yet"]
            else:
                return [False, "Meeting is already ended"]
            
        return is_participant
    else:
        return [False, "Meeting not found"]

@frappe.whitelist()
def get_jitsi_meeting_url(room):
    if frappe.session.user and frappe.session.user != "Guest" and frappe.db.exists("User", frappe.session.user):
        user = frappe.get_doc("User", frappe.session.user)
        meeting_info = check_meeting_info(room)
        if meeting_info[0]:
            domain = frappe.get_single("JitSi Settings").domain
            jitsi_meeting_token = generate_jitsi_meeting_token(full_name=user.full_name, email=user.email)
            if jitsi_meeting_token:
                meeting_url = f"https://{domain}/{meeting_info[1]}?jwt={jitsi_meeting_token}"
                return [True, meeting_url]
            else:
                return [False, "Error while generating token"]
        else:
            return meeting_info
    else:
        return [False, "User doesn't exist"]
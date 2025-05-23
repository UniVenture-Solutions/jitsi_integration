import frappe
from jitsi_integration.utils.jitsi_utils import generate_jitsi_meeting_token, decrypt_info

def check_meeting_info(room, user, guest):
    if frappe.db.exists("JitSi Meeting", room):
        jitsi_meeting = frappe.get_doc("JitSi Meeting", room)
        is_participant = [False, "You are not in participants list"]
        
        if user:
            if not guest:
                for jitsi_participant in jitsi_meeting.participants:
                    if jitsi_participant.user == user:
                        is_participant = [True, jitsi_meeting.meeting_name, jitsi_participant.full_name]
                        break
            else:
                for guest in jitsi_meeting.guests:
                    if guest.email == user:
                        is_participant = [True, jitsi_meeting.meeting_name, guest.full_name]
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

@frappe.whitelist(allow_guest=True)
def get_jitsi_meeting_url(room, guest=None):
    user = "Guest" if guest else None
    is_guest = True if guest else False
    
    if frappe.session.user != "Guest":
        user = frappe.get_doc("User", frappe.session.user)
        is_guest = False
    
    if user:
        email = frappe.session.user
        if is_guest:
            email = decrypt_info(guest) or None
            
        meeting_info = check_meeting_info(room, email, guest=is_guest)
        if meeting_info[0]:
            domain = frappe.get_single("JitSi Settings").domain
            jitsi_meeting_token = generate_jitsi_meeting_token(full_name=meeting_info[2], email=email)
            if jitsi_meeting_token:
                meeting_url = f"{domain}/{meeting_info[1]}?jwt={jitsi_meeting_token}"
                return [True, meeting_url]
            else:
                return [False, "Error while generating token"]
        else:
            return meeting_info 
    else:
        return [False, "User doesn't exist"]
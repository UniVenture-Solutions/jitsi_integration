import smtplib
from email.message import EmailMessage
from caldav import DAVClient
from datetime import datetime
from jitsi_integration.utils.jitsi_utils import generate_jitsi_meeting_token
import random
import re
import frappe
from jitsi_integration.utils.jitsi_utils import encrypt_info

class EventScheduler:
    def __init__(self, user_url, meeting_name, frappe_email_account_name=None):
        if not frappe_email_account_name:
            frappe_email_account_name = frappe.get_doc("Email Account", {"default_outgoing": 1})
        self.user_url = user_url
        self.meeting_name = meeting_name
        # Fetch SMTP settings and Mailcow credentials from Frappe
        self.mailcow_email, self.mailcow_password, self.mailcow_domain, self.smtp_server, self.smtp_port = self.get_frappe_email_settings(frappe_email_account_name)
        self.mailcow_caldav_url = f"https://mail.{self.mailcow_domain}/SOGo/dav/{self.mailcow_email}/Calendar/personal/"

    def get_frappe_email_settings(self, frappe_email_account_name=None):
        # Retrieve email account settings from Frappe

        if not frappe_email_account_name:
            raise ValueError(f"Email account {frappe_email_account_name} not found in Frappe.")
        email_account = frappe.get_doc("Email Account", frappe_email_account_name)
        # Get the Mailcow credentials and SMTP server details
        mailcow_email = email_account.email_id
        mailcow_password = email_account.get_password('password')
        mailcow_domain = email_account.domain
        smtp_server = email_account.smtp_server
        smtp_port = email_account.smtp_port or 465  # Default to 465 if not specified
        
        return mailcow_email, mailcow_password, mailcow_domain, smtp_server, smtp_port

    def generate_event_uid(self, event_title):
        # Generates a unique event UID based on the event title and random digits
        digits = ''.join(random.choices('0123456789', k=8))
        slug = re.sub(r'[^a-z0-9]+', '-', event_title.lower()).strip('-')
        return f"event-{digits}-{slug}@{self.mailcow_domain}"

    def split_invitees(self, invitees):
        # Splits invitees into mailcow users and external users based on domain
        mailcow = []
        external = []
        for user in invitees:
            user = user.as_dict()
            domain = user["email"].split("@")[1].lower()
            if domain == self.mailcow_domain:
                user["link"] = self.user_url
                mailcow.append(user)
            else:
                user["link"] = f"{self.user_url}&guest={encrypt_info(user['email'])}"
                external.append(user)
        return mailcow, external

    def generate_unique_link(self, full_name, invitee_email):
        # Generate a unique meeting link for each invitee (e.g., for a Zoom meeting)
        # Here, we'll use the invitee's email to create a unique link, but you can use other data as well
        # meeting_link = f"https://zoom.us/j/{random.randint(1000000000, 9999999999)}?invitee={invitee_email}"
        settings = frappe.get_single('JitSi Settings')
        if not settings.domain:
            frappe.throw("Domain not set in JitSi Settings.")
        token = generate_jitsi_meeting_token(full_name=full_name, email=invitee_email)
        meeting_link = f"{settings.domain}/{self.meeting_name}?jwt={token}"
        return meeting_link

    def create_ics_content(self, event_uid, event_title, event_description, event_location, start, end, user, invitees):
        # Generates the ICS content string with unique meeting link for each invitee
        ics = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//UnisolERP//Mailcow Calendar Integration//EN
CALSCALE:GREGORIAN
METHOD:REQUEST
BEGIN:VEVENT
UID:{event_uid}
DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}
DTSTART:{start.strftime('%Y%m%dT%H%M%SZ')}
DTEND:{end.strftime('%Y%m%dT%H%M%SZ')}
SUMMARY:{event_title}
DESCRIPTION:{event_description} Join the meeting: {user['link']}
LOCATION:{event_location}
ORGANIZER;CN=ERP Coordinator:mailto:{self.mailcow_email}
"""
        for u in invitees:
            # unique_link = self.generate_unique_link(user['email'])
            ics += f"ATTENDEE;CN={u['full_name']};RSVP=TRUE:mailto:{u['email']}\n"
            # ics += f"DESCRIPTION:{event_description} Join the meeting: {self.user_url}\n" 

        ics += """END:VEVENT
END:VCALENDAR"""

        return ics

    def add_event_to_mailcow_calendar(self, event_uid, event_title, event_description, event_location, start, end, invitees):
        # Adds the event to the Mailcow calendar via CalDAV
        client = DAVClient(
            url=self.mailcow_caldav_url,
            username=self.mailcow_email,
            password=self.mailcow_password
        )
        principal = client.principal()
        calendars = principal.calendars()
        calendar = calendars[0]
        
        for user in invitees:
            ical_event = self.create_ics_content(event_uid, event_title, event_description, event_location, start, end, user, invitees)
            try:
                self.send_email_invites(ical_event, user, event_title)
            except Exception as e:
                frappe.log_error("ICS Content:", ical_event)
                frappe.throw("Something went wrong.")

        print("✅ Event added to Mailcow calendar")

    def send_email_invites(self, ics_content, user, event_title):
        # Sends email invites with the ICS calendar invite as an attachment
        if not user:
            print("ℹ️ No invitee to email.")
            return

        with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as smtp:
            smtp.login(self.mailcow_email, self.mailcow_password)
            msg = EmailMessage()
            email = user['email']
            meeting_link = user['link']
            msg['Subject'] = f"You're Invited: {event_title}"
            msg['From'] = self.mailcow_email
            msg['To'] = email
            msg.set_content(f"Hi {user['full_name']},\n\nYou're invited to {event_title}.\nPlease see the attached updated calendar invite.\n\nJoin the meeting: {meeting_link}")

            # Attach the ICS content directly in memory (no file needed)
            msg.add_attachment(ics_content.encode('utf-8'), maintype='text', subtype='calendar', filename="invite.ics")

            smtp.send_message(msg)
            print(f"📧 Sent invite to {user['email']}")

    def create_event(self, event_title, event_description, event_location, start, end, invitees, event_uid):
        # Main function to create the event (generate ICS, add to Mailcow, send invites)
        event_uid = self.generate_event_uid(event_title)
        mailcow_invitees, external_invitees = self.split_invitees(invitees)
        sep_invitees = [*mailcow_invitees, *external_invitees]
        self.add_event_to_mailcow_calendar(event_uid, event_title, event_description, event_location, start, end, sep_invitees)
        return True

    def reschedule_event(self, event_uid, event_title, event_description, event_location, new_start, new_end, invitees):
        # Function to reschedule an existing event and send new invites
        print(f"Rescheduling event: {event_uid}")
        
        # Generate new ICS content with the updated time
        ics_content = self.create_ics_content(event_uid, event_title, event_description, event_location, new_start, new_end, invitees)
        
        # Update the event in Mailcow (same UID but updated start and end time)
        self.add_event_to_mailcow_calendar(event_uid, event_title, event_description, event_location, new_start, new_end, invitees)
        
        # Send updated email invites to external users
        external_invitees = [user for user in invitees if user["email"].split("@")[1].lower() != self.mailcow_domain]
        self.send_email_invites(ics_content, external_invitees, event_title)


# ----------------------------
# USAGE EXAMPLE
# ----------------------------

# if __name__ == "__main__":
#     # Example event details
#     EVENT_TITLE = "Project Kickoff"
#     EVENT_DESCRIPTION = "Kickoff meeting for the ERP project."
#     EVENT_LOCATION = "Zoom"
#     EVENT_START = datetime(2025, 4, 20, 14, 0)  # UTC
#     EVENT_END = EVENT_START + timedelta(hours=1)

#     INVITEES = [
#         {"name": "User1", "email": "user1@unisolerp.com"},
#         {"name": "External User", "email": "external@example.com"},
#         {"name": "Client A", "email": "client@example.com"},
#         {"name": "Internal Team", "email": "internal@unisolerp.com"},
#     ]

#     # Instantiate the EventScheduler class with Frappe email account
#     scheduler = EventScheduler(
#         frappe_email_account_name="cerp@unisolerp.com"  # Default email account in Frappe
#     )

#     # Create and schedule the event
#     scheduler.create_event(
#         event_title=EVENT_TITLE,
#         event_description=EVENT_DESCRIPTION,
#         event_location=EVENT_LOCATION,
#         start=EVENT_START,
#         end=EVENT_END,
#         invitees=INVITEES
#     )

#     # Example of rescheduling the event
#     NEW_EVENT_START = datetime(2025, 4, 21, 15, 0)  # New start time (UTC)
#     NEW_EVENT_END = NEW_EVENT_START + timedelta(hours=1)  # New end time

#     # Reschedule the event (you should know the event UID)
#     EVENT_UID = "event-12345678-project-kickoff@unisolerp.com"  # Example UID
#     scheduler.reschedule_event(
#         event_uid=EVENT_UID,
#         event_title=EVENT_TITLE,
#         event_description=EVENT_DESCRIPTION,
#         event_location=EVENT_LOCATION,
#         new_start=NEW_EVENT_START,
#         new_end=NEW_EVENT_END,
#         invitees=INVITEES
#     )

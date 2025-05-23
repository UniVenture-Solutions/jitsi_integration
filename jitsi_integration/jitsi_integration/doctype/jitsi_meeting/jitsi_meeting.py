# Copyright (c) 2025, Khizer Saeed and contributors
# For license information, please see license.txt

import frappe
import requests
from frappe.model.document import Document
from jitsi_integration.www.meet.index import get_jitsi_meeting_url
from jitsi_integration.utils.jitsi_utils import generate_jitsi_meeting_token
from mattermost_integration.api.mattermost_methods import create_posts
from jitsi_integration.invite import EventScheduler

class JitSiMeeting(Document):
	def before_validate(self):
		self.meeting_name = "_".join(self.meeting_name.split(" "))
		
	@frappe.whitelist()
	def go_to_meeting(self):
		response = get_jitsi_meeting_url(self.name)
		return response

	def after_insert(self):
		self.generate_event_uid()

	def generate_event_uid(self):
		self.db_set("event_uid", f"event-{self.name}-{self.meeting_name}@cerp.com")

	@frappe.whitelist()
	def send_invitation(self, domain, user_invitation_mode):
		user_url = f"{domain}/meet?room={self.name}"
		event = EventScheduler(user_url, self.meeting_name, "Staging Development")
		response = event.create_event(
			self.meeting_agenda,
			self.meeting_details,
			"JitSi Meet",
			frappe.utils.get_datetime(self.from_datetime),
			frappe.utils.get_datetime(self.to_datetime),
			self.participants + self.guests,
			self.event_uid
		)

		return response

	@frappe.whitelist()
	def _send_invitation(self, domain, user_invitation_mode):
		user_url = f"{domain}/meet?room={self.name}"
		res = self.invite_guests()
		if user_invitation_mode == 'email':
			msg = self.invite_users_email(user_url)
			if msg:
				res = msg
		elif user_invitation_mode == 'mattermost':
			msg = self.invite_users_mattermost(user_url)
			if msg:
				res = msg

		return res

	def invite_users_email(self, url):
		if len(self.participants) > 0:
			for participant in self.participants:
				self.send_invitation_email(participant.user, url)
			return "Invitation sent successfully"

	def invite_users_mattermost(self, url):
		participants = ""
		part_len = 0
		if len(self.participants) > 0:
			for participant in self.participants:
				if frappe.db.exists("User", participant.user):
					user = frappe.get_doc("User", participant.user)
					full_name = user.full_name
					symbol = ", " if participant.user != self.participants[-1].user else ""
					participants += f"{full_name}{symbol}"
					part_len += 1
			return self.send_invitation_mattermost(participants, part_len, url)

	def invite_guests(self):
		if len(self.guests) > 0:
			for guest in self.guests:
				token = generate_jitsi_meeting_token(full_name=guest.full_name, email=guest.email)	
				url = f"{frappe.get_single('JitSi Settings').domain}/{self.meeting_name}?jwt={token}"
				self.send_invitation_email(guest.email, url)
			return "Invitation sent successfully"


	def send_invitation_email(self, email, url):
		try:
			message = f"""
			You are invited to join the meeting. Please click on the link below to join the meeting.<br><br>
			<strong>Meeting Details:</strong> {self.meeting_details} <br><br>
			<a href="{url}" style="
				display: inline-block;
				padding: 10px 20px;
				font-size: 16px;
				color: #fff;
				background-color: #007bff;
				text-decoration: none;
				border-radius: 5px;
			">Join Meeting</a>
			"""
			frappe.sendmail(
				recipients=[email],
				subject=self.meeting_agenda,
				message=message
			)
		except Exception as e:
			frappe.log_error("Email Notification Error", f"Exception occurred: {str(e)}")
			frappe.throw("Something went wrong while sending invitation at email")

	def send_invitation_mattermost(self, participants, part_len, url):
		try:
			hv = "are" if part_len > 1 else "is"
			message = f"{participants} {hv} invited to join the meeting. Please click on the link below to join the meeting." + "\n" + f"{url}" "\n" + f"**Meeting Details:** {self.meeting_details}"
			settings = frappe.get_single("Mattermost Settings")

			if not settings.mattermost_meeting_channel:
				frappe.throw("Please set the Mattermost Meeting Channel in Mattermost Settings")

			channel_id = frappe.db.get_value("Mattermost Channel", settings.mattermost_meeting_channel, "channel_id")
			if not channel_id:
				frappe.throw("Channel ID not found for the Mattermost Meeting Channel")

			response = create_posts(channel_id, message)
			if response and response.get("id"):
				return "Invitation sent successfully"
			else:
				error_message = response.detailed_error or "No detailed error provided"
				frappe.log_error(
					title="Mattermost Notification Failed",  
					message=f"Failed to send notification.\n\nError: {error_message}"
				)
				frappe.throw("Failed to send invitation at mattermost")
		
		except Exception as e:
			frappe.log_error(
				title="Mattermost Notification Error",
				message=f"Exception occurred: {str(e)}"
			)
			frappe.throw("Something went wrong while sending invitation at mattermost")
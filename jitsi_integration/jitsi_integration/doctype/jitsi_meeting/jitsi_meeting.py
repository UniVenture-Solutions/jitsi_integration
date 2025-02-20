# Copyright (c) 2025, Khizer Saeed and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from jitsi_integration.www.meet.index import get_jitsi_meeting_url
from jitsi_integration.utils.jitsi_utils import generate_jitsi_meeting_token


class JitSiMeeting(Document):
	@frappe.whitelist()
	def go_to_meeting(self):
		response = get_jitsi_meeting_url(self.name)
		return response

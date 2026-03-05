# Copyright (c) 2026, Aerele Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from nomination.api.validation import validate_aadhaar_number, validate_date_of_birth, validate_pan_number


class NominationForm(Document):
	def before_insert(self):
		if self.aadhaar_number:
			validate_aadhaar_number(self.aadhaar_number)

		if self.pan_number:
			validate_pan_number(self.pan_number)
		if self.date_of_birth:
			validate_date_of_birth(self.date_of_birth)

	def before_save(self):
		self.set_approval_log()

	def on_update(self):
		self.set_approval_log()

	def set_approval_log(self):
		current_user = frappe.session.user
		current_time = frappe.utils.now()

		if self.workflow_state == "VO Approved" and not self.vo_approval_by:
			self.vo_approval_by = current_user
			self.vo_approved_on = current_time

		elif self.workflow_state == "CLF Approved" and not self.clf_approval_by:
			print("Setting CLF approval")
			self.clf_approval_by = current_user
			self.clf_approved_on = current_time

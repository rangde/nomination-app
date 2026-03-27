# Copyright (c) 2026, Aerele Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import cint, get_fullname
from nomination.api.validation import validate_aadhaar_number, validate_date_of_birth, validate_pan_number


class NominationForm(Document):
	
	def validate(self):
		self.set_proposed_amount()

	def set_proposed_amount(self):
		role_field_map = frappe._dict({
			"SHG Proposed": "shg_proposed",
			"VO Approved":  "vo_proposed",
			"CLF Approved": "clf_proposed",
		})
		if role_field_map.get(self.workflow_state):
			self.set(role_field_map[self.workflow_state], cint(self.set_credit_limit))

	def before_insert(self):
		if self.aadhaar_number:
			validate_aadhaar_number(self.aadhaar_number)

		if self.pan_number:
			validate_pan_number(self.pan_number)
		if self.date_of_birth:
			validate_date_of_birth(self.date_of_birth)

	def before_save(self):
		self.set_approval_log()

	def set_approval_log(self):
		current_user = frappe.session.user
		current_time = frappe.utils.now()

		approved_by = frappe._dict({
			"SHG Proposed": "shg",
			"VO Approved":  "vo",
			"CLF Approved": "clf",
		})

		if approved_by.get(self.workflow_state):
			self.set(f"{approved_by.get(self.workflow_state)}_approval_by", get_fullname(current_user))
			self.set(f"{approved_by.get(self.workflow_state)}_approved_on", current_time)

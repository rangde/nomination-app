# Copyright (c) 2026, Aerele Technologies and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class Organization(Document):
	def autoname(self):
		if self.shg == 1:
			self.name = f"{self.organisation_name}-SHG"
		if self.vo == 1:
			self.name = f"{self.organisation_name}-VO"

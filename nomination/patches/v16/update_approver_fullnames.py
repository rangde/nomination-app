import frappe

approvers = ["shg", "vo", "clf"]


def execute():
	nomination_forms = frappe.get_all("Nomination Form", pluck="name")
	for nomination_form in nomination_forms:
		nomination = frappe.get_doc("Nomination Form", nomination_form)
		for row in approvers:
			fieldname = f"{row}_approval_by"
			frappe.db.set_value("Nomination Form", nomination_form, fieldname, frappe.utils.get_fullname(nomination.get(fieldname)))

import json

import frappe
from frappe import _
from frappe.query_builder import DocType


def before_insert(doc, method):
	if not doc.mobile_no:
		frappe.throw("Mobile number is required to create a user.")

	if not doc.email:
		mobile = doc.mobile_no.strip().replace(" ", "").replace("+", "")
		doc.email = f"{mobile}@nomination.com"
		doc.name = doc.email


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_approvers(doctype, txt, searchfield, start, page_len, filters):
	roles = filters.get("roles") or []

	if "SHG" in roles:
		approver_role = "VO"
	elif "VO" in roles:
		approver_role = "CLF"
	else:
		frappe.throw(_("No valid role found to determine approver."))

	User = DocType("User")
	HasRole = DocType("Has Role")

	approvers = (
		frappe.qb.from_(User)
		.join(HasRole)
		.on(HasRole.parent == User.name)
		.select(User.name, User.full_name)
		.where(HasRole.role == approver_role)
		.where(User.enabled == 1)
		.where(User.name.like(f"%{txt}%"))
	).run()

	if not approvers:
		frappe.throw(
			_("No {0} users found to set as approver.").format(frappe.bold(approver_role)),
			title=_("Approver Missing"),
		)

	return set(tuple(approver) for approver in approvers)

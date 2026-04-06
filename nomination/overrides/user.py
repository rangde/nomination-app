import frappe


def before_insert(doc, method):
	if not doc.mobile_no:
		frappe.throw("Mobile number is required to create a user.")

	if not doc.email:
		mobile = doc.mobile_no.strip().replace(" ", "").replace("+", "")
		doc.email = f"{mobile}@nomination.com"
		doc.name = doc.email

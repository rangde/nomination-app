import base64

import frappe
from frappe.utils.pdf import get_pdf

CREDIT_REPORT_DOCTYPE = "Nomination Form"


def _report_file_name(docname):
	return f"Credit Report - {docname}.pdf"


def generate_credit_report(docname, report_base64):
	if not report_base64:
		return None

	try:
		html = base64.b64decode(report_base64).decode("utf-8")
		pdf_content = get_pdf(html)

		file_name = _report_file_name(docname)

		existing = frappe.get_all(
			"File",
			filters={
				"attached_to_doctype": CREDIT_REPORT_DOCTYPE,
				"attached_to_name": docname,
				"file_name": file_name,
			},
			pluck="name",
		)
		if existing:
			frappe.delete_doc("File", existing[0], force=True)

		_file = frappe.get_doc(
			{
				"doctype": "File",
				"file_name": file_name,
				"content": pdf_content,
				"attached_to_doctype": CREDIT_REPORT_DOCTYPE,
				"attached_to_name": docname,
				"is_private": 1,
			}
		)
		_file.insert(ignore_permissions=True)
		return _file.file_url

	except Exception:
		frappe.log_error(frappe.get_traceback(), "Credit Report PDF Generation Error")
		return None


@frappe.whitelist()
def get_credit_report(docname):
	if frappe.session.user == "Guest":
		return {"status": 0, "msg": "Not logged in"}
	if "System Manager" not in frappe.get_roles(frappe.session.user):
		frappe.throw("Not permitted to view the credit report", frappe.PermissionError)

	file_url = frappe.db.get_value(
		"File",
		{
			"attached_to_doctype": CREDIT_REPORT_DOCTYPE,
			"attached_to_name": docname,
			"file_name": _report_file_name(docname),
		},
		"file_url",
	)

	return {"file_url": file_url}

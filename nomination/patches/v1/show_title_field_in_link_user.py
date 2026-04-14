import frappe


def execute():
	user_doctype = frappe.get_doc("DocType", "User")

	updated = False

	if user_doctype.title_field != "full_name":
		user_doctype.title_field = "full_name"
		updated = True

	if not user_doctype.show_title_field_in_link:
		user_doctype.show_title_field_in_link = 1
		updated = True

	if updated:
		user_doctype.save()
		frappe.db.commit()

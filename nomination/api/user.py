import frappe


@frappe.whitelist()
def get_user_info():
	if frappe.session.user == "Guest":
		return {"status": 0, "msg": "Not logged in"}

	user = frappe.session.user

	user_info = frappe.get_value("User", user, ["full_name", "mobile_no", "email"], as_dict=True)

	profile_url = frappe.get_value(
		"File",
		filters={"attached_to_doctype": "User", "attached_to_name": user, "attached_to_field": "user_image"},
		fieldname="file_url",
	)

	user_info["profile"] = profile_url

	user_info = [user_info]

	return {"status": 1, "msg": user_info}


@frappe.whitelist()
def get_roles():
	if frappe.session.user == "Guest":
		return {"status": 0, "msg": "Not logged in"}

	user = frappe.session.user
	roles = frappe.get_roles(user)

	return {"status": 1, "msg": roles}

import frappe


def execute():
	nomination_roles = ["SHG", "VO", "GPLF", "System Manager", "Administrator", "All", "Guest"]

	roles = frappe.db.set_value("Role", {"name": ["not in", nomination_roles]}, "disabled", 1)

	return roles

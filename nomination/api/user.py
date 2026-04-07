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


@frappe.whitelist()
def get_user_hierarchy():
	rows = frappe.get_all("User", fields=["name", "reports_to"], filters={"enabled": 1})

	children_map: dict[str, list[str]] = {}
	child_set: set[str] = set()
	full_names: dict[str, str] = {}

	for r in rows:
		full_names[r.name] = frappe.get_value("User", r.name, "full_name") or r.name
		if r.reports_to:
			children_map.setdefault(r.reports_to, []).append(r.name)
			child_set.add(r.name)

	roots = set(children_map.keys()) - child_set

	def build_node(user, visited=None):
		if visited is None:
			visited = set()

		if user in visited:
			return {
				"user": user,
				"full_name": full_names.get(user, user) + "  (cycle)",
				"children": [],
			}

		visited = visited | {user}

		return {
			"user": user,
			"full_name": full_names.get(user, user),
			"children": [build_node(c, visited) for c in children_map.get(user, [])],
		}

	return [build_node(r) for r in roots]

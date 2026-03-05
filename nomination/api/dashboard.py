import frappe


@frappe.whitelist()
def get_nomination_list():
	if frappe.session.user == "Guest":
		return {"status": 0, "msg": "Not logged in"}

	user = frappe.session.user
	roles = frappe.get_roles(user)

	response = {}

	if "SHG" in roles:
		response = {
			"submitted": frappe.get_list(
				"Nomination Form",
				filters={"owner": user, "workflow_state": "SHG Proposed"},
				fields=["*"],
				order_by="creation desc",
			),
			"ready_for_training": frappe.get_list(
				"Nomination Form",
				filters={"owner": user, "workflow_state": "CLF Approved"},
				fields=["*"],
				order_by="creation desc",
			),
		}

	elif "VO" in roles:
		response = {
			"submitted": frappe.get_list(
				"Nomination Form",
				filters={"workflow_state": "SHG Proposed"},
				fields=["*"],
				order_by="creation desc",
			),
			"ready_for_training": frappe.get_list(
				"Nomination Form",
				filters={"workflow_state": "VO Approved"},
				fields=["*"],
				order_by="creation desc",
			),
		}

	elif "CLF" in roles:
		response = {
			"submitted": frappe.get_list(
				"Nomination Form",
				filters={"workflow_state": "VO Approved"},
				fields=["*"],
				order_by="creation desc",
			),
			"ready_for_training": frappe.get_list(
				"Nomination Form",
				filters={"workflow_state": "CLF Approved"},
				fields=["*"],
				order_by="creation desc",
			),
		}

	return {"status": 1, "msg": [response]}

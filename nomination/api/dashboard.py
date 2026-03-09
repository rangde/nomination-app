import frappe

from nomination.api.rangde_service import get_metrics


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


@frappe.whitelist(allow_guest=True)
def get_dashboard_metrics():
	metrics = get_metrics()

	return {
		"nomination": {
			"shg_approved": frappe.db.count("Nomination Form", {"workflow_state": "SHG Proposed"}),
			"vo_pending": frappe.db.count("Nomination Form", {"workflow_state": "SHG Proposed"}),
			"vo_approved": frappe.db.count("Nomination Form", {"workflow_state": "VO Approved"}),
			"clf_pending": frappe.db.count("Nomination Form", {"workflow_state": "VO Approved"}),
			"clf_approved": frappe.db.count("Nomination Form", {"workflow_state": "CLF Approved"}),
		},
		"training": {
			"total_registered": metrics.get("totalTrainees"),
			"under_training": metrics.get("completedTraining"),
			"passed": metrics.get("passed"),
			"failed": metrics.get("failed"),
		},
		"loan": {
			"loan_applicants": metrics.get("numLoans"),
			"loan_disbursed": metrics.get("numDisbursedLoans"),
			"amount_disbursed": metrics.get("amountDisbursed"),
			"median_days": metrics.get("medianDaysToDisbursal"),
		},
	}

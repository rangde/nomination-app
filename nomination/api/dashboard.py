import frappe

from nomination.api.rangde_service import get_metrics


def _user_sees_all_nominations(user: str) -> bool:
	if user == "Administrator":
		return True
	return "System Manager" in frappe.get_roles(user)


def _get_subordinate_users(manager: str) -> set[str]:
	"""Users who report to `manager`, directly or transitively (User Reporting)."""
	subordinates: set[str] = set()
	queue: list[str] = [manager]
	expanded: set[str] = set()

	while queue:
		m = queue.pop(0)
		if m in expanded:
			continue
		expanded.add(m)

		direct = frappe.get_all(
			"User Reporting",
			filters={"reports_to": m},
			pluck="user",
		)
		for u in direct:
			if u not in subordinates:
				subordinates.add(u)
				queue.append(u)

	return subordinates


def _count_nomination_forms(workflow_state: str, owners: set[str] | None) -> int:
	filters: dict = {"workflow_state": workflow_state}
	if owners is not None:
		if not owners:
			return 0
		filters["owner"] = ["in", list(owners)]
	return frappe.db.count("Nomination Form", filters)


def _nomination_owner_scope_for_session() -> set[str] | None:
	"""None = no owner filter (all forms). Otherwise restrict to these owners (SHG creators)."""
	user = frappe.session.user
	if user == "Guest":
		frappe.throw(frappe._("Please log in to view the dashboard."))

	if _user_sees_all_nominations(user):
		return None

	return _get_subordinate_users(user)


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


@frappe.whitelist()
def get_dashboard_metrics():
	metrics = get_metrics()
	owners = _nomination_owner_scope_for_session()

	return {
		"nomination": {
			"shg_approved": _count_nomination_forms("SHG Proposed", owners),
			"vo_pending": _count_nomination_forms("SHG Proposed", owners),
			"vo_approved": _count_nomination_forms("VO Approved", owners),
			"clf_pending": _count_nomination_forms("VO Approved", owners),
			"clf_approved": _count_nomination_forms("CLF Approved", owners),
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

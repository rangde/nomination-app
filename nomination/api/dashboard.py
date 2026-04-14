import frappe
from frappe.utils import get_fullname

from nomination.api.rangde_service import get_metrics


def _user_sees_all_nominations(user: str) -> bool:
	if user == "Administrator":
		return True
	return "System Manager" in frappe.get_roles(user)


def _get_subordinate_users(manager: str) -> set[str]:
	rows = frappe.get_all(
		"User",
		fields=["name", "reports_to"],
		filters={"enabled": 1},
	)

	children_map: dict[str, list[str]] = {}
	for r in rows:
		if r.reports_to:
			children_map.setdefault(r.reports_to, []).append(r.name)

	subordinates: set[str] = set()
	queue = [manager]
	while queue:
		current = queue.pop(0)
		for child in children_map.get(current, []):
			if child not in subordinates:
				subordinates.add(child)
				queue.append(child)

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


def get_nominations(
	workflow_state: str | list[str] | tuple[str, ...] | None = None,
	approval_field: str | None = None,
	approver_name: str | None = None,
):
	nomination_form = frappe.qb.DocType("Nomination Form")
	query = frappe.qb.from_(nomination_form).select(nomination_form.star)

	if workflow_state:
		if isinstance(workflow_state, (list, tuple)):
			query = query.where(nomination_form.workflow_state.isin(workflow_state))
		else:
			query = query.where(nomination_form.workflow_state == workflow_state)

	if approval_field and approver_name:
		query = query.where(nomination_form[approval_field] == approver_name)

	return query.orderby(nomination_form.creation, order=frappe.qb.desc).run(as_dict=True)


@frappe.whitelist()
def get_nomination_list():
	if frappe.session.user == "Guest":
		return {"status": 0, "msg": "Not logged in"}

	user = frappe.session.user
	full_name = get_fullname(user)
	roles = frappe.get_roles(user)

	response = {}

	if "SHG" in roles:
		response = {
			"submitted": get_nominations(
				workflow_state=["SHG Proposed", "VO Approved"],
				approval_field="shg_approval_by",
				approver_name=full_name,
			),
			"ready_for_training": get_nominations(
				workflow_state="CLF Approved", approval_field="shg_approval_by", approver_name=full_name
			),
		}

	elif "VO" in roles:
		response = {
			"submitted": get_nominations(workflow_state="SHG Proposed"),
			"ready_for_training": get_nominations(approval_field="vo_approval_by", approver_name=full_name),
		}

	elif "CLF" in roles:
		response = {
			"submitted": get_nominations(workflow_state="VO Approved"),
			"ready_for_training": get_nominations(approval_field="clf_approval_by", approver_name=full_name),
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

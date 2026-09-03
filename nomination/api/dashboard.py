import frappe
from frappe.utils import get_fullname

from nomination.api.rangde_service import get_metrics

dashboard_access = {"System Manager", "Read only"}

DASHBOARD_STAGE_FILTERS = {
	"all": None,
	"shg_approved": "SHG Proposed",
	"vo_pending": "SHG Proposed",
	"vo_approved": "VO Approved",
	"clf_pending": "VO Approved",
	"clf_approved": "CLF Approved",
}


def _user_sees_all_nominations(user: str) -> bool:
	roles = set(frappe.get_roles(user))
	return bool(dashboard_access & roles)


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


def _as_filter_values(value):
	if not value:
		return []
	if isinstance(value, str):
		return [item.strip() for item in value.split(",") if item.strip()]
	if isinstance(value, (list, tuple, set)):
		return [str(item).strip() for item in value if str(item).strip()]
	return [str(value).strip()]


def _list_filters(stage_key: str, owners: set[str] | None, vo=None, shg=None):
	stage_keys = _as_filter_values(stage_key) or ["all"]
	if any(key not in DASHBOARD_STAGE_FILTERS for key in stage_keys):
		frappe.throw(frappe._("Invalid dashboard stage selected."))

	workflow_states = sorted(
		{DASHBOARD_STAGE_FILTERS.get(key) for key in stage_keys if DASHBOARD_STAGE_FILTERS.get(key)}
	)
	filters = {}

	if workflow_states and "all" not in stage_keys:
		filters["workflow_state"] = (
			workflow_states[0] if len(workflow_states) == 1 else ["in", workflow_states]
		)

	if owners is not None:
		if not owners:
			return None
		filters["owner"] = ["in", list(owners)]

	vo_values = _as_filter_values(vo)
	shg_values = _as_filter_values(shg)
	if vo_values:
		filters["name_of_the_vo"] = vo_values[0] if len(vo_values) == 1 else ["in", vo_values]
	if shg_values:
		filters["name_of_the_shg"] = shg_values[0] if len(shg_values) == 1 else ["in", shg_values]

	return filters


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


@frappe.whitelist()
def get_dashboard_nomination_rows(
	stage_key,
	page=1,
	page_size=10,
	search=None,
	vo=None,
	shg=None,
	sort_by="modified",
):
	owners = _nomination_owner_scope_for_session()
	filters = _list_filters(stage_key, owners, vo, shg)
	if filters is None:
		return {
			"status": 1,
			"msg": {
				"rows": [],
				"total": 0,
				"page": 1,
				"page_size": page_size,
				"vos": [],
				"shgs": [],
			},
		}

	try:
		page = max(int(page), 1)
	except (TypeError, ValueError):
		page = 1

	try:
		page_size = min(max(int(page_size), 1), 10000)
	except (TypeError, ValueError):
		page_size = 20

	search = (search or "").strip()
	or_filters = []
	if search:
		like = f"%{search}%"
		or_filters = [
			["Nomination Form", "first_name", "like", like],
			["Nomination Form", "last_name", "like", like],
			["Nomination Form", "townvillage", "like", like],
			["Nomination Form", "name_of_the_shg", "like", like],
			["Nomination Form", "name_of_the_vo", "like", like],
		]

	order_by = "creation desc" if sort_by == "created" else "modified desc"
	fields = [
		"name",
		"first_name",
		"last_name",
		"townvillage",
		"name_of_the_shg",
		"name_of_the_vo",
		"workflow_state",
		"shg_approval_by",
		"shg_approved_on",
		"vo_approval_by",
		"vo_approved_on",
		"clf_approval_by",
		"clf_approved_on",
		"creation",
		"modified",
		"photo_of_didi",
	]

	total = len(
		frappe.get_all(
			"Nomination Form",
			filters=filters,
			or_filters=or_filters,
			pluck="name",
		)
	)
	rows = frappe.get_all(
		"Nomination Form",
		fields=fields,
		filters=filters,
		or_filters=or_filters,
		order_by=order_by,
		limit_start=(page - 1) * page_size,
		limit_page_length=page_size,
	)

	option_filters = dict(filters)
	option_filters.pop("name_of_the_vo", None)
	option_filters.pop("name_of_the_shg", None)
	option_rows = frappe.get_all(
		"Nomination Form",
		fields=["name_of_the_vo", "name_of_the_shg"],
		filters=option_filters,
		or_filters=or_filters,
	)
	vos = sorted({row.name_of_the_vo for row in option_rows if row.name_of_the_vo})
	shgs = sorted({row.name_of_the_shg for row in option_rows if row.name_of_the_shg})

	return {
		"status": 1,
		"msg": {
			"rows": rows,
			"total": total,
			"page": page,
			"page_size": page_size,
			"vos": vos,
			"shgs": shgs,
		},
	}

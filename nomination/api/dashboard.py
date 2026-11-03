import re
from datetime import datetime
from zoneinfo import ZoneInfo

import frappe
from frappe.utils import get_fullname

from nomination.api.rangde_service import get_metrics, get_nominees

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
			"assessment_completed": metrics.get("completedAssessment")
			or (metrics.get("passed") or 0) + (metrics.get("failed") or 0),
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


TRAINING_STATUSES = ("registered", "training_completed", "passed", "failed")
LOAN_STATUSES = ("applied", "disbursed", "repaying")
# fully repaid loans stay in the Loan tab as Repaying (RangDe's data so far only has Applied/Disbursed)
COMPLETED_LOAN_STATUSES = ("closed", "repaid", "completed", "settled")
NOMINATION_STATUS_BY_WORKFLOW_STATE = {
	"SHG Proposed": "shg_approved",
	"VO Approved": "vo_approved",
	"CLF Approved": "clf_approved",
}
DIDI_TABS = ("all", "training", "loan")


def _mobile_key(value) -> str:
	"""RangDe stores 91XXXXXXXXXX, Nomination Form stores a plain number: match on the last 10 digits."""
	return re.sub(r"\D", "", str(value or ""))[-10:]


def _naive_datetime(value):
	"""Parse a timestamp into a naive datetime in the site timezone (RangDe sends offsets / Z)."""
	if not value:
		return None
	if not isinstance(value, datetime):
		text = str(value).strip()
		if text.endswith(("Z", "z")):
			text = f"{text[:-1]}+00:00"
		try:
			value = datetime.fromisoformat(text)
		except ValueError:
			return None
	if value.tzinfo is not None:
		value = value.astimezone(ZoneInfo(frappe.utils.get_system_timezone()))
	return value.replace(tzinfo=None)


def _iso(value) -> str | None:
	value = _naive_datetime(value)
	return value.isoformat() if value else None


def _training_status(nominee: dict) -> str:
	result = (nominee.get("taStatus") or "").strip().lower()
	if result in ("passed", "failed"):
		return result
	return "training_completed" if nominee.get("trainingCompletedDate") else "registered"


def _loan_status(nominee: dict) -> str | None:
	status = (nominee.get("lpStatus") or "").strip().lower()
	if status:
		# unknown values (Rejected, Closed, ...) are not one of the dashboard's loan stages
		if status in COMPLETED_LOAN_STATUSES:
			return "repaying"
		return status if status in LOAN_STATUSES else None
	# no lpStatus: infer from the loan dates
	if nominee.get("lastRepaymentDate"):
		return "repaying"
	if nominee.get("disbursalDate"):
		return "disbursed"
	if nominee.get("loanId"):
		return "applied"
	return None


def _didi_record(form: dict | None, nominee: dict | None, index: int = 0) -> dict:
	"""One didi, with her current stage/status (the furthest stage she has reached)."""
	training_status = _training_status(nominee) if nominee else None
	loan_status = _loan_status(nominee) if nominee else None
	nomination_status = NOMINATION_STATUS_BY_WORKFLOW_STATE.get(form.get("workflow_state")) if form else None

	if loan_status:
		stage, status = "loan", loan_status
	elif training_status:
		stage, status = "training", training_status
	else:
		stage, status = "nomination", nomination_status

	form = form or {}
	nominee = nominee or {}
	full_name = f"{form.get('first_name') or ''} {form.get('last_name') or ''}".strip()
	updated = [_naive_datetime(form.get("modified")), _naive_datetime(nominee.get("lastUpdated"))]
	updated = max((d for d in updated if d), default=None)
	created = _naive_datetime(form.get("creation")) or _naive_datetime(
		nominee.get("trainingRegistrationDate")
	)

	return {
		"key": form.get("name") or _mobile_key(nominee.get("mobileNumber")) or f"rangde-{index}",
		"name": full_name or nominee.get("name") or form.get("name"),
		"mobile": form.get("mobile_number") or nominee.get("mobileNumber"),
		"village": form.get("townvillage"),
		"shg": form.get("name_of_the_shg"),
		"vo": form.get("name_of_the_vo"),
		"photo": form.get("photo_of_didi"),
		"stage": stage,
		"status": status,
		"nomination_status": nomination_status,
		"training_status": training_status,
		"loan_status": loan_status,
		"nominated_on": _iso(form.get("creation")),
		"last_updated": updated.isoformat() if updated else None,
		"created": created.isoformat() if created else None,
		"registered_on": nominee.get("trainingRegistrationDate"),
		"training_completed_on": nominee.get("trainingCompletedDate"),
		"assessed_on": nominee.get("assessCompletedDate"),
		"requested_amount": nominee.get("requestedLoanAmount"),
		"disbursed_amount": nominee.get("loanAmount") if loan_status in ("disbursed", "repaying") else None,
		"disbursed_on": nominee.get("disbursalDate"),
		"repaid_so_far": nominee.get("repaidSoFar"),
		"last_repayment_on": nominee.get("lastRepaymentDate"),
	}


@frappe.whitelist()
def get_dashboard_didi_rows(
	tab="all", statuses=None, vo=None, shg=None, search=None, sort_by="modified", refresh=0
):
	"""Unified didi list across Nomination Form (local) and the RangDe nominee list (training/loan)."""
	owners = _nomination_owner_scope_for_session()
	if tab not in DIDI_TABS:
		frappe.throw(frappe._("Invalid dashboard tab selected."))

	nominees = get_nominees(force=bool(int(refresh or 0)))
	if nominees is None:
		frappe.throw(frappe._("Unable to load nominees from RangDe."))
	nominee_by_mobile, nominees_without_mobile = {}, []
	for nominee in nominees:
		key = _mobile_key(nominee.get("mobileNumber"))
		if not key:
			nominees_without_mobile.append(nominee)
			continue
		existing = nominee_by_mobile.get(key)
		# RangDe returns one row per loan, so a person can repeat; keep her latest row
		if existing and (nominee.get("lastUpdated") or "") <= (existing.get("lastUpdated") or ""):
			continue
		nominee_by_mobile[key] = nominee

	# only the active nomination stages, like the existing list endpoints
	form_filters = {"workflow_state": ["in", list(NOMINATION_STATUS_BY_WORKFLOW_STATE)]}
	if owners is not None:
		if not owners:
			return {"status": 1, "msg": {"rows": [], "total": 0, "vos": [], "shgs": []}}
		form_filters["owner"] = ["in", list(owners)]
	forms = frappe.get_all(
		"Nomination Form",
		fields=[
			"name",
			"first_name",
			"last_name",
			"townvillage",
			"name_of_the_shg",
			"name_of_the_vo",
			"workflow_state",
			"mobile_number",
			"photo_of_didi",
			"creation",
			"modified",
		],
		filters=form_filters,
		# oldest form wins when several share a mobile number
		order_by="creation asc",
	)

	records, matched = [], set()
	for form in forms:
		key = _mobile_key(form.mobile_number)
		nominee = nominee_by_mobile.get(key) if key else None
		if nominee and key in matched:
			# a second form with the same number must not attach to the same nominee
			frappe.logger("nomination").warning(f"Mobile {key} is on multiple Nomination Forms")
			nominee = None
		elif nominee:
			matched.add(key)
		records.append(_didi_record(form, nominee))
	if owners is None:
		# RangDe-only didis (no local Nomination Form) are visible to users who see everything
		rangde_only = [n for k, n in nominee_by_mobile.items() if k not in matched]
		rangde_only += nominees_without_mobile
		records += [_didi_record(None, n, index) for index, n in enumerate(rangde_only)]

	if tab == "training":
		records = [r for r in records if r["training_status"]]
		for r in records:
			r["stage"], r["status"] = "training", r["training_status"]
	elif tab == "loan":
		records = [r for r in records if r["loan_status"]]
		for r in records:
			r["stage"], r["status"] = "loan", r["loan_status"]

	status_values = set(_as_filter_values(statuses))
	if status_values:
		records = [r for r in records if r["status"] in status_values]

	search = (search or "").strip().lower()
	if search:
		records = [
			r
			for r in records
			if search in (r["name"] or "").lower()
			or search in (r["village"] or "").lower()
			or search in str(r["mobile"] or "")
		]

	vo_values, shg_values = _as_filter_values(vo), _as_filter_values(shg)
	vos = sorted({r["vo"] for r in records if r["vo"]})
	shgs = sorted({r["shg"] for r in records if r["shg"]})
	if vo_values:
		records = [r for r in records if r["vo"] in vo_values]
	if shg_values:
		records = [r for r in records if r["shg"] in shg_values]

	sort_field = "created" if sort_by == "created" else "last_updated"
	records.sort(key=lambda r: r[sort_field] or "", reverse=True)

	return {"status": 1, "msg": {"rows": records, "total": len(records), "vos": vos, "shgs": shgs}}

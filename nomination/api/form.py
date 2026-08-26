import json

import frappe
from frappe.model.workflow import apply_workflow
from frappe.utils import cint, flt

from .credit_report import generate_credit_report
from .didi_photo import save_didi_photo
from .leader_approval import (
	DEFAULT_LEVEL,
	LEADER_ROLES,
	MIN_APPROVALS,
	clear_approvals,
	get_approved_leaders,
)
from .validation import validate_aadhaar_number, validate_date_of_birth, validate_pan_number

APPROVERS_TABLE = "table_nmzc"

# the SHG submits, the VO reviews it next, and the CLF reviews after that, so the
# state a nomination is sitting in says whose leaders have to approve to move it on
STATE_APPROVAL_LEVEL = {
	"SHG Proposed": "VO",
	"VO Approved": "CLF",
}


@frappe.whitelist()
def validate_aadhaar(aadhaar_number):
	try:
		validate_aadhaar_number(aadhaar_number)
		frappe.session.data["aadhaar_validated"] = aadhaar_number
		return {"status": 1, "msg": "Valid Aadhaar"}
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Aadhaar Validation Error")
		frappe.session.data["aadhaar_validated"] = None
		return {"status": 0, "msg": "Invalid Aadhaar Number"}


@frappe.whitelist()
def validate_pan(pan_number):
	try:
		validate_pan_number(pan_number)
		return {"status": 1, "msg": "Valid PAN"}
	except Exception:
		frappe.log_error(frappe.get_traceback(), "PAN Validation Error")
		return {"status": 0, "msg": "Invalid PAN Number"}


@frappe.whitelist()
def validate_dob(dob):
	try:
		validate_date_of_birth(dob)
		return {"status": 1, "msg": "Valid DOB"}
	except Exception:
		frappe.log_error(frappe.get_traceback(), "DOB Validation Error")
		return {"status": 0, "msg": "Invalid Date of Birth"}


def mask_aadhaar(aadhaar):
	if not aadhaar or len(aadhaar) < 4:
		return aadhaar
	digits = aadhaar[-4:]
	return f"xxxx-xxxx-{digits}"


def mask_pan(pan):
	if not pan or len(pan) <= 5:
		return pan
	value = pan[:5]
	masked = "X" * (len(pan) - 5)
	return f"{value}{masked}"


@frappe.whitelist()
def get_nomination_form(name):
	if not frappe.db.exists("Nomination Form", name):
		return {"status": 0, "msg": "Document not found"}
	nomi_doc = frappe.get_doc("Nomination Form", name)

	data = nomi_doc.as_dict()
	data["approved_leaders"] = get_doc_approved_leaders(nomi_doc)

	if data.get("aadhaar_number"):
		data["aadhaar_number"] = mask_aadhaar(data["aadhaar_number"])

	if data.get("pan_number"):
		data["pan_number"] = mask_pan(data["pan_number"])

	return {"status": 1, "msg": [data]}


def add_approver_rows(doc, approved_leaders):
	"""Write the approving leaders straight into the shared approvers table.

	The rows have to be on disk before apply_workflow runs, because it reloads the
	document and drops anything unsaved. Saving the parent instead would re-run
	validate, and set_approval_log stamps the current state's approver on every
	save, which would overwrite whoever actually approved the previous stage.
	"""
	idx = len(doc.get(APPROVERS_TABLE) or [])

	for leader in approved_leaders:
		idx += 1
		frappe.get_doc(
			{
				"doctype": "Leaders Details",
				"parent": doc.name,
				"parenttype": doc.doctype,
				"parentfield": APPROVERS_TABLE,
				"idx": idx,
				"name1": leader["label"],
				"mobile_number": f"+91- {leader['mobile_number']}",
				"verified_on": leader.get("verified_on"),
			}
		).insert(ignore_permissions=True)


def _role_from_approval_label(label, level=DEFAULT_LEVEL):
	prefix = f"{level}-"
	if not label or not str(label).startswith(prefix):
		return None

	role_label = str(label)[len(prefix) :].strip().lower()
	for role in LEADER_ROLES:
		if role_label == role:
			return role
	return None


def get_doc_approved_leaders(doc, level=DEFAULT_LEVEL):
	leaders = []
	for row in doc.get(APPROVERS_TABLE) or []:
		role = _role_from_approval_label(row.name1, level)
		if not role:
			continue
		leaders.append(
			{
				"role": role,
				"level": level,
				"label": row.name1,
				"mobile_number": "".join(ch for ch in str(row.mobile_number or "") if ch.isdigit())[-10:],
				"verified_on": row.verified_on,
			}
		)
	return leaders


def set_doc_approver_rows(doc, approved_leaders, level=DEFAULT_LEVEL):
	prefix = f"{level}-"
	other_rows = [
		row for row in doc.get(APPROVERS_TABLE) or [] if not str(row.name1 or "").startswith(prefix)
	]
	doc.set(APPROVERS_TABLE, other_rows)

	for leader in approved_leaders:
		doc.append(
			APPROVERS_TABLE,
			{
				"name1": leader["label"],
				"mobile_number": f"+91- {leader['mobile_number']}",
				"verified_on": leader.get("verified_on"),
			},
		)

	for role in LEADER_ROLES:
		setattr(doc, f"{role}_approved", 0)
	for leader in approved_leaders:
		setattr(doc, f"{leader['role']}_approved", 1)


def clear_doc_approvals(doc, level=DEFAULT_LEVEL):
	set_doc_approver_rows(doc, [], level)
	clear_approvals(level, doc.name)


def _clean_mobile(value):
	return "".join(ch for ch in str(value or "") if ch.isdigit())[-10:]


def _payload_business_category(payload):
	business_category = payload.get("business_category")
	if business_category == "other":
		return payload.get("business_category_other") or business_category
	return business_category


def _payload_values(payload):
	sector = payload.get("sector")
	return {
		"first_name": payload.get("first_name"),
		"last_name": payload.get("last_name"),
		"pincode": payload.get("pincode"),
		"district": payload.get("district"),
		"townvillage": payload.get("townvillage"),
		"permanent_address": payload.get("permanent_address"),
		"aadhaar_number": payload.get("aadhaar_number"),
		"pan_number": payload.get("pan_number"),
		"voter_id": payload.get("voter_id"),
		"date_of_birth": payload.get("date_of_birth"),
		"mobile_number": _clean_mobile(payload.get("mobile_number")),
		"name_of_the_vo": payload.get("vo_name"),
		"name_of_the_shg": payload.get("shg_name"),
		"year_of_joining_shg": payload.get("year_of_joining_shg"),
		"attendance_in_last_12_meetings": map_option(
			ATTENDANCE_MAP, payload.get("attendance_last_12_meetings")
		),
		"repayment_record": map_option(REPAYMENT_MAP, payload.get("repayment_record")),
		"total_savings_in_shg": flt(payload.get("total_savings")),
		"business_category": _payload_business_category(payload),
		"years_of_experience": map_option(EXPERIENCE_MAP, payload.get("years_of_experience")),
		"number_of_business": map_option(BUSINESS_COUNT_MAP, payload.get("number_of_businesses")),
		"family_support_in_enterprise": map_option(FAMILY_SUPPORT_MAP, payload.get("family_support")),
		"credit_score": cint(payload.get("credit_score")),
		"set_credit_limit": str(payload.get("set_credit_limit") or ""),
		"farm_based": 1 if sector == "farm_based" else 0,
		"non_farm": 0 if sector == "farm_based" else 1,
		"market_access": 1 if "market_access" in payload.get("supportNeeded", []) else 0,
		"marketing": 1 if "marketing" in payload.get("supportNeeded", []) else 0,
		"demand_assessment": 1 if "demand_assessment" in payload.get("supportNeeded", []) else 0,
		"none": 1 if "none" in payload.get("supportNeeded", []) else 0,
		"hushband": 1 if "husband" in payload.get("business_helpers", []) else 0,
		"children": 1 if "children" in payload.get("business_helpers", []) else 0,
		"in_laws": 1 if "in_laws" in payload.get("business_helpers", []) else 0,
		"no_one": 1 if "none" in payload.get("business_helpers", []) else 0,
	}


def _doc_values(doc):
	return {
		"first_name": doc.get("first_name"),
		"last_name": doc.get("last_name"),
		"pincode": doc.get("pincode"),
		"district": doc.get("district"),
		"townvillage": doc.get("townvillage"),
		"permanent_address": doc.get("permanent_address"),
		"aadhaar_number": doc.get("aadhaar_number"),
		"pan_number": doc.get("pan_number"),
		"voter_id": doc.get("voter_id"),
		"date_of_birth": str(doc.get("date_of_birth") or ""),
		"mobile_number": _clean_mobile(doc.get("mobile_number")),
		"name_of_the_vo": doc.get("name_of_the_vo"),
		"name_of_the_shg": doc.get("name_of_the_shg"),
		"year_of_joining_shg": doc.get("year_of_joining_shg"),
		"attendance_in_last_12_meetings": doc.get("attendance_in_last_12_meetings"),
		"repayment_record": doc.get("repayment_record"),
		"total_savings_in_shg": flt(doc.get("total_savings_in_shg")),
		"business_category": doc.get("business_category"),
		"years_of_experience": doc.get("years_of_experience"),
		"number_of_business": doc.get("number_of_business"),
		"family_support_in_enterprise": doc.get("family_support_in_enterprise"),
		"credit_score": cint(doc.get("credit_score")),
		"set_credit_limit": str(doc.get("set_credit_limit") or ""),
		"farm_based": cint(doc.get("farm_based")),
		"non_farm": cint(doc.get("non_farm")),
		"market_access": cint(doc.get("market_access")),
		"marketing": cint(doc.get("marketing")),
		"demand_assessment": cint(doc.get("demand_assessment")),
		"none": cint(doc.get("none")),
		"hushband": cint(doc.get("hushband")),
		"children": cint(doc.get("children")),
		"in_laws": cint(doc.get("in_laws")),
		"no_one": cint(doc.get("no_one")),
	}


def _set_nomination_values(doc, payload):
	values = _payload_values(payload)
	for fieldname, value in values.items():
		if fieldname == "mobile_number":
			value = f"+91- {value}" if value else ""
		doc.set(fieldname, value)


def _payload_changed(doc, payload):
	photo = str(payload.get("photo_of_didi") or "")
	photo_changed = bool(photo and photo != str(doc.get("photo_of_didi") or ""))
	return _doc_values(doc) != _payload_values(payload) or photo_changed


def _parse_payload(payload):
	if isinstance(payload, str):
		return json.loads(payload)
	return payload or {}


def _can_update_draft(doc):
	roles = set(frappe.get_roles(frappe.session.user))
	return doc.owner == frappe.session.user or "System Manager" in roles


def _get_owned_draft(name=None):
	filters = {"workflow_state": "Draft"}
	if name:
		filters["name"] = name
	else:
		filters["owner"] = frappe.session.user

	draft_name = frappe.db.get_value(
		"Nomination Form",
		filters,
		"name",
		order_by="modified desc",
	)
	if not draft_name:
		return None

	doc = frappe.get_doc("Nomination Form", draft_name)
	if not _can_update_draft(doc):
		return None

	return doc


def _get_owned_nomination(name):
	if not name or not frappe.db.exists("Nomination Form", name):
		return None

	doc = frappe.get_doc("Nomination Form", name)
	if not _can_update_draft(doc):
		return None

	return doc


def _save_nomination_attachments(doc, payload):
	report_base64 = payload.get("reportBase64")
	if report_base64:
		generate_credit_report(doc.name, report_base64)

	save_didi_photo(doc.name, payload.get("photo_of_didi"))


def _draft_response(doc, approvals_cleared=False):
	return {
		"name": doc.name,
		"photo_of_didi": doc.get("photo_of_didi"),
		"approvals_cleared": approvals_cleared,
		"approved_leaders": get_doc_approved_leaders(doc),
	}


@frappe.whitelist()
def approve_form(name, credit_limit):
	if not frappe.db.exists("Nomination Form", name):
		return {"status": 0, "msg": "Document not found"}

	try:
		user_roles = frappe.get_roles(frappe.session.user)
		if "SHG" in user_roles and "CLF" not in user_roles and "System Manager" not in user_roles:
			frappe.throw("Not permitted to approve nominations", frappe.PermissionError)

		nomi_doc = frappe.get_doc("Nomination Form", name)
		current_state = nomi_doc.workflow_state

		if current_state == "Draft":
			action = "Send to VO"
		elif current_state == "SHG Proposed":
			action = "Send to CLF"
		elif current_state == "VO Approved":
			action = "Approve"
		else:
			return {"status": 0, "msg": "Not a valid Workflow Action"}

		level = STATE_APPROVAL_LEVEL.get(current_state)

		# trust only the OTP verifications recorded server side, never the payload
		approved_leaders = get_approved_leaders(level, name) if level else []
		if level and len(approved_leaders) < MIN_APPROVALS:
			return {
				"status": 0,
				"msg": f"Any {MIN_APPROVALS} of {len(LEADER_ROLES)} {level} leaders must approve via OTP",
			}

		new_credit_limit = flt(credit_limit)
		if nomi_doc.set_credit_limit != new_credit_limit:
			frappe.db.set_value(nomi_doc.doctype, nomi_doc.name, "set_credit_limit", credit_limit)
			frappe.log_error(
				f"Credit limit changed to {credit_limit} for {name} "
				f"by {frappe.session.user} from state {current_state}",
				"Credit Limit Audit",
			)
			nomi_doc.reload()

		add_approver_rows(nomi_doc, approved_leaders)

		apply_workflow(nomi_doc, action)

		# the cached approvals are spent once they are on the document
		if level:
			clear_approvals(level, name)

		return {"status": 1, "msg": f"{name} Document has been moved to next workflow state"}

	except frappe.PermissionError:
		raise
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Approve Form Error")
		return {"status": 0, "msg": "An error occurred while approving the form. Please try again later."}


ATTENDANCE_MAP = {
	"10_or_more": "10 or more",
	"7_to_9": "7 to 9",
	"fewer_than_7": "fewer than 7",
}

REPAYMENT_MAP = {
	"always_on_time": "Always on time",
	"mostly_on_time": "Mostly on time",
	"has_delayed": "Has delayed",
}

EXPERIENCE_MAP = {
	"below_1": "Under 1 year",
	"1_to_2": "1 to 2 years",
	"3_to_5": "3 to 5 years",
	"above_5": "Over 5 years",
}

BUSINESS_COUNT_MAP = {
	"1": "1",
	"2": "2",
	"3_or_more": "3 or more",
}

FAMILY_SUPPORT_MAP = {
	"yes": "Yes",
	"partially": "Partially",
	"no": "No",
}

# who helps in business or finances -> doctype checkboxes
HELPER_FIELD_MAP = {
	"husband": "hushband",
	"children": "children",
	"in_laws": "in_laws",
	"none": "no_one",
}


def map_option(mapping, value):
	"""Translate a web form slug to its doctype Select value."""
	if not value:
		return None
	return mapping.get(value, value)


@frappe.whitelist()
def submit_nomination(payload):
	if frappe.session.user == "Guest":
		return {"status": 0, "msg": "Not logged in"}

	payload = _parse_payload(payload)
	requested_name = payload.get("draft_name") or payload.get("name")
	doc = _get_owned_draft(requested_name)
	if not doc:
		existing_doc = _get_owned_nomination(requested_name)
		if existing_doc and existing_doc.workflow_state != "Draft":
			return {"status": 1, "msg": existing_doc.name}

	is_new = doc is None

	if is_new:
		doc = frappe.new_doc("Nomination Form")
	elif _payload_changed(doc, payload):
		clear_doc_approvals(doc)

	_set_nomination_values(doc, payload)

	cache_approvals = get_approved_leaders(DEFAULT_LEVEL, doc.name)
	existing_approvals = get_doc_approved_leaders(doc)
	approvals_by_role = {leader["role"]: leader for leader in existing_approvals}
	for leader in cache_approvals:
		approvals_by_role[leader["role"]] = leader

	approved_leaders = list(approvals_by_role.values())
	if len(approved_leaders) < MIN_APPROVALS:
		return {
			"status": 0,
			"msg": f"Any {MIN_APPROVALS} of {len(LEADER_ROLES)} SHG leaders must approve via OTP",
		}

	set_doc_approver_rows(doc, approved_leaders)

	if is_new:
		doc.insert(ignore_permissions=True)
	else:
		doc.save(ignore_permissions=True)
	apply_workflow(doc, "Send to VO")

	_save_nomination_attachments(doc, payload)

	clear_approvals(DEFAULT_LEVEL, doc.name)

	return {"status": 1, "msg": doc.name}


@frappe.whitelist()
def save_nomination_draft(payload):
	if frappe.session.user == "Guest":
		return {"status": 0, "msg": "Not logged in"}

	payload = _parse_payload(payload)
	requested_name = payload.get("draft_name") or payload.get("name")
	doc = _get_owned_draft(requested_name)
	if not doc:
		existing_doc = _get_owned_nomination(requested_name)
		if existing_doc and existing_doc.workflow_state != "Draft":
			return {"status": 1, "msg": _draft_response(existing_doc)}

	is_new = doc is None
	approvals_cleared = False

	if is_new:
		doc = frappe.new_doc("Nomination Form")
	elif _payload_changed(doc, payload):
		clear_doc_approvals(doc)
		approvals_cleared = True

	_set_nomination_values(doc, payload)

	if is_new:
		doc.insert(ignore_permissions=True)
	else:
		doc.save(ignore_permissions=True)

	_save_nomination_attachments(doc, payload)
	doc.reload()

	return {"status": 1, "msg": _draft_response(doc, approvals_cleared)}


@frappe.whitelist()
def get_nomination_draft(name=None):
	if frappe.session.user == "Guest":
		return {"status": 0, "msg": "Not logged in"}

	doc = _get_owned_draft(name)
	if not doc:
		return {"status": 0, "msg": "Draft not found"}

	data = doc.as_dict()
	data["approved_leaders"] = get_doc_approved_leaders(doc)

	return {"status": 1, "msg": [data]}

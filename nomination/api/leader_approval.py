import json

import frappe
from frappe.utils import now

from nomination.api.login import send_otp_internal, verify_otp_internal
from nomination.api.rangde_service import strip_country_code

LEADER_ROLES = ("president", "secretary", "treasurer")

# the same three roles approve at each stage of the workflow
LEADER_LEVELS = ("SHG", "VO", "CLF")

DEFAULT_LEVEL = "SHG"

MIN_APPROVALS = 2

# a leader approval stays valid long enough to finish the credit step and submit
APPROVAL_TTL_SEC = 3600


def _clean_role(role):
	role = (role or "").strip().lower()
	return role if role in LEADER_ROLES else None


def _clean_level(level):
	level = (level or DEFAULT_LEVEL).strip().upper()
	return level if level in LEADER_LEVELS else None


def _scope_name(nomination_name):
	return (nomination_name or "").strip() or "__unsaved__"


def _number_key(level, role, nomination_name=None):
	return f"leader_otp_number_{frappe.session.user}_{_scope_name(nomination_name)}_{level}_{role}"


def _approved_key(level, role, nomination_name=None):
	return f"leader_otp_approved_{frappe.session.user}_{_scope_name(nomination_name)}_{level}_{role}"


def _can_update_nomination(doc):
	roles = set(frappe.get_roles(frappe.session.user))
	return doc.owner == frappe.session.user or "System Manager" in roles


def _can_record_approval(doc, level):
	roles = set(frappe.get_roles(frappe.session.user))
	if "System Manager" in roles:
		return True
	if level == DEFAULT_LEVEL:
		return doc.owner == frappe.session.user
	return level in roles


def _duplicate_role(level, role, mobile_number, nomination_name=None):
	"""Return the other role at this level already using this number, if any."""
	for other in LEADER_ROLES:
		if other == role:
			continue
		if frappe.cache().get_value(_number_key(level, other, nomination_name)) == mobile_number:
			return other
	return None


ROLE_LABELS = {
	"president": "President",
	"secretary": "Secretary",
	"treasurer": "Treasurer",
}


def _read_approval(level, role, nomination_name=None):
	"""Return the stored approval as a dict, tolerating an older bare number."""
	raw = frappe.cache().get_value(_approved_key(level, role, nomination_name))
	if not raw:
		return None

	if isinstance(raw, dict):
		return raw

	try:
		parsed = json.loads(raw)
	except (TypeError, ValueError):
		return {"mobile_number": raw, "verified_on": None}

	if isinstance(parsed, dict):
		return parsed

	return {"mobile_number": raw, "verified_on": None}


def get_approved_roles(level=DEFAULT_LEVEL, nomination_name=None):
	"""Roles that completed OTP verification at this level in this session."""
	level = _clean_level(level) or DEFAULT_LEVEL
	return [role for role in LEADER_ROLES if _read_approval(level, role, nomination_name)]


def get_approved_leaders(level=DEFAULT_LEVEL, nomination_name=None):
	"""Verified roles with the mobile number each one approved from."""
	level = _clean_level(level) or DEFAULT_LEVEL
	leaders = []

	for role in LEADER_ROLES:
		approval = _read_approval(level, role, nomination_name)
		if not approval:
			continue

		role_label = ROLE_LABELS.get(role, role.title())

		leaders.append(
			{
				"role": role,
				"level": level,
				# the approvers table is shared across SHG, VO and CLF
				"label": f"{level}-{role_label}",
				"mobile_number": approval.get("mobile_number"),
				"verified_on": approval.get("verified_on"),
			}
		)

	return leaders


APPROVAL_WORKFLOW_STATE = {
	"SHG": "Draft",
	"VO": "SHG Proposed",
	"CLF": "VO Approved",
}


def record_leader_approval(nomination_name, level, role, mobile_number, verified_on):
	if not nomination_name:
		return

	level = _clean_level(level)
	role = _clean_role(role)
	if not level or not role:
		return

	if not frappe.db.exists("Nomination Form", nomination_name):
		return

	doc = frappe.get_doc("Nomination Form", nomination_name)
	if doc.workflow_state != APPROVAL_WORKFLOW_STATE.get(level) or not _can_record_approval(doc, level):
		return

	role_label = ROLE_LABELS.get(role, role.title())
	label = f"{level}-{role_label}"
	mobile_number = strip_country_code(mobile_number)

	doc.set(
		"table_nmzc",
		[row for row in doc.get("table_nmzc") or [] if row.name1 != label],
	)
	doc.append(
		"table_nmzc",
		{
			"name1": label,
			"mobile_number": f"+91- {mobile_number}",
			"verified_on": verified_on,
		},
	)
	setattr(doc, f"{role}_approved", 1)
	doc.save(ignore_permissions=True)


def clear_approvals(level=DEFAULT_LEVEL, nomination_name=None):
	level = _clean_level(level) or DEFAULT_LEVEL
	for role in LEADER_ROLES:
		frappe.cache().delete_value(_number_key(level, role, nomination_name))
		frappe.cache().delete_value(_approved_key(level, role, nomination_name))


@frappe.whitelist()
def send_leader_otp(mobile_number, role, level=DEFAULT_LEVEL, nomination_name=None):
	if frappe.session.user == "Guest":
		return {"status": 0, "msg": "Not logged in"}

	role = _clean_role(role)
	if not role:
		return {"status": 0, "msg": "Invalid leader role"}

	level = _clean_level(level)
	if not level:
		return {"status": 0, "msg": "Invalid approval level"}

	mobile_number = strip_country_code(mobile_number)
	if not mobile_number:
		return {"status": 0, "msg": "Please enter a valid 10-digit mobile number"}

	duplicate = _duplicate_role(level, role, mobile_number, nomination_name)
	if duplicate:
		return {
			"status": 0,
			"msg": f"This number is already used for the {duplicate.title()}. "
			"Each leader needs a different mobile number",
		}

	frappe.cache().set_value(
		_number_key(level, role, nomination_name), mobile_number, expires_in_sec=APPROVAL_TTL_SEC
	)
	frappe.cache().delete_value(_approved_key(level, role, nomination_name))

	send_otp_internal(mobile_number)

	return {"status": 1, "msg": "OTP sent successfully"}


@frappe.whitelist()
def verify_leader_otp(mobile_number, otp, role, level=DEFAULT_LEVEL, nomination_name=None):
	if frappe.session.user == "Guest":
		return {"status": 0, "msg": "Not logged in"}

	role = _clean_role(role)
	if not role:
		return {"status": 0, "msg": "Invalid leader role"}

	level = _clean_level(level)
	if not level:
		return {"status": 0, "msg": "Invalid approval level"}

	mobile_number = strip_country_code(mobile_number)
	if not mobile_number:
		return {"status": 0, "msg": "Please enter a valid 10-digit mobile number"}

	if frappe.cache().get_value(_number_key(level, role, nomination_name)) != mobile_number:
		return {"status": 0, "msg": "Please request an OTP for this number first"}

	duplicate = _duplicate_role(level, role, mobile_number, nomination_name)
	if duplicate:
		return {
			"status": 0,
			"msg": f"This number is already used for the {duplicate.title()}. "
			"Each leader needs a different mobile number",
		}

	result = verify_otp_internal(mobile_number, otp)
	messages = result.get("messages", [])

	if not messages or messages[0].get("code") != "1":
		frappe.log_error(
			f"Invalid leader OTP for {level}-{role} on mobile number {mobile_number}. Response: {result}",
			"Leader OTP Verification Failed",
		)
		frappe.response.http_status_code = 417
		frappe.cache().delete_value(_approved_key(level, role))
		return {"status": 0, "msg": "Incorrect OTP, please enter the correct OTP"}

	# the timestamp is taken here so a wrong device clock cannot stamp an approval
	verified_on = now()

	frappe.cache().set_value(
		_approved_key(level, role, nomination_name),
		json.dumps({"mobile_number": mobile_number, "verified_on": verified_on}),
		expires_in_sec=APPROVAL_TTL_SEC,
	)

	record_leader_approval(nomination_name, level, role, mobile_number, verified_on)

	return {
		"status": 1,
		"msg": "OTP verified successfully",
		"verified_on": verified_on,
		"approved_leaders": get_approved_leaders(level, nomination_name),
	}


@frappe.whitelist()
def get_leader_approvals(level=DEFAULT_LEVEL, nomination_name=None):
	if frappe.session.user == "Guest":
		return {"status": 0, "msg": "Not logged in"}

	level = _clean_level(level)
	if not level:
		return {"status": 0, "msg": "Invalid approval level"}

	return {"status": 1, "msg": get_approved_leaders(level, nomination_name)}

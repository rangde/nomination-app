import json

import frappe
from frappe.model.workflow import apply_workflow
from frappe.utils import cint, flt

from .credit_report import generate_credit_report
from .didi_photo import save_didi_photo
from .leader_approval import (
	LEADER_ROLES,
	MIN_APPROVALS,
	clear_approvals,
	get_approved_leaders,
)
from .validation import validate_aadhaar_number, validate_date_of_birth, validate_pan_number

APPROVERS_TABLE = "table_nmzc"


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

	if data.get("aadhaar_number"):
		data["aadhaar_number"] = mask_aadhaar(data["aadhaar_number"])

	if data.get("pan_number"):
		data["pan_number"] = mask_pan(data["pan_number"])

	return {"status": 1, "msg": [data]}


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

		new_credit_limit = flt(credit_limit)
		if nomi_doc.set_credit_limit != new_credit_limit:
			frappe.db.set_value(nomi_doc.doctype, nomi_doc.name, "set_credit_limit", credit_limit)
			frappe.log_error(
				f"Credit limit changed to {credit_limit} for {name} "
				f"by {frappe.session.user} from state {current_state}",
				"Credit Limit Audit",
			)
			nomi_doc.reload()

		apply_workflow(nomi_doc, action)

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

	if isinstance(payload, str):
		payload = json.loads(payload)

	doc = frappe.new_doc("Nomination Form")

	doc.first_name = payload.get("first_name")
	doc.last_name = payload.get("last_name")
	doc.pincode = payload.get("pincode")
	doc.district = payload.get("district")
	doc.townvillage = payload.get("townvillage")
	doc.permanent_address = payload.get("permanent_address")
	doc.aadhaar_number = payload.get("aadhaar_number")
	doc.pan_number = payload.get("pan_number")
	doc.voter_id = payload.get("voter_id")
	doc.date_of_birth = payload.get("date_of_birth")
	business_category = payload.get("business_category")
	if business_category == "other":
		business_category = payload.get("business_category_other") or business_category
	doc.business_category = business_category
	doc.mobile_number = f"+91- {payload.get('mobile_number')}"

	doc.name_of_the_vo = payload.get("vo_name")
	doc.name_of_the_shg = payload.get("shg_name")
	doc.year_of_joining_shg = payload.get("year_of_joining_shg")
	doc.attendance_in_last_12_meetings = map_option(
		ATTENDANCE_MAP, payload.get("attendance_last_12_meetings")
	)
	doc.repayment_record = map_option(REPAYMENT_MAP, payload.get("repayment_record"))
	doc.total_savings_in_shg = flt(payload.get("total_savings"))

	doc.years_of_experience = map_option(EXPERIENCE_MAP, payload.get("years_of_experience"))
	doc.number_of_business = map_option(BUSINESS_COUNT_MAP, payload.get("number_of_businesses"))
	doc.family_support_in_enterprise = map_option(FAMILY_SUPPORT_MAP, payload.get("family_support"))

	doc.credit_score = cint(payload.get("credit_score"))
	doc.set_credit_limit = payload.get("set_credit_limit")

	sector = payload.get("sector")

	if sector == "farm_based":
		doc.farm_based = 1
		doc.non_farm = 0
	else:
		doc.farm_based = 0
		doc.non_farm = 1

	support_needed = payload.get("supportNeeded", [])
	for item in support_needed:
		if hasattr(doc, item):
			setattr(doc, item, 1)

	business_helpers = payload.get("business_helpers", [])
	for helper in business_helpers:
		fieldname = HELPER_FIELD_MAP.get(helper)
		if fieldname and hasattr(doc, fieldname):
			setattr(doc, fieldname, 1)

	# trust only the OTP verifications recorded server side, never the payload
	approved_leaders = get_approved_leaders()
	if len(approved_leaders) < MIN_APPROVALS:
		return {
			"status": 0,
			"msg": f"Any {MIN_APPROVALS} of {len(LEADER_ROLES)} SHG leaders must approve via OTP",
		}

	for leader in approved_leaders:
		setattr(doc, f"{leader['role']}_approved", 1)

		doc.append(
			APPROVERS_TABLE,
			{
				"name1": leader["label"],
				"mobile_number": f"+91- {leader['mobile_number']}",
				"verified_on": leader.get("verified_on"),
			},
		)

	doc.insert(ignore_permissions=True)
	apply_workflow(doc, "Send to VO")

	report_base64 = payload.get("reportBase64")
	if report_base64:
		generate_credit_report(doc.name, report_base64)

	save_didi_photo(doc.name, payload.get("photo_of_didi"))

	clear_approvals()

	return {"status": 1, "msg": doc.name}

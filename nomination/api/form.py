import json

import frappe
from frappe.model.workflow import apply_workflow
from frappe.utils import cint, flt

from .validation import validate_aadhaar_number, validate_date_of_birth, validate_pan_number


@frappe.whitelist()
def validate_aadhaar(aadhaar_number):
	try:
		validate_aadhaar_number(aadhaar_number)
		return {"status": 1, "msg": "Valid Aadhaar"}
	except Exception as e:
		return {"status": 0, "msg": str(e)}


@frappe.whitelist()
def validate_pan(pan_number):
	try:
		validate_pan_number(pan_number)
		return {"status": 1, "msg": "Valid PAN"}
	except Exception as e:
		return {"status": 0, "msg": str(e)}


@frappe.whitelist()
def validate_dob(dob):
	try:
		validate_date_of_birth(dob)
		return {"status": 1, "msg": "Valid DOB"}
	except Exception as e:
		return {"status": 0, "msg": str(e)}


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
		nomi_doc = frappe.get_doc("Nomination Form", name)
		new_credit_limit = flt(credit_limit)
		if nomi_doc.set_credit_limit != new_credit_limit:
			frappe.db.set_value(nomi_doc.doctype, nomi_doc.name, "set_credit_limit", credit_limit)
			nomi_doc.reload()

		current_state = nomi_doc.workflow_state

		if current_state == "Draft":
			action = "Send to VO"

		elif current_state == "SHG Proposed":
			action = "Send to CLF"

		elif current_state == "VO Approved":
			action = "Approve"

		else:
			return {"status": 0, "msg": f"No workflow action available from state {current_state}"}

		apply_workflow(nomi_doc, action)

		return {"status": 1, "msg": f"{name} Document has been moved to next workflow state"}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Approve Form Error")
		return {"status": 0, "msg": str(e)}


@frappe.whitelist()
def submit_nomination(payload):
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
	doc.date_of_birth = payload.get("date_of_birth")
	doc.business_category = payload.get("business_category")
	doc.mobile_number = f"+91- {payload.get('mobile_number')}"

	doc.credit_score = cint(payload.get("credit_score"))
	doc.set_credit_limit = payload.get("set_credit_limit")

	sector = payload.get("sector")

	if sector == "farm_based":
		doc.farm_based = 1
		doc.non_farm_based = 0
	else:
		doc.farm_based = 0
		doc.non_farm_based = 1

	support_needed = payload.get("supportNeeded", [])
	for item in support_needed:
		if hasattr(doc, item):
			setattr(doc, item, 1)

	doc.insert(ignore_permissions=True)
	apply_workflow(doc, "Send to VO")

	return {"status": 1, "msg": doc.name}

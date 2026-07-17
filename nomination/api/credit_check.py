import frappe
from frappe.utils import formatdate

from nomination.api.rangde_service import (
	add_country_code,
	credit_check,
	strip_country_code,
)
from nomination.api.state_code import get_state_code


@frappe.whitelist()
def credit_score(**kwargs):
	if frappe.session.user == "Guest":
		return {"status": 0, "msg": "Not logged in"}

	mobile = strip_country_code(kwargs.get("mobile_number"))
	if not mobile:
		return {"status": 0, "msg": "Please enter a valid 10-digit mobile number"}

	verified = frappe.cache().get_value(f"otp_verified_{mobile}")
	if not verified:
		return {"status": 0, "msg": "OTP verification required"}

	frappe.cache().delete_value(f"otp_verified_{mobile}")

	try:
		dob = formatdate(kwargs.get("dob"), "dd-MM-yyyy")

		state_code = kwargs.get("state_code")
		pincode = kwargs.get("pincode")
		district = None

		if not state_code:
			if not pincode:
				return {"status": 0, "msg": "Pincode required to fetch state code"}

			state_code, district = get_state_code(pincode)
			if not state_code:
				return {"status": 0, "msg": "Unable to determine state code from pincode"}

		payload = {
			"firstName": kwargs.get("first_name"),
			"lastName": kwargs.get("last_name"),
			"dob": dob,
			"idType": kwargs.get("id_type"),
			"idNumber": kwargs.get("id_number"),
			"mobileNumber": add_country_code(mobile),
			"district": district,
			"stateCode": state_code,
			"pincode": pincode,
		}

		score = credit_check(payload)

		return {"status": 1, "msg": score}

	except Exception:
		frappe.log_error(frappe.get_traceback(), "Credit Check Error")
		return {"status": 0, "msg": "Credit check failed, please try again later"}

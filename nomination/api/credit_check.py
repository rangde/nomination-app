import frappe
from frappe.utils import formatdate

from nomination.api.rangde_service import credit_check, request_otp, verify_otp
from nomination.api.state_code import get_state_code


@frappe.whitelist()
def credit_score(**kwargs):
	if frappe.session.user == "Guest":
		return {"status": 0, "msg": "Not logged in"}

	try:
		mobile = (kwargs.get("mobile_number") or "").strip()

		if not mobile:
			return {"status": 0, "msg": "Mobile number required"}

		if not mobile.startswith("91"):
			mobile = f"91{mobile}"

		dob = formatdate(kwargs.get("dob"), "dd-MM-yyyy")

		state_code = kwargs.get("state_code")
		pincode = kwargs.get("pincode")

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
			"idType": "PAN",
			"idNumber": kwargs.get("pan_number"),
			"mobileNumber": mobile,
			"district": district,
			"stateCode": state_code,
			"pincode": pincode,
		}

		score = credit_check(payload)

		return {"status": 1, "msg": score}

	except Exception as e:
		return {"status": 0, "msg": str(e)}

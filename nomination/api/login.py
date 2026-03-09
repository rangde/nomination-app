import frappe

from nomination.api.rangde_service import get_tokens, initiate_session, request_otp, verify_otp


@frappe.whitelist(allow_guest=True)
def user_validation(mobile_number, credit_check=False):
	mobile_number = str(mobile_number).strip()
	if not credit_check:
		user = frappe.db.get_value("User", {"mobile_no": mobile_number}, "name")
		if not user:
			return {"status": 0, "msg": "Mobile number not registered"}

		auth_token, csrf_token = get_tokens()

		if not auth_token or not csrf_token:
			initiate_session()

	mobile_number = f"91{mobile_number}"
	send_otp(mobile_number)

	return {"status": 1, "msg": "OTP sent successfully"}


@frappe.whitelist(allow_guest=True)
def send_otp(mobile_number):
	result = request_otp(mobile_number)

	return {"status": 1, "msg": result}


@frappe.whitelist(allow_guest=True)
def verify_user_otp(mobile_number, otp, credit_check=False):
	result = verify_otp(mobile_number, otp)

	messages = result.get("messages", [])

	if not messages or messages[0].get("code") != "1":
		return {"status": 0, "msg": "OTP verification failed"}

	mobile_number = str(mobile_number).strip()

	if mobile_number.startswith("91"):
		mobile_number = mobile_number[2:]

	if credit_check:
		return {"status": 1, "msg": "Otp Verfied successfully"}

	user = frappe.db.get_value("User", {"mobile_no": mobile_number}, "name")

	if not user:
		return {"status": 0, "msg": "User not found "}

	frappe.local.login_manager.login_as(user)

	return {"status": 1, "msg": "Logged in successfully", "user": user}

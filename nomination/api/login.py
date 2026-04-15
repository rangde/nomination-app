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

	mobile_number_with_prefix = f"91{mobile_number}"
	send_otp_internal(mobile_number_with_prefix)

	return {"status": 1, "msg": "OTP sent successfully"}


def send_otp_internal(mobile_number):
	try:
		result = request_otp(mobile_number)
		return result
	except Exception:
		frappe.log_error(frappe.get_traceback(), "RangDe OTP Service Error")
		frappe.throw("OTP service is temporarily unavailable. Please try again later.")


@frappe.whitelist(allow_guest=True)
def verify_user_otp(mobile_number, otp):
	result = verify_otp(mobile_number, otp)
	messages = result.get("messages", [])

	if not messages or messages[0].get("code") != "1":
		frappe.response.http_status_code = 417
		frappe.cache().delete_value(f"otp_verified_{mobile_number}")
		return {"status": 0, "msg": "OTP verification failed"}

	mobile_number = str(mobile_number).strip()
	if mobile_number.startswith("91"):
		mobile_number = mobile_number[2:]

	frappe.cache().set_value(f"otp_verified_{mobile_number}", "1", expires_in_sec=300)

	user = frappe.db.get_value("User", {"mobile_no": mobile_number}, "name")
	if not user:
		return {"status": 0, "msg": "User not found"}

	frappe.local.login_manager.login_as(user)
	return {"status": 1, "msg": "Logged in successfully", "user": user}

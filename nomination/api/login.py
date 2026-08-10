import frappe
import requests

from nomination.api.rangde_service import (
	get_tokens,
	initiate_session,
	request_otp,
	strip_country_code,
	verify_otp,
)


@frappe.whitelist(allow_guest=True)
def user_validation(mobile_number, credit_check=False):
	mobile_number = strip_country_code(mobile_number)
	if not mobile_number:
		return {"status": 0, "msg": "Please enter a valid 10-digit mobile number"}

	if not credit_check:
		user = frappe.db.get_value("User", {"mobile_no": mobile_number}, "name")
		if not user:
			return {"status": 0, "msg": "Mobile number not registered"}

		auth_token, csrf_token = get_tokens()
		if not auth_token or not csrf_token:
			initiate_session()

	send_otp_internal(mobile_number)

	return {"status": 1, "msg": "OTP sent successfully"}


def send_otp_internal(mobile_number):
	try:
		result = request_otp(mobile_number)
		return result
	except requests.exceptions.ReadTimeout:
		# The request was fully delivered and the gateway simply answered too
		# slowly — the SMS is normally sent in this case. Reporting a failure here
		# tells the user the OTP never came while their phone is buzzing, so let
		# them proceed to the OTP screen instead.
		#
		# Deliberately not retried: a second request sends a second OTP and can
		# invalidate the code the user already has.
		frappe.log_error(frappe.get_traceback(), "RangDe OTP Response Timeout")
		return None
	except Exception:
		# Connect timeouts and connection errors mean the request never landed,
		# so no OTP was sent and failing is correct.
		frappe.log_error(frappe.get_traceback(), "RangDe OTP Service Error")
		frappe.throw("OTP service is temporarily unavailable. Please try again later.")


@frappe.whitelist(allow_guest=True)
def verify_user_otp(mobile_number, otp, credit_check=False):
	mobile_number = strip_country_code(mobile_number)
	if not mobile_number:
		return {"status": 0, "msg": "Please enter a valid 10-digit mobile number"}

	result = verify_otp(mobile_number, otp)
	messages = result.get("messages", [])

	if not messages or messages[0].get("code") != "1":
		frappe.log_error(
			f"Invalid OTP verification for mobile number {mobile_number}. Response: {result}",
			"RangDe OTP Verification Failed",
		)
		frappe.response.http_status_code = 417
		frappe.cache().delete_value(f"otp_verified_{mobile_number}")
		return {"status": 0, "msg": "Incorrect OTP, please enter the correct OTP"}

	frappe.cache().set_value(f"otp_verified_{mobile_number}", "1", expires_in_sec=300)

	if credit_check:
		return {"status": 1, "msg": "OTP verified successfully"}

	user = frappe.db.get_value("User", {"mobile_no": mobile_number}, "name")
	if not user:
		return {"status": 0, "msg": "User not found"}

	frappe.local.login_manager.login_as(user)
	return {"status": 1, "msg": "Logged in successfully", "user": user}


@frappe.whitelist(allow_guest=True, methods=["POST"])
def logout():
	try:
		frappe.local.login_manager.logout()
		frappe.db.commit()
		return {"status": 1, "msg": "Logged out successfully"}
	except Exception:
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "Custom Logout Failed")
		return {"status": 0, "msg": "Logout failed"}


@frappe.whitelist(allow_guest=True)
def get_csrf():
	return {
		"csrf_token": frappe.sessions.get_csrf_token(),
		"user": frappe.session.user,
	}

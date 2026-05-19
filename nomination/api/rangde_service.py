import frappe
import requests


def get_base_url():
	base_url = frappe.get_single("Rangde Settings").base_url
	if not base_url:
		frappe.throw("RangDe base URL not configured")
	return base_url


def rangde_headers():
	return frappe.conf.get("rangde_headers", {})


def initiate_session():
	url = f"{get_base_url()}/login"

	headers = rangde_headers()

	response = requests.get(url, headers=headers, timeout=10)

	if response.status_code != 200:
		frappe.throw("Failed to initiate RangDe session")

	auth_token = response.headers.get("x-auth-token")
	csrf_token = response.headers.get("x-csrf-token")

	if not auth_token or not csrf_token:
		frappe.throw("RangDe tokens missing")

	frappe.cache().set_value("rangde_auth_token", auth_token)
	frappe.cache().set_value("rangde_csrf_token", csrf_token)

	return auth_token, csrf_token


def get_tokens():
	cached_auth_token = frappe.cache().get_value("rangde_auth_token")
	cached_csrf_token = frappe.cache().get_value("rangde_csrf_token")

	if not cached_auth_token or not cached_csrf_token:
		return initiate_session()

	return cached_auth_token, cached_csrf_token


def _post(endpoint, data, retry=True):
	auth_token, csrf_token = get_tokens()
	payload = dict(data or {})
	payload.setdefault("userName", get_user_name(payload.get("mobileNumber")))

	headers = {
		**rangde_headers(),
		"x-auth-token": auth_token,
		"x-csrf-token": csrf_token,
	}

	url = f"{get_base_url()}/{endpoint}"

	response = requests.post(url, headers=headers, data=payload, timeout=10)

	if response.status_code == 401 and retry:
		initiate_session()
		return _post(endpoint, data, retry=False)

	if response.status_code != 200:
		frappe.log_error(f"RangDe API error: {response.text}", "RangDe Service Error")
		frappe.throw("RangDe API request failed")

	return response.json()


def request_otp(mobileNumber):
	mobilenumber = mobileNumber.strip()

	payload = {"mobileNumber": mobilenumber, "purpose": "NOMINATION"}

	return _post("borrower-nomination/otp/requests", payload)


def verify_otp(mobileNumber, otp):
	mobileNumber = mobileNumber.strip()

	if not mobileNumber.startswith("91"):
		mobileNumber = f"91{mobileNumber}"

	payload = {"mobileNumber": mobileNumber, "code": otp}

	return _post("borrower-nomination/otp/verify", payload)


def credit_check(data):
	if data:
		return _post("borrower-nomination/credit-check", data)
	return None


def get_metrics():
	headers = rangde_headers()
	url = f"{get_base_url()}/borrower-nomination/metrics"
	response = requests.get(url, headers=headers, timeout=10)
	return response.json()


def get_user_name(fallback_identifier=None):
	user = frappe.session.user
	if user and user != "Guest":
		user_info = frappe.get_value("User", user, ["full_name", "mobile_no"], as_dict=True)
		if user_info:
			return user_info.full_name or user_info.mobile_no or user
		return user

	if fallback_identifier:
		return fallback_identifier

	request_id = frappe.get_request_header("X-Frappe-Request-Id")
	if request_id:
		return request_id
	return frappe.local.request_ip or "Guest"

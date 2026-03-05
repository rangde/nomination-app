import frappe
import requests

STATE_MAPPING = {
	"Tamil Nadu": "TN",
	"Kerala": "KL",
	"Karnataka": "KA",
	"Maharashtra": "MH",
	"Andhra Pradesh": "AP",
	"Telangana": "TS",
	"Uttar Pradesh": "UP",
	"Delhi": "DL",
	"Gujarat": "GJ",
	"Rajasthan": "RJ",
	"West Bengal": "WB",
	"Bihar": "BR",
	"Punjab": "PB",
	"Haryana": "HR",
	"Madhya Pradesh": "MP",
	"Odisha": "OD",
	"Assam": "AS",
	"Chhattisgarh": "CG",
	"Jharkhand": "JH",
	"Uttarakhand": "UK",
	"Himachal Pradesh": "HP",
	"Jammu and Kashmir": "JK",
	"Ladakh": "LA",
	"Goa": "GA",
	"Tripura": "TR",
	"Meghalaya": "ML",
	"Manipur": "MN",
	"Nagaland": "NL",
	"Arunachal Pradesh": "AR",
	"Mizoram": "MZ",
}


def get_state_code(pincode):
	try:
		url = f"https://api.postalpincode.in/pincode/{pincode}"

		response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
		data = response.json()
		if not data or data[0].get("Status") != "Success":
			return None

		state_name = data[0]["PostOffice"][0]["State"]
		distric_name = data[0]["PostOffice"][0]["District"]
		format_name = state_name.strip().replace("\xa0", " ")
		format_name = " ".join(format_name.split())

		for key, value in STATE_MAPPING.items():
			if key.lower() == format_name.lower():
				return value, distric_name

		return None

	except Exception as e:
		frappe.log_error(f"Error fetching state code for pincode {pincode}: {e}")

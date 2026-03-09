import re

import frappe
from frappe.utils import add_years, getdate, nowdate

# Multiplication table
D_TABLE = [
	[0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
	[1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
	[2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
	[3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
	[4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
	[5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
	[6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
	[7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
	[8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
	[9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
]

# Permutation table
P_TABLE = [
	[0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
	[1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
	[5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
	[8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
	[9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
	[4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
	[2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
	[7, 0, 4, 6, 9, 1, 3, 2, 5, 8],
]


def validate_aadhaar_number(aadhaar_number):
	if not aadhaar_number.isdigit() or len(aadhaar_number) != 12:
		frappe.throw("Aadhaar number must be a 12-digit numeric string")
	c = 0
	for i, digit in enumerate(reversed(aadhaar_number)):
		c = D_TABLE[c][P_TABLE[i % 8][int(digit)]]

	if c != 0:
		frappe.throw("Invalid Aadhaar number")


def validate_pan_number(pan_number):
	pan_no = pan_number.strip().upper()

	pattern = r"^[A-Z]{5}[0-9]{4}[A-Z]$"
	valid_types = ["A", "B", "C", "F", "G", "H", "L", "J", "P", "T"]

	if len(pan_no) != 10:
		frappe.throw("PAN number must be 10 characters")

	if pan_no[3] not in valid_types:
		frappe.thorw("Invalid PAN number tyep")
	if not re.match(pattern, pan_no):
		frappe.throw("Invalid PAN format")


def validate_date_of_birth(dob):
	dob_date = getdate(dob)
	today = getdate(nowdate())

	if dob_date >= today:
		frappe.throw("Date of birth must be in the past")

	eligible_year = add_years(today, -18)

	if dob_date > eligible_year:
		frappe.throw("Must be at least 18 years of age to apply")

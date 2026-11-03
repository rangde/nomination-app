import unittest
from unittest.mock import patch

import frappe

from nomination.api import dashboard

NOMINEES = [
	{
		"name": "Asha",
		"mobileNumber": "919000000001",
		"taStatus": "Failed",
		"lpStatus": None,
		"trainingCompletedDate": "2026-04-21T17:16:29+05:30",
		"lastUpdated": "2026-10-01T10:00:00+05:30",
	},
	{
		"name": "Bina",
		"mobileNumber": "919000000002",
		"taStatus": "Passed",
		"lpStatus": "Applied",
		"loanId": "9",
		"requestedLoanAmount": "₹10,000.00",
		"lastUpdated": "2026-10-05T10:00:00+05:30",
	},
	{
		"name": "Chitra",
		"mobileNumber": "919000000003",
		"taStatus": None,
		"lpStatus": None,
		"lastUpdated": "2026-10-03T10:00:00+05:30",
	},
	{
		"name": "Devi",
		"mobileNumber": "919000000004",
		"taStatus": "Passed",
		"lpStatus": "Disbursed",
		"loanId": "7",
		"disbursalDate": "2026-09-01T10:00:00+05:30",
		"lastUpdated": "2026-10-04T10:00:00+05:30",
	},
]
FORMS = [
	{
		"name": "NF-1",
		"first_name": "Asha",
		"last_name": "K",
		"townvillage": "Vill A",
		"name_of_the_shg": "S1",
		"name_of_the_vo": "V1",
		"workflow_state": "CLF Approved",
		"mobile_number": "9000000001",
		"photo_of_didi": None,
		"creation": "2026-03-01 10:00:00",
		"modified": "2026-03-02 10:00:00",
	},
	{
		"name": "NF-2",
		"first_name": "Eka",
		"last_name": "",
		"townvillage": "Vill B",
		"name_of_the_shg": "S2",
		"name_of_the_vo": "V2",
		"workflow_state": "VO Approved",
		"mobile_number": "9000000005",
		"photo_of_didi": None,
		"creation": "2026-03-01 10:00:00",
		"modified": "2026-03-02 10:00:00",
	},
]


class TestDidiRows(unittest.TestCase):
	def rows(self, **kwargs):
		with (
			patch.object(dashboard, "_nomination_owner_scope_for_session", return_value=None),
			patch.object(dashboard, "get_nominees", return_value=NOMINEES),
			patch.object(frappe, "get_all", return_value=[frappe._dict(f) for f in FORMS]),
		):
			return dashboard.get_dashboard_didi_rows(**kwargs)["msg"]

	def test_all_tab_shows_each_didi_once_with_latest_status(self):
		by_name = {r["name"]: r for r in self.rows(tab="all")["rows"]}
		self.assertEqual(len(by_name), 5)
		self.assertEqual((by_name["Asha K"]["stage"], by_name["Asha K"]["status"]), ("training", "failed"))
		self.assertEqual(by_name["Asha K"]["village"], "Vill A")
		self.assertEqual((by_name["Eka"]["stage"], by_name["Eka"]["status"]), ("nomination", "vo_approved"))
		self.assertEqual(by_name["Bina"]["status"], "applied")
		self.assertEqual(by_name["Chitra"]["status"], "registered")

	def test_training_tab_status_filter(self):
		rows = self.rows(tab="training", statuses="passed,failed")["rows"]
		self.assertEqual(sorted(r["name"] for r in rows), ["Asha K", "Bina", "Devi"])

	def test_loan_tab_keeps_training_result_and_filters(self):
		rows = self.rows(tab="loan", statuses="disbursed,repaying")["rows"]
		self.assertEqual([r["name"] for r in rows], ["Devi"])
		self.assertEqual(rows[0]["training_status"], "passed")

	def test_sorted_by_last_updated_desc(self):
		rows = self.rows(tab="training")["rows"]
		self.assertEqual([r["name"] for r in rows][:2], ["Bina", "Devi"])

	def test_invalid_tab_rejected(self):
		with patch.object(dashboard, "_nomination_owner_scope_for_session", return_value=None):
			with self.assertRaises(frappe.ValidationError):
				dashboard.get_dashboard_didi_rows(tab="bogus")

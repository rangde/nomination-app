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

	def test_only_active_workflow_states_are_queried(self):
		with (
			patch.object(dashboard, "_nomination_owner_scope_for_session", return_value=None),
			patch.object(dashboard, "get_nominees", return_value=[]),
			patch.object(frappe, "get_all", return_value=[]) as get_all,
		):
			dashboard.get_dashboard_didi_rows()
		states = get_all.call_args.kwargs["filters"]["workflow_state"][1]
		self.assertEqual(set(states), {"SHG Proposed", "VO Approved", "CLF Approved"})

	def test_scoped_user_sees_no_rangde_only_rows(self):
		with (
			patch.object(dashboard, "_nomination_owner_scope_for_session", return_value={"a@x.com"}),
			patch.object(dashboard, "get_nominees", return_value=NOMINEES),
			patch.object(frappe, "get_all", return_value=[frappe._dict(FORMS[0])]),
		):
			rows = dashboard.get_dashboard_didi_rows()["msg"]["rows"]
		self.assertEqual([r["name"] for r in rows], ["Asha K"])

	def test_scoped_user_without_subordinates_gets_empty_list(self):
		with (
			patch.object(dashboard, "_nomination_owner_scope_for_session", return_value=set()),
			patch.object(dashboard, "get_nominees", return_value=NOMINEES),
		):
			self.assertEqual(dashboard.get_dashboard_didi_rows()["msg"]["rows"], [])

	def test_empty_and_duplicate_mobiles_do_not_collapse(self):
		nominees = [
			{"name": "N1", "mobileNumber": None, "lastUpdated": "2026-10-01T10:00:00+05:30"},
			{"name": "N2", "mobileNumber": "", "lastUpdated": "2026-10-02T10:00:00+05:30"},
			{"name": "D1", "mobileNumber": "919111111111", "lastUpdated": "2026-10-01T10:00:00+05:30"},
			{"name": "D2", "mobileNumber": "919111111111", "lastUpdated": "2026-10-03T10:00:00+05:30"},
		]
		with (
			patch.object(dashboard, "_nomination_owner_scope_for_session", return_value=None),
			patch.object(dashboard, "get_nominees", return_value=nominees),
			patch.object(frappe, "get_all", return_value=[]),
			patch.object(frappe, "log_error"),
		):
			rows = dashboard.get_dashboard_didi_rows()["msg"]["rows"]
		self.assertEqual(sorted(r["name"] for r in rows), ["D2", "N1", "N2"])
		self.assertEqual(len({r["key"] for r in rows}), 3)

	def test_two_forms_with_same_mobile_share_one_nominee_only_once(self):
		forms = [frappe._dict(FORMS[0]), frappe._dict({**FORMS[0], "name": "NF-9", "first_name": "Dup"})]
		with (
			patch.object(dashboard, "_nomination_owner_scope_for_session", return_value=None),
			patch.object(dashboard, "get_nominees", return_value=NOMINEES[:1]),
			patch.object(frappe, "get_all", return_value=forms),
			patch.object(frappe, "log_error"),
		):
			rows = {r["key"]: r for r in dashboard.get_dashboard_didi_rows()["msg"]["rows"]}
		self.assertEqual(rows["NF-1"]["status"], "failed")
		self.assertEqual(rows["NF-9"]["status"], "clf_approved")

	def test_each_loan_is_its_own_card_but_training_counts_the_didi_once(self):
		nominees = [
			{**NOMINEES[1], "loanId": "1", "lastUpdated": "2026-10-01T10:00:00+05:30"},
			{
				**NOMINEES[1],
				"loanId": "2",
				"lpStatus": "Disbursed",
				"lastUpdated": "2026-10-02T10:00:00+05:30",
			},
			{
				**NOMINEES[1],
				"loanId": "2",
				"lpStatus": "Repaying",
				"lastUpdated": "2026-10-03T10:00:00+05:30",
			},
		]
		with (
			patch.object(dashboard, "_nomination_owner_scope_for_session", return_value=None),
			patch.object(dashboard, "get_nominees", return_value=nominees),
			patch.object(frappe, "get_all", return_value=[]),
		):
			get = lambda **kw: dashboard.get_dashboard_didi_rows(**kw)["msg"]["rows"]  # noqa: E731
			loans, everything, training = get(tab="loan"), get(tab="all"), get(tab="training")
		# loan 2 appears once, with its latest status
		self.assertEqual(len(loans), 2)
		self.assertEqual(sorted(r["status"] for r in loans), ["applied", "repaying"])
		self.assertEqual(len({r["key"] for r in loans}), 2)
		self.assertEqual({r["training_status"] for r in loans}, {"passed"})
		self.assertEqual(len(everything), 2)
		self.assertEqual(len(training), 1)
		self.assertEqual(training[0]["status"], "passed")

	def test_completed_loans_stay_in_loan_tab(self):
		self.assertEqual(dashboard._loan_status({"lpStatus": "Closed"}), "repaying")

	def test_unknown_loan_status_is_not_applied(self):
		self.assertIsNone(dashboard._loan_status({"lpStatus": "Rejected", "loanId": "1"}))
		self.assertEqual(dashboard._loan_status({"lpStatus": "", "loanId": "1"}), "applied")

	def test_zero_requested_amount_is_shown_as_empty(self):
		self.assertIsNone(dashboard._positive_amount("₹0.00"))
		self.assertIsNone(dashboard._positive_amount(None))
		self.assertEqual(dashboard._positive_amount("₹1,00,000.00"), "₹1,00,000.00")
		bina = next(r for r in self.rows(tab="loan")["rows"] if r["name"] == "Bina")
		self.assertEqual(bina["requested_amount"], "₹10,000.00")

	def test_timestamps_with_z_and_offsets_are_parsed(self):
		self.assertIsNotNone(dashboard._naive_datetime("2026-10-01T10:00:00Z"))
		self.assertIsNotNone(dashboard._naive_datetime("2026-10-01T10:00:00+05:30"))

	def test_assessment_completed_falls_back_when_null(self):
		metrics = {"completedAssessment": None, "passed": 2, "failed": 3}
		with patch.object(dashboard, "_count_nomination_forms", return_value=0):
			result = dashboard._build_dashboard_metrics(metrics, None)
		self.assertEqual(result["training"]["assessment_completed"], 5)

	def test_rangde_failure_message_includes_status_code(self):
		from nomination.api import rangde_service

		response = type("R", (), {"status_code": 400, "text": "Bad Request", "headers": {}})()
		with (
			patch.object(rangde_service, "get_base_url", return_value="https://x"),
			patch.object(rangde_service, "rangde_headers", return_value={}),
			patch.object(rangde_service.requests, "get", return_value=response),
			patch.object(rangde_service.frappe, "log_error"),
		):
			with self.assertRaises(frappe.ValidationError) as ctx:
				rangde_service.get_nominees(force=True)
		self.assertIn("status 400", str(ctx.exception))

	def test_nominee_list_is_read_from_nominees_or_data_key(self):
		from nomination.api import rangde_service

		for key in ("nominees", "data"):
			response = type(
				"R",
				(),
				{
					"status_code": 200,
					"text": "",
					"headers": {},
					"json": lambda self, k=key: {k: [{"name": "A"}]},
				},
			)()
			with (
				patch.object(rangde_service, "get_base_url", return_value="https://x"),
				patch.object(rangde_service, "rangde_headers", return_value={}),
				patch.object(rangde_service.requests, "get", return_value=response),
				patch.object(rangde_service.frappe, "cache"),
			):
				self.assertEqual(rangde_service.get_nominees(force=True), [{"name": "A"}])

	def test_invalid_tab_rejected(self):
		with patch.object(dashboard, "_nomination_owner_scope_for_session", return_value=None):
			with self.assertRaises(frappe.ValidationError):
				dashboard.get_dashboard_didi_rows(tab="bogus")

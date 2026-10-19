import unittest
from datetime import datetime
from unittest.mock import patch

import frappe

from nomination.api import dashboard, public_dashboard


class TestPublicDashboard(unittest.TestCase):
	def setUp(self):
		self.counts = patch.object(dashboard, "_count_nomination_forms", return_value=7).start()
		self.upstream = patch.object(public_dashboard, "get_metrics", return_value={}).start()
		patch.object(public_dashboard, "now_datetime", return_value=datetime(2026, 10, 19, 12)).start()
		self.addCleanup(patch.stopall)

	def summary(self):
		# Exercise payload generation separately from Redis infrastructure.
		return public_dashboard._get_public_dashboard_metrics.__wrapped__()

	def test_only_public_endpoint_allows_guests(self):
		self.assertIn(public_dashboard.get_public_dashboard_metrics, frappe.guest_methods)
		for endpoint in (
			dashboard.get_dashboard_metrics,
			dashboard.get_dashboard_nomination_rows,
			dashboard.get_nomination_list,
		):
			self.assertNotIn(endpoint, frappe.guest_methods)
		self.assertEqual(
			frappe.allowed_http_methods_for_whitelisted_func[public_dashboard.get_public_dashboard_metrics],
			["GET"],
		)

	def test_publishes_only_known_numeric_aggregates(self):
		self.upstream.return_value = {
			"totalTrainees": "12",
			"passed": 0,
			"amountDisbursed": "1250.50",
			"medianDaysToDisbursal": 2.5,
			"borrowers": [{"name": "Private Name", "mobile": "9999999999"}],
			"failed": {"name": "Private Name"},
		}
		result = self.summary()
		self.assertEqual(set(result), {"nomination", "training", "loan", "updated_at"})
		self.assertEqual(
			result["training"], {"total_registered": 12, "under_training": None, "passed": 0, "failed": None}
		)
		self.assertEqual(result["loan"]["amount_disbursed"], 1250.5)
		self.assertEqual(result["loan"]["median_days"], 2.5)
		self.assertNotIn("Private Name", str(result))
		self.assertNotIn("9999999999", str(result))

	def test_public_counts_have_site_wide_scope(self):
		result = self.summary()
		self.assertEqual(len(result["nomination"]), 5)
		for call in self.counts.call_args_list:
			self.assertIsNone(call.args[1])
		self.assertEqual(result["nomination"]["shg_approved"], result["nomination"]["vo_pending"])
		self.assertEqual(result["nomination"]["vo_approved"], result["nomination"]["clf_pending"])

	def test_upstream_failure_preserves_nomination_counts(self):
		self.upstream.side_effect = RuntimeError("Service unavailable")
		with patch.object(frappe, "log_error"), patch.object(frappe, "get_traceback", return_value=""):
			result = self.summary()
		self.assertEqual(result["nomination"]["clf_approved"], 7)
		self.assertTrue(all(value is None for value in result["training"].values()))
		self.assertTrue(all(value is None for value in result["loan"].values()))

	def test_unexpected_upstream_payload_is_unavailable(self):
		for payload in (None, [], "Service unavailable"):
			with self.subTest(payload=payload):
				self.upstream.return_value = payload
				self.assertIsNone(self.summary()["training"]["passed"])

	def test_rejects_non_numeric_and_non_finite_values(self):
		for value in (None, True, False, {}, [], "Private Name", "NaN", "Infinity", -1, float("inf")):
			with self.subTest(value=value):
				self.assertIsNone(public_dashboard._public_number(value))

	def test_existing_dashboard_still_uses_session_scope(self):
		with (
			patch.object(dashboard, "get_metrics", return_value={}),
			patch.object(dashboard, "_nomination_owner_scope_for_session", return_value={"team-user"}),
		):
			dashboard.get_dashboard_metrics()
		for call in self.counts.call_args_list:
			self.assertEqual(call.args[1], {"team-user"})

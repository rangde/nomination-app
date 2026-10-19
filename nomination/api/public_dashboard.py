"""Public, aggregate-only dashboard data. Never return nomination records here."""

import math

import frappe
from frappe.utils import now_datetime
from frappe.utils.caching import redis_cache

from nomination.api.dashboard import _build_dashboard_metrics
from nomination.api.rangde_service import get_metrics


def _public_number(value):
	# Only publish finite, non-negative numbers, even if the upstream schema changes.
	if isinstance(value, bool) or not isinstance(value, (str, int, float)):
		return None
	try:
		number = float(value)
	except ValueError, OverflowError:
		return None
	if not math.isfinite(number) or number < 0:
		return None
	return int(number) if number.is_integer() else number


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_public_dashboard_metrics():
	"""Return site-wide totals, identical for guests and signed-in visitors."""
	return _get_public_dashboard_metrics()


@redis_cache(ttl=60)
def _get_public_dashboard_metrics():
	try:
		metrics = get_metrics()
	except Exception:
		frappe.log_error(title="Public Dashboard Metrics Unavailable", message=frappe.get_traceback())
		metrics = {}
	if not isinstance(metrics, dict):
		metrics = {}

	# The shared builder selects only known aggregate fields. The numeric filter
	# prevents upstream objects or text from being exposed through those fields.
	summary = _build_dashboard_metrics(metrics, owners=None)
	return {
		**{
			section: {key: _public_number(value) for key, value in values.items()}
			for section, values in summary.items()
		},
		"updated_at": now_datetime().isoformat(),
	}

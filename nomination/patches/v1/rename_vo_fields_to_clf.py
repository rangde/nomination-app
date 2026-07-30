import frappe
from frappe.model.utils.rename_field import rename_field

DOCTYPE = "Nomination Form"

FIELD_RENAMES = {
	"vo_approval_by": "clf_approval_by",
	"vo_approved_on": "clf_approved_on",
	"vo_proposed": "clf_proposed",
}


def execute():
	"""Rename the vo_* approval fields to clf_* before the doctype is synced.

	Runs pre_model_sync so the old fieldnames still exist in the DocType and the
	column data is carried over instead of being dropped and recreated empty.
	"""
	if not frappe.db.table_exists(DOCTYPE):
		return

	meta = frappe.get_meta(DOCTYPE)

	for old_fieldname, new_fieldname in FIELD_RENAMES.items():
		if not meta.has_field(old_fieldname) or meta.has_field(new_fieldname):
			continue

		rename_field(DOCTYPE, old_fieldname, new_fieldname)

import frappe

DOCTYPE = "Nomination Form"

# Approval data stranded by the tier renames. Each entry maps a column left behind
# in the table to the live field that should now hold that tier's data.
#
# Odisha renamed its tiers twice: CLF -> GPLF (94b7fc5) and then VO -> CLF (633022c).
# The first rename changed the DocType JSON with no accompanying patch, so sync_all()
# created the new columns empty and left the old ones in the table with their data.
STRANDED_COLUMNS = {
	"vo_approval_by": "clf_approval_by",
	"vo_approved_on": "clf_approved_on",
	"vo_proposed": "clf_proposed",
}

NUMERIC_FIELDTYPES = {"Currency", "Float", "Int", "Percent"}


def execute():
	"""Move approval data out of orphaned tier columns into the live tier fields.

	Only touches columns that are orphans -- present in the table but no longer in
	the DocType. On Bihar vo_* is still a live tier-2 field and clf_* is tier 3, so
	every move is skipped there and the patch is a no-op. Rows that already have a
	value in the target field are left alone, so this never overwrites an approval
	and is safe to re-run.
	"""
	if not frappe.db.table_exists(DOCTYPE):
		return

	meta = frappe.get_meta(DOCTYPE)

	for stranded_column, live_fieldname in STRANDED_COLUMNS.items():
		if meta.has_field(stranded_column):
			# Still a live field on this site (Bihar): nothing was stranded.
			continue

		live_field = meta.get_field(live_fieldname)
		if not live_field:
			continue

		if not frappe.db.has_column(DOCTYPE, stranded_column):
			continue

		if live_field.fieldtype in NUMERIC_FIELDTYPES:
			# These columns are NOT NULL DEFAULT 0, so "empty" means zero.
			condition = f"ifnull(`{live_fieldname}`, 0) = 0 and ifnull(`{stranded_column}`, 0) != 0"
		else:
			condition = f"`{live_fieldname}` is null and `{stranded_column}` is not null"

		affected = frappe.db.sql(f"select count(*) from `tab{DOCTYPE}` where {condition}")[0][0]
		if not affected:
			continue

		# Raw SQL on purpose: the stranded column has no DocField, so the ORM cannot
		# read it. modified is deliberately left untouched -- this is a data repair,
		# not a document edit.
		frappe.db.sql(f"update `tab{DOCTYPE}` set `{live_fieldname}` = `{stranded_column}` where {condition}")

		print(f"  restored {affected} row(s): {stranded_column} -> {live_fieldname}")

	# The orphaned columns are deliberately left in place. Once the restored data has
	# been verified in production they can be dropped in a follow-up patch.

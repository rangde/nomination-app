import frappe

OLD_STATE = "VO Approved"
NEW_STATE = "CLF Approved"

OLD_ACTION = "Send to VO"
NEW_ACTION = "Send to CLF"

OLD_ROLE = "VO"
NEW_ROLE = "CLF"


def _rename(doctype, old_name, new_name):
	if not frappe.db.exists(doctype, old_name):
		return

	# A stale CLF record can be left over from the earlier CLF -> GPLF rename,
	# so merge into it rather than failing on a duplicate name.
	merge = bool(frappe.db.exists(doctype, new_name))
	frappe.rename_doc(doctype, old_name, new_name, merge=merge, force=True, show_alert=False)


def execute():
	"""Rename the VO role, workflow state and workflow action to CLF.

	rename_doc updates the link fields that point at these records (Has Role.role,
	DocPerm.role, Workflow Document State.state, Workflow Transition.action,
	Nomination Form.workflow_state), so existing users keep their permissions and
	in-flight nominations keep their workflow state.
	"""
	_rename("Workflow Action Master", OLD_ACTION, NEW_ACTION)
	_rename("Workflow State", OLD_STATE, NEW_STATE)
	_rename("Role", OLD_ROLE, NEW_ROLE)

	# Safety net: workflow_state is only link-updated if the field is a Link to
	# Workflow State, so move any documents the rename above left behind.
	if frappe.db.table_exists("Nomination Form"):
		frappe.db.set_value(
			"Nomination Form",
			{"workflow_state": OLD_STATE},
			"workflow_state",
			NEW_STATE,
			update_modified=False,
		)

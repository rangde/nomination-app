import frappe
from frappe.core.doctype.role.role import STANDARD_ROLES
from frappe.permissions import SYSTEM_USER_ROLE

# Roles this app defines and assigns.
NOMINATION_ROLES = ("SHG", "VO", "GPLF", "Read only")

# Roles the desk breaks without. STANDARD_ROLES covers Administrator, System Manager,
# Script Manager, All and Guest; SYSTEM_USER_ROLE ("Desk User") drives System User
# desk access. Never disable these -- Role.disable_role() throws on some of them.
REQUIRED_FRAPPE_ROLES = (*STANDARD_ROLES, SYSTEM_USER_ROLE)

# Standard desk roles kept enabled for report and workspace administration.
# Remove entries here if they should be disabled too.
RETAINED_DESK_ROLES = ("Report Manager", "Workspace Manager", "Prepared Report User")


def roles_to_keep() -> set[str]:
	return {*NOMINATION_ROLES, *REQUIRED_FRAPPE_ROLES, *RETAINED_DESK_ROLES}


def disable_non_nomination_roles() -> list[str]:
	"""Disable every role that isn't needed by the nomination app.

	Saves through the ORM on purpose: Role.disable_role() deletes the matching
	Has Role rows and clears the cache, both of which frappe.db.set_value skips.
	"""
	to_disable = frappe.get_all(
		"Role",
		filters={"name": ["not in", list(roles_to_keep())], "disabled": 0},
		pluck="name",
	)

	for name in to_disable:
		role = frappe.get_doc("Role", name)
		role.disabled = 1
		role.save(ignore_permissions=True)

	return to_disable


def enable_required_roles() -> list[str]:
	"""Re-enable core roles that an earlier run of the patch disabled."""
	wrongly_disabled = frappe.get_all(
		"Role",
		filters={"name": ["in", list(REQUIRED_FRAPPE_ROLES)], "disabled": 1},
		pluck="name",
	)

	for name in wrongly_disabled:
		role = frappe.get_doc("Role", name)
		role.disabled = 0
		role.save(ignore_permissions=True)

	return wrongly_disabled


def setup_roles():
	enable_required_roles()
	disable_non_nomination_roles()


def after_install():
	setup_roles()

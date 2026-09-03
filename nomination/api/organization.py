import frappe

ORGANIZATION_TYPES = {
	"SHG": "shg",
	"VO": "vo",
}


@frappe.whitelist()
def search_organizations(organization_type, search_text="", limit=10):
	if frappe.session.user == "Guest":
		return {"status": 0, "msg": "Not logged in"}

	organization_type = str(organization_type or "").upper()
	flag_field = ORGANIZATION_TYPES.get(organization_type)
	if not flag_field:
		return {"status": 0, "msg": "Invalid organization type"}

	try:
		limit = min(max(int(limit), 1), 20)
	except (TypeError, ValueError):
		limit = 10

	filters = {flag_field: 1}
	search_text = str(search_text or "").strip()
	if search_text:
		filters["organisation_name"] = ["like", f"%{search_text}%"]

	organizations = frappe.get_all(
		"Organization",
		fields=["name", "organisation_name"],
		filters=filters,
		order_by="organisation_name asc",
		limit_page_length=limit,
	)

	return {"status": 1, "msg": organizations}

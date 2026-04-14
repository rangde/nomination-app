import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	custom_fields = {
		"User": [
			{
				"fieldname": "reports_to",
				"label": "Reports To",
				"fieldtype": "Link",
				"options": "User",
				"insert_after": "username",
				"translatable": 0,
			}
		],
	}

	create_custom_fields(custom_fields)

// Copyright (c) 2026, Aerele Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Nomination Form", {
	refresh(frm) {
		if (frm.is_new()) return;

		if (frappe.user.has_role("System Manager")) {
			frm.add_custom_button(__("View Credit Report"), () => {
				frappe.call({
					method: "nomination.api.credit_report.get_credit_report",
					args: { docname: frm.doc.name },
					callback(r) {
						if (r.message && r.message.pdf_base64) {
							const blob = b64_to_blob(r.message.pdf_base64, "application/pdf");
							const url = URL.createObjectURL(blob);
							window.open(url, "_blank");
						} else {
							frappe.msgprint(
								__("No credit report is available for this nomination.")
							);
						}
					},
				});
			});

			frm.add_custom_button(__("View Credit Report HTML"), () => {
				frappe.call({
					method: "nomination.api.credit_report.get_credit_report_html",
					args: { docname: frm.doc.name },
					callback(r) {
						if (r.message && r.message.html) {
							const d = new frappe.ui.Dialog({
								title: __("Credit Report"),
								size: "extra-large",
								fields: [{ fieldtype: "HTML", fieldname: "report" }],
							});
							d.fields_dict.report.$wrapper.html(r.message.html);
							d.show();
						} else {
							frappe.msgprint(
								__("No credit report is available for this nomination.")
							);
						}
					},
				});
			});
		}
	},
	farm_based(frm) {
		if (frm.doc.farm_based) {
			frm.set_value("non_farm", 0);

			frm.set_df_property("business_category", "options", [
				"Agriculture",
				"Dairy",
				"Goat rearing",
				"Poultry farming",
				"Mushroom cultivation",
				"Agri input shop",
			]);
		}
	},

	non_farm(frm) {
		if (frm.doc.non_farm) {
			frm.set_value("farm_based", 0);

			frm.set_df_property("business_category", "options", [
				"Tailoring",
				"Beauty Parlour",
				"Grocery Store",
				"Vegetable Vendor",
			]);
		}
	},
});

function b64_to_blob(b64_data, content_type) {
	const byte_chars = atob(b64_data);
	const byte_numbers = new Array(byte_chars.length);
	for (let i = 0; i < byte_chars.length; i++) {
		byte_numbers[i] = byte_chars.charCodeAt(i);
	}
	return new Blob([new Uint8Array(byte_numbers)], { type: content_type });
}

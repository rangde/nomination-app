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
						if (r.message && r.message.file_url) {
							window.open(r.message.file_url, "_blank");
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

// Copyright (c) 2026, Aerele Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Nomination Form", {
	refresh(frm) {
		if (frm.is_new()) return;

		if (frappe.user.has_role("System Manager")) {
			frm.add_custom_button(__("View Credit Report"), () => {
				frappe.call({
					method: "nomination.api.credit_report.get_credit_report_html",
					args: { docname: frm.doc.name },
					callback(r) {
						if (r.message && r.message.html) {
							const d = new frappe.ui.Dialog({
								title: __("Credit Report"),
								size: "extra-large",
								fields: [{ fieldtype: "HTML", fieldname: "report" }],
								primary_action_label: __("Print / Save as PDF"),
								primary_action() {
									print_credit_report(r.message.html);
								},
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

function print_credit_report(html) {
	// Render the report HTML with the browser's own engine (a hidden iframe) and
	// print it, so the user can "Save as PDF" with a faithful layout. wkhtmltopdf
	// clips/overlaps this complex CRIF HTML, so we avoid it for printing.
	const iframe = document.createElement("iframe");
	iframe.setAttribute("aria-hidden", "true");
	Object.assign(iframe.style, {
		position: "fixed",
		right: "0",
		bottom: "0",
		width: "0",
		height: "0",
		border: "0",
	});
	document.body.appendChild(iframe);

	const doc = iframe.contentWindow.document;
	doc.open();
	doc.write(html);
	doc.close();

	const trigger = () => {
		iframe.contentWindow.focus();
		iframe.contentWindow.print();
		setTimeout(() => iframe.remove(), 1000);
	};

	// Give the report (logo/images/styles) a moment to load before printing.
	if (doc.readyState === "complete") {
		setTimeout(trigger, 300);
	} else {
		iframe.onload = () => setTimeout(trigger, 300);
	}
}

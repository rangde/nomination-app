console.log("user_reporting.js loaded successfully!");

frappe.ui.form.on("User", {
	refresh(frm) {
		console.log("User form refresh triggered");

		if (!frm.is_new()) {
			console.log("Adding Reports To button");

			frm.add_custom_button(__("Reports To"), function () {
				console.log("Reports To button clicked");
				open_reporting_dialog(frm);
			});
		}
	},
});

function open_reporting_dialog(frm) {
	let role = "";
	let user_roles = frm.doc.roles ? frm.doc.roles.map((r) => r.role) : [];

	if (user_roles.includes("SHG")) {
		role = "VO";
	} else if (user_roles.includes("VO")) {
		role = "CLF";
	}

	let dialog = new frappe.ui.Dialog({
		title: __("Assign Reporting"),

		fields: [
			{
				label: __("Reports To"),
				fieldname: "reports_to",
				fieldtype: "Link",
				options: "User",
				reqd: 1,

				get_query: function () {
					return {
						query: "frappe.core.doctype.user.user.user_query",
						filters: {
							role: role,
						},
					};
				},
			},
		],

		primary_action_label: __("Save"),

		primary_action(values) {
			frappe.call({
				method: "frappe.client.insert",
				args: {
					doc: {
						doctype: "User Reporting",
						user: frm.doc.name,
						reports_to: values.reports_to,
					},
				},

				callback: function () {
					frappe.msgprint(__("Reporting assigned successfully"));
					dialog.hide();
					frm.reload_doc();
				},
			});
		},
	});

	dialog.show();
}

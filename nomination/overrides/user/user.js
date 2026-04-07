frappe.ui.form.on("User", {
	setup: function (frm) {
		frm.set_query("reports_to", function () {
			return {
				query: "nomination.overrides.user.user.get_approvers",
				filters: {
					roles: (frm.doc.roles || []).map((r) => r.role),
				},
			};
		});
	},
});

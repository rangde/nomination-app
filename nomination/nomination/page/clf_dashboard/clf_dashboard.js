frappe.pages["clf-dashboard"].on_page_load = function (wrapper) {
	let page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "CLF Dashboard",
		single_column: true,
	});

	page.main.html(`
		<div id="dashboard">
			<div class="section-header">
				<div class="section-bar" style="background:#378ADD"></div>
				<h3>Nomination Flow</h3>
			</div>
			<div id="nomination_flow" class="metrics-grid"></div>

			<div class="section-header" style="margin-top:2rem">
				<div class="section-bar" style="background:#1D9E75"></div>
				<h3>Training &amp; Assessment</h3>
			</div>
			<div id="training_flow" class="metrics-grid"></div>

			<div class="section-header" style="margin-top:2rem">
				<div class="section-bar" style="background:#BA7517"></div>
				<h3>Loan Process</h3>
			</div>
			<div id="loan_flow" class="metrics-grid"></div>
		</div>
	`);

	add_dashboard_style();
	load_dashboard();
	setInterval(load_dashboard, 30000);
};

function load_dashboard() {
	frappe.call({
		method: "nomination.api.dashboard.get_dashboard_metrics",
		callback: function (r) {
			if (!r.message) return;
			let data = r.message;
			render_nomination(data.nomination);
			render_training(data.training);
			render_loan(data.loan);
		},
		error: function () {
			frappe.msgprint(__("Unable to load dashboard metrics."));
		},
	});
}

function add_dashboard_style() {
	frappe.dom.set_style(`
		#dashboard {
			padding: 1.5rem 0.5rem;
		}

		#dashboard .section-header {
			display: flex;
			align-items: center;
			gap: 10px;
			margin: 0 0 1rem;
		}

		#dashboard .section-bar {
			width: 4px;
			height: 20px;
			border-radius: 2px;
			flex-shrink: 0;
		}

		#dashboard h3 {
			font-size: 12px !important;
			font-weight: 500 !important;
			letter-spacing: 0.07em;
			text-transform: uppercase;
			color: var(--text-muted) !important;
			margin: 0 !important;
		}

		.metrics-grid {
			display: grid;
			grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
			gap: 10px;
			margin-bottom: 2.5rem;
		}

		.metric-card {
			background: var(--card-bg);
			border: 0.5px solid var(--border-color);
			border-radius: 8px;
			padding: 1rem 1.25rem;
			border-left-width: 3px;
		}

		.metric-card.blue  { border-left-color: #378ADD; }
		.metric-card.teal  { border-left-color: #1D9E75; }
		.metric-card.amber { border-left-color: #BA7517; }

		.metric-title {
			font-size: 12px;
			color: var(--text-muted);
			letter-spacing: 0.02em;
			margin-bottom: 8px;
		}

		.metric-value {
			font-size: 30px;
			font-weight: 500;
			color: var(--text-color);
			line-height: 1;
		}
	`);
}

function card(title, value, color) {
	return `
		<div class="metric-card ${color || ""}">
			<div class="metric-title">${title}</div>
			<div class="metric-value">${value || 0}</div>
		</div>`;
}

function render_nomination(data) {
	let html = "";
	html += card("SHG Approved", data.shg_approved, "blue");
	html += card("VO Pending", data.vo_pending, "blue");
	html += card("VO Approved", data.vo_approved, "blue");
	html += card("CLF Pending", data.clf_pending, "blue");
	html += card("CLF Approved", data.clf_approved, "blue");
	$("#nomination_flow").html(html);
}

function render_training(data) {
	let html = "";
	html += card("Total Registered", data.total_registered, "teal");
	html += card("Under Training", data.under_training, "teal");
	html += card("Passed", data.passed, "teal");
	html += card("Failed", data.failed, "teal");
	$("#training_flow").html(html);
}

function render_loan(data) {
	let html = "";
	html += card("Loan Applicants", data.loan_applicants, "amber");
	html += card("Loan Disbursed", data.loan_disbursed, "amber");
	html += card("Amount Disbursed", data.amount_disbursed, "amber");
	html += card("Median Days", data.median_days, "amber");
	$("#loan_flow").html(html);
}

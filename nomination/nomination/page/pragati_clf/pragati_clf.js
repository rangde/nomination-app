frappe.pages["pragati-clf"].on_page_load = function (wrapper) {
	let page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "Pragati CLF Dashboard",
		single_column: true,
	});

	page.main.html(`
		<div id="dashboard">

			<h3>Nomination Flow</h3>
			<div id="nomination_flow" class="metrics-grid"></div>

			<h3 style="margin-top:40px">Training & Assessment</h3>
			<div id="training_flow" class="metrics-grid"></div>

			<h3 style="margin-top:40px">Loan Process</h3>
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
			let data = r.message;

			render_nomination(data.nomination);
			render_training(data.training);
			render_loan(data.loan);
		},
	});
}

function add_dashboard_style() {
	frappe.dom.set_style(`
	.metrics-grid{
		display:grid;
		grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
		gap:20px;
		margin-top:15px;
	}

	.metric-card{
		border:1px solid var(--border-color);
		border-radius:10px;
		padding:20px;
		background:var(--card-bg);
		text-align:center;
	}

	.metric-title{
		font-size:14px;
		color:var(--text-muted);
	}

	.metric-value{
		font-size:38px;
		font-weight:700;
		margin-top:10px;
		color:var(--text-color);
	}
	`);
}

function card(title, value) {
	return `
	<div class="metric-card">

		<div class="metric-title">
			${title}
		</div>

		<div class="metric-value">
			${value || 0}
		</div>

	</div>
	`;
}

function render_nomination(data) {
	let html = "";

	html += card("SHG Approved", data.shg_approved);
	html += card("VO Pending", data.vo_pending);
	html += card("VO Approved", data.vo_approved);
	html += card("CLF Pending", data.clf_pending);
	html += card("CLF Approved", data.clf_approved);

	$("#nomination_flow").html(html);
}

function render_training(data) {
	let html = "";

	html += card("Total Registered", data.total_registered);
	html += card("Under Training", data.under_training);
	html += card("Passed", data.passed);
	html += card("Failed", data.failed);

	$("#training_flow").html(html);
}

function render_loan(data) {
	let html = "";

	html += card("Loan Applicants", data.loan_applicants);
	html += card("Loan Disbursed", data.loan_disbursed);
	html += card("Amount Disbursed", data.amount_disbursed);
	html += card("Median Days", data.median_days);

	$("#loan_flow").html(html);
}

frappe.pages["clf-dashboard"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "CLF Dashboard",
		single_column: true,
	});

	page.main.html(`
		<div id="clf-dashboard-root">
			<div class="abh-bg-glow abh-bg-glow-one" aria-hidden="true"></div>
			<div class="abh-bg-glow abh-bg-glow-two" aria-hidden="true"></div>
			<div class="abh-bg-glow abh-bg-glow-three" aria-hidden="true"></div>
			<div class="abh-shell">
				<header class="abh-header">
					<button class="abh-header-back" type="button" data-action="back-dashboard">
						<span aria-hidden="true">←</span>
						<span data-i18n="back_dashboard">Dashboard</span>
					</button>
					<div class="abh-brand">
						<div class="abh-brand-mark" aria-hidden="true">अ</div>
						<h1 data-i18n="title">CLF Dashboard</h1>
					</div>
					<div class="abh-actions">
						<button class="abh-refresh" type="button" data-action="refresh">
							<span class="abh-refresh-icon">↻</span>
							<span>
								<strong data-i18n="refresh">Refresh</strong>
								<small id="abh-header-updated">-</small>
							</span>
						</button>
						<div class="abh-lang" role="group" aria-label="Language">
							<button data-lang="hi">हिंदी</button>
							<button class="active" data-lang="en">English</button>
						</div>
					</div>
				</header>

				<div id="abh-dashboard-view">
					<section class="abh-overview">
						<div>
							<h2 data-i18n="overview_title">Dashboard — At a Glance</h2>
							<p data-i18n="overview_body">The same didi moves through all three stages: nomination, training, then loan. Tap any number to follow her.</p>
						</div>
						<button class="abh-browse" type="button" data-action="browse-village">
							<span aria-hidden="true">⌾</span>
							<span data-i18n="browse_village">Browse all didis by village</span>
						</button>
					</section>

					<section class="abh-section abh-flow-section">
						<div class="abh-section-head abh-flow-head">
							<span class="abh-flow-icon" aria-hidden="true">
								<span></span><span></span><span></span>
							</span>
							<h2 data-i18n="nomination_heading">Nomination Journey</h2>
						</div>
						<div id="abh-nomination" class="abh-flow-track"></div>
					</section>

					<div class="abh-connector" id="abh-connector-training"></div>

					<section class="abh-section abh-training-section">
						<div class="abh-section-head">
							<span class="abh-dot green">${clf_dashboard.icon("training_stage")}</span>
							<h2 data-i18n="training_heading">Training & Assessment</h2>
						</div>
						<div id="abh-training" class="abh-metric-grid"></div>
					</section>

					<div class="abh-connector" id="abh-connector-loan"></div>

					<section class="abh-section abh-loan-section">
						<div class="abh-section-head">
							<span class="abh-dot amber">${clf_dashboard.icon("loan_stage")}</span>
							<h2 data-i18n="loan_heading">Loan Process</h2>
						</div>
						<div id="abh-loan" class="abh-metric-grid"></div>
					</section>
				</div>

				<div id="abh-list-view" style="display:none"></div>
				<div id="abh-detail-modal" style="display:none"></div>
				<div id="abh-filter-sheet" style="display:none"></div>
			</div>
		</div>
	`);

	add_clf_dashboard_style();
	clf_dashboard.bind_events();
	clf_dashboard.apply_route_state();
	clf_dashboard.load();
	clf_dashboard.interval = setInterval(() => clf_dashboard.load(), 30000);

	$(wrapper).on("remove", () => {
		clearInterval(clf_dashboard.interval);
		$(document).off("click.clf-dashboard-root");
	});
};

frappe.pages["clf-dashboard"].on_page_show = function () {
	if ($("#clf-dashboard-root").length) {
		clf_dashboard.apply_route_state();
	}
};

const clf_dashboard = {
	lang: "en",
	interval: null,
	data: null,
	view: "dashboard",
	stageKey: "shg_approved",
	page: 1,
	pageSize: 20,
	pageSizeOptions: [20, 100, 500, 2500],
	stageKeys: ["all", "shg_approved", "vo_pending", "vo_approved", "clf_pending", "clf_approved"],
	counterFrame: null,
	search: "",
	vo: "",
	shg: "",
	sortBy: "modified",
	listData: { rows: [], total: 0, vos: [], shgs: [], page: 1, page_size: 20 },
	searchTimer: null,
	labels: {
		en: {
			kicker: "CLF Overview",
			title: "CLF Dashboard",
			subtitle: "Track nomination, training and loan progress from one view.",
			refresh: "Refresh",
			overview_title: "Dashboard — At a Glance",
			overview_body:
				"The same didi moves through all three stages: nomination, training, then loan. Tap any number to follow her.",
			browse_village: "Browse all didis by village",
			last_updated: "Last updated",
			nomination_heading: "Nomination Flow",
			training_heading: "Training & Assessment",
			loan_heading: "Loan Process",
			shg_approved: "SHG Approved",
			vo_pending: "VO Pending",
			vo_approved: "VO Approved",
			clf_pending: "CLF Pending",
			clf_approved: "CLF Approved",
			total_registered: "Total Registered",
			under_training: "Under Training",
			passed: "Passed",
			failed: "Failed",
			loan_applicants: "Loan Applicants",
			loan_disbursed: "Loan Disbursed",
			amount_disbursed: "Amount Disbursed",
			median_days: "Median Days",
			training_connector: "{0} of {1} CLF-approved didis have entered training",
			loan_connector: "{0} of {1} didis who passed have received a loan",
			open_list: "Open list",
			view_details: "View details",
			unavailable: "Not available",
			back_dashboard: "Dashboard",
			all: "All",
			all_nomination: "All Nomination",
			nomination_tab: "Nomination",
			training_tab: "Training & Assessment",
			loan_tab: "Loan Process",
			all_vos: "All VOs",
			all_shgs: "All SHGs",
			search_placeholder: "Search name or village",
			last_updated_sort: "Last Updated",
			date_created_sort: "Date Created",
			stage: "Stage",
			status: "Status",
			last_updated_card: "Last Updated",
			didis: "Didis",
			group: "Group",
			vo: "VO",
			nominated_on: "Nominated On",
			days_ago: "Days Ago",
			training_pending: "She will enter training after CLF approval.",
			loan_pending: "Loan details will appear after training and assessment.",
			not_yet: "Not Yet",
			prev: "Prev",
			next: "Next",
			showing_range: "{0} - {1} of {2}",
			no_records: "No records found.",
		},
		hi: {
			kicker: "CLF अवलोकन",
			title: "CLF डैशबोर्ड",
			subtitle: "नामांकन, प्रशिक्षण और लोन की प्रगति एक जगह देखें।",
			refresh: "रिफ्रेश",
			overview_title: "एक नज़र में",
			overview_body: "हर दीदी की यात्रा नामांकन मंजूरी से प्रशिक्षण और लोन तक देखें।",
			browse_village: "गाँव के अनुसार सभी दीदी देखें",
			last_updated: "अंतिम अपडेट",
			nomination_heading: "नामांकन फ्लो",
			training_heading: "प्रशिक्षण और मूल्यांकन",
			loan_heading: "लोन प्रक्रिया",
			shg_approved: "समूह से मंजूर",
			vo_pending: "VO लंबित",
			vo_approved: "VO से मंजूर",
			clf_pending: "CLF लंबित",
			clf_approved: "CLF से मंजूर",
			total_registered: "कुल नाम दर्ज",
			under_training: "प्रशिक्षण चल रहा",
			passed: "पास",
			failed: "फेल",
			loan_applicants: "लोन आवेदन",
			loan_disbursed: "लोन दिए गए",
			amount_disbursed: "कुल राशि",
			median_days: "औसत दिन",
			training_connector: "{1} CLF-स्वीकृत में से {0} दीदी प्रशिक्षण में हैं।",
			loan_connector: "पास हुई {1} में से {0} दीदी को लोन मिला।",
			open_list: "सूची खोलें",
			view_details: "विवरण देखें",
			unavailable: "उपलब्ध नहीं",
			back_dashboard: "डैशबोर्ड",
			all: "सभी",
			all_nomination: "सभी नामांकन",
			nomination_tab: "नामांकन",
			training_tab: "प्रशिक्षण और मूल्यांकन",
			loan_tab: "लोन प्रक्रिया",
			all_vos: "सभी VO",
			all_shgs: "सभी समूह",
			search_placeholder: "नाम या गाँव खोजें",
			last_updated_sort: "अंतिम अपडेट",
			date_created_sort: "नाम जोड़ने की तारीख",
			stage: "चरण",
			status: "स्थिति",
			last_updated_card: "अंतिम अपडेट",
			didis: "दीदी",
			group: "समूह",
			vo: "VO",
			nominated_on: "नामांकित तारीख",
			days_ago: "दिन पहले",
			training_pending: "CLF मंजूरी के बाद प्रशिक्षण शुरू होगा।",
			loan_pending: "प्रशिक्षण और मूल्यांकन के बाद लोन विवरण दिखेगा।",
			not_yet: "अभी नहीं",
			prev: "पिछला",
			next: "आगे",
			showing_range: "{0} - {1} / {2}",
			no_records: "कोई रिकॉर्ड नहीं मिला।",
		},
	},

	t(key) {
		return this.labels[this.lang][key] || this.labels.en[key] || key;
	},

	bind_events() {
		$("#clf-dashboard-root").on("click", "[data-lang]", (event) => {
			this.lang = $(event.currentTarget).data("lang");
			$("#clf-dashboard-root [data-lang]").removeClass("active");
			$(event.currentTarget).addClass("active");
			this.render_current_view();
		});

		$("#clf-dashboard-root").on("click", "[data-action='refresh']", () => this.load(true));

		$("#clf-dashboard-root").on("click", "[data-action='browse-village']", () =>
			this.open_list("all")
		);

		$("#clf-dashboard-root").on("click", ".abh-flow-step", (event) => {
			event.preventDefault();
			this.open_list($(event.currentTarget).data("stage"));
		});

		$("#clf-dashboard-root").on("click", "[data-action='back-dashboard']", () => {
			if (this.view !== "list") return;
			this.view = "dashboard";
			$("#clf-dashboard-root").removeClass("abh-list-mode");
			$("#abh-list-view").hide();
			$("#abh-dashboard-view").show();
			this.update_dashboard_route();
			this.render();
		});

		$("#clf-dashboard-root").on("click", "[data-stage-tab]", (event) => {
			this.stageKey = $(event.currentTarget).data("stage-tab");
			this.page = 1;
			this.load_list();
		});

		$("#clf-dashboard-root").on("click", "[data-sheet-toggle]", (event) => {
			event.stopPropagation();
			const type = $(event.currentTarget).data("sheet-toggle");
			this.open_filter_sheet(type);
		});

		$("#clf-dashboard-root").on("click", "[data-dropdown-option]", (event) => {
			event.stopPropagation();
			const type = $(event.currentTarget).data("dropdown-type");
			const value = String($(event.currentTarget).data("value") || "");

			if (type === "stage") {
				this.stageKey = this.normalize_stage(value) || "all";
			} else {
				this[type] = value;
			}

			this.close_filter_sheet();
			this.page = 1;
			this.load_list();
		});

		$("#clf-dashboard-root").on(
			"click",
			"[data-action='close-filter-sheet'], .abh-sheet-backdrop",
			() => this.close_filter_sheet()
		);

		$("#clf-dashboard-root").on("click", ".abh-sheet-panel", (event) =>
			event.stopPropagation()
		);

		$("#clf-dashboard-root").on("input", "[data-filter='search']", (event) => {
			this.search = event.currentTarget.value;
			this.page = 1;
			clearTimeout(this.searchTimer);
			this.searchTimer = setTimeout(() => this.load_list(), 250);
		});

		$("#clf-dashboard-root").on("click", "[data-sort]", (event) => {
			this.sortBy = $(event.currentTarget).data("sort");
			this.page = 1;
			this.load_list();
		});

		$("#clf-dashboard-root").on("click", "[data-page]", (event) => {
			this.page = Number($(event.currentTarget).data("page"));
			this.load_list();
		});

		$("#clf-dashboard-root").on("click", "[data-page-size]", (event) => {
			this.pageSize = Number($(event.currentTarget).data("page-size"));
			this.page = 1;
			this.load_list();
		});

		$("#clf-dashboard-root").on("click", ".abh-list-card", (event) => {
			const name = $(event.currentTarget).data("name");
			const row = this.listData.rows.find((item) => item.name === name);
			if (row) this.open_modal(row);
		});

		$("#clf-dashboard-root").on(
			"click",
			"[data-action='close-modal'], .abh-modal-backdrop",
			() => {
				this.close_modal();
			}
		);

		$("#clf-dashboard-root").on("click", ".abh-modal-card", (event) =>
			event.stopPropagation()
		);
	},

	open_list(stageKey) {
		this.view = "list";
		$("#clf-dashboard-root").addClass("abh-list-mode");
		this.stageKey = this.normalize_stage(stageKey) || "shg_approved";
		this.page = 1;
		this.search = "";
		this.vo = "";
		this.shg = "";
		this.sortBy = "modified";
		$("#abh-dashboard-view").hide();
		$("#abh-list-view").show();
		this.load_list();
	},

	open_filter_sheet(type) {
		const config = this.filter_sheet_config(type);
		if (!config) return;

		$("#abh-filter-sheet")
			.html(
				`
			<div class="abh-sheet-backdrop">
				<div class="abh-sheet-panel" role="dialog" aria-modal="true">
					<div class="abh-sheet-head">
						<h2>${frappe.utils.escape_html(config.title)}</h2>
						<button type="button" data-action="close-filter-sheet">×</button>
					</div>
					<div class="abh-sheet-options">
						${config.options
							.map((option) => {
								const active =
									String(option.value) === String(config.selected || "");
								return `<button class="abh-sheet-option ${
									active ? "active" : ""
								}" type="button" data-dropdown-type="${frappe.utils.escape_html(
									type
								)}" data-dropdown-option data-value="${frappe.utils.escape_html(
									option.value
								)}">
									<span class="abh-sheet-dot ${this.option_tone(option.value)} ${active ? "active" : ""}"></span>
									<span>${frappe.utils.escape_html(option.label)}</span>
									<span class="abh-sheet-check" aria-hidden="true">✓</span>
								</button>`;
							})
							.join("")}
					</div>
				</div>
			</div>`
			)
			.show();
	},

	close_filter_sheet() {
		$("#abh-filter-sheet").hide().empty();
	},

	load_list() {
		this.update_list_route();
		$("#abh-list-view").html(
			`<div class="abh-list-loading-wrap"><div class="abh-list-loading">Loading...</div></div>`
		);

		frappe.call({
			method: "nomination.api.dashboard.get_dashboard_nomination_rows",
			args: {
				stage_key: this.stageKey,
				page: this.page,
				page_size: this.pageSize,
				search: this.search,
				vo: this.vo,
				shg: this.shg,
				sort_by: this.sortBy,
			},
			callback: (r) => {
				const payload = r.message && r.message.status ? r.message.msg : null;
				this.listData = payload || {
					rows: [],
					total: 0,
					vos: [],
					shgs: [],
					page: 1,
					page_size: this.pageSize,
				};
				this.render_list();
			},
			error: () => {
				frappe.msgprint(__("Unable to load nominations."));
			},
		});
	},

	load(spin) {
		if (spin) $("#clf-dashboard-root .abh-refresh-icon").addClass("spinning");

		frappe.call({
			method: "nomination.api.dashboard.get_dashboard_metrics",
			callback: (r) => {
				$("#clf-dashboard-root .abh-refresh-icon").removeClass("spinning");
				if (!r.message) return;
				this.data = r.message;
				this.render();
			},
			error: () => {
				$("#clf-dashboard-root .abh-refresh-icon").removeClass("spinning");
				frappe.msgprint(__("Unable to load dashboard metrics."));
			},
		});
	},

	render() {
		this.apply_labels();
		if (!this.data) return;

		const updatedAt = this.format_time(new Date());
		$("#abh-header-updated").text(updatedAt);
		this.render_nomination(this.data.nomination || {});
		this.render_training(this.data.training || {});
		this.render_loan(this.data.loan || {});
		this.animate_counters();
	},

	render_current_view() {
		if (this.view === "list") {
			this.render_list();
			return;
		}
		this.render();
	},

	apply_route_state() {
		const state = this.get_route_state();
		if (state.view !== "list") return;

		this.view = "list";
		this.stageKey = state.stageKey;
		this.page = state.page;
		this.pageSize = state.pageSize;
		this.search = state.search;
		this.vo = state.vo;
		this.shg = state.shg;
		this.sortBy = state.sortBy;
		$("#clf-dashboard-root").addClass("abh-list-mode");
		$("#abh-dashboard-view").hide();
		$("#abh-list-view").show();
		this.load_list();
	},

	get_route_state() {
		const params = new URLSearchParams(window.location.search || "");
		const route = frappe.get_route ? frappe.get_route().map((part) => String(part)) : [];
		const pathParts = window.location.pathname
			.split("/")
			.filter(Boolean)
			.map((part) => decodeURIComponent(part));
		const pagePathIndex = pathParts.indexOf("clf-dashboard");
		const routeParts = route[0] === "clf-dashboard" ? route.slice(1) : route;
		const pagePathParts = pagePathIndex === -1 ? [] : pathParts.slice(pagePathIndex + 1);
		const routeStage = [...routeParts, ...pagePathParts].find((part) =>
			this.normalize_stage(part)
		);
		const stageKey =
			this.normalize_stage(params.get("stage")) || this.normalize_stage(routeStage);
		const hasListRoute =
			params.get("view") === "list" ||
			routeParts.includes("list") ||
			pagePathParts.includes("list") ||
			!!stageKey;

		if (!hasListRoute) {
			return { view: "dashboard" };
		}

		const page = Math.max(1, Number(params.get("page")) || 1);
		const pageSize = this.pageSizeOptions.includes(Number(params.get("page_size")))
			? Number(params.get("page_size"))
			: this.pageSize;
		const sortBy = ["modified", "created"].includes(params.get("sort_by"))
			? params.get("sort_by")
			: "modified";

		return {
			view: "list",
			stageKey: stageKey || "shg_approved",
			page,
			pageSize,
			search: params.get("search") || "",
			vo: params.get("vo") || "",
			shg: params.get("shg") || "",
			sortBy,
		};
	},

	normalize_stage(stageKey) {
		const normalized = String(stageKey || "").replace(/-/g, "_");
		return this.stageKeys.includes(normalized) ? normalized : "";
	},

	update_dashboard_route() {
		this.replace_route("/app/clf-dashboard");
	},

	update_list_route() {
		if (this.view !== "list") return;
		const params = new URLSearchParams();
		params.set("view", "list");
		params.set("stage", this.stageKey);
		if (this.page > 1) params.set("page", String(this.page));
		if (this.pageSize !== 20) params.set("page_size", String(this.pageSize));
		if (this.search) params.set("search", this.search);
		if (this.vo) params.set("vo", this.vo);
		if (this.shg) params.set("shg", this.shg);
		if (this.sortBy !== "modified") params.set("sort_by", this.sortBy);
		this.replace_route(`/app/clf-dashboard?${params.toString()}`);
	},

	replace_route(url) {
		if (window.location.pathname + window.location.search !== url) {
			window.history.replaceState(null, "", url);
		}
	},

	apply_labels() {
		$("#clf-dashboard-root [data-i18n]").each((_, el) => {
			const key = $(el).data("i18n");
			$(el).text(this.t(key));
		});
	},

	render_nomination(data) {
		const cards = [
			this.nomination_card("shg_approved", data.shg_approved, "blue", [
				["Nomination Form", "workflow_state", "=", "SHG Proposed"],
			]),
			this.nomination_card("vo_pending", data.vo_pending, "gray", [
				["Nomination Form", "workflow_state", "=", "SHG Proposed"],
			]),
			this.nomination_card("vo_approved", data.vo_approved, "blue", [
				["Nomination Form", "workflow_state", "=", "VO Approved"],
			]),
			this.nomination_card("clf_pending", data.clf_pending, "gray", [
				["Nomination Form", "workflow_state", "=", "VO Approved"],
			]),
			this.nomination_card("clf_approved", data.clf_approved, "green", [
				["Nomination Form", "workflow_state", "=", "CLF Approved"],
			]),
		];

		$("#abh-nomination").html(cards.join(""));
	},

	render_training(data) {
		const total = this.num(data.total_registered);
		const entered = this.num(data.under_training);
		const passed = this.num(data.passed);
		const clfApproved = this.num(this.data?.nomination?.clf_approved);

		$("#abh-connector-training").text(
			this.t("training_connector")
				.replace("{0}", this.format_number(entered || total))
				.replace("{1}", this.format_number(clfApproved))
		);

		$("#abh-training").html(
			[
				this.metric_card("total_registered", total, "gray", "ID"),
				this.metric_card("under_training", entered, "amber", "TR"),
				this.metric_card("passed", passed, "green", "OK"),
				this.metric_card("failed", data.failed, "red", "NO"),
			].join("")
		);
	},

	render_loan(data) {
		const disbursed = this.num(data.loan_disbursed);
		const amount = this.money(data.amount_disbursed);
		const passed = this.num(this.data?.training?.passed);

		$("#abh-connector-loan").text(
			this.t("loan_connector")
				.replace("{0}", this.format_number(disbursed))
				.replace("{1}", this.format_number(passed))
		);

		$("#abh-loan").html(
			[
				this.metric_card("loan_applicants", data.loan_applicants, "amber", "AP"),
				this.metric_card("loan_disbursed", data.loan_disbursed, "blue", "LD"),
				this.metric_card("amount_disbursed", amount, "green", "₹"),
				this.metric_card("median_days", data.median_days, "gray", "DY"),
			].join("")
		);
	},

	render_list() {
		const total = this.num(this.listData.total);
		const totalPages = Math.max(1, Math.ceil(total / this.pageSize));
		const rangeStart = total ? (this.page - 1) * this.pageSize + 1 : 0;
		const rangeEnd = Math.min(this.page * this.pageSize, total);
		const title = this.t(this.stageKey);
		const rows = this.listData.rows || [];

		$("#abh-list-view").html(`
			<div class="abh-list-page">
				<div class="abh-list-top">
					<div class="abh-list-summary">
						<div class="abh-list-total"><strong>${this.format_number(
							total
						)}</strong><span>${frappe.utils.escape_html(this.t("didis"))}</span></div>
						<div class="abh-page-size abh-page-size-top">
							${this.page_size_buttons()}
						</div>
					</div>
				</div>

				<h1 class="abh-list-title">${frappe.utils.escape_html(title)}</h1>

				<div class="abh-tabs-row">
					<div class="abh-tabs">
						<button class="abh-tab ${
							this.stageKey === "all" ? "active" : ""
						}" type="button" data-stage-tab="all">${frappe.utils.escape_html(
			this.t("all")
		)}</button>
						<button class="abh-tab ${
							this.stageKey !== "all" ? "active" : ""
						}" type="button" data-stage-tab="shg_approved">${frappe.utils.escape_html(
			this.t("nomination_tab")
		)}</button>
						<button class="abh-tab" type="button" disabled>${frappe.utils.escape_html(
							this.t("training_tab")
						)}</button>
						<button class="abh-tab" type="button" disabled>${frappe.utils.escape_html(
							this.t("loan_tab")
						)}</button>
					</div>
				</div>

				<div class="abh-list-rule"></div>

				<div class="abh-filter-row">
					${this.stage_select()}
					${this.option_select("vo", this.t("all_vos"), this.listData.vos || [], this.vo)}
					${this.option_select("shg", this.t("all_shgs"), this.listData.shgs || [], this.shg)}
					<label class="abh-search">
						<span>⌕</span>
						<input data-filter="search" value="${frappe.utils.escape_html(
							this.search
						)}" placeholder="${frappe.utils.escape_html(
			this.t("search_placeholder")
		)}">
					</label>
				</div>

				<div class="abh-list-tools">
					<div class="abh-sort">
						<button class="${
							this.sortBy === "modified" ? "active" : ""
						}" type="button" data-sort="modified">${frappe.utils.escape_html(
			this.t("last_updated_sort")
		)}</button>
						<button class="${
							this.sortBy === "created" ? "active" : ""
						}" type="button" data-sort="created">${frappe.utils.escape_html(
			this.t("date_created_sort")
		)}</button>
					</div>
				</div>

				<div class="abh-card-grid">
					${
						rows.length
							? rows.map((row, index) => this.list_card(row, index)).join("")
							: `<div class="abh-empty">${frappe.utils.escape_html(
									this.t("no_records")
							  )}</div>`
					}
				</div>

				<div class="abh-pager">
					<button type="button" ${this.page <= 1 ? "disabled" : ""} data-page="${
			this.page - 1
		}">${frappe.utils.escape_html(this.t("prev"))}</button>
					<span>${frappe.utils.escape_html(
						this.t("showing_range")
							.replace("{0}", this.format_number(rangeStart))
							.replace("{1}", this.format_number(rangeEnd))
							.replace("{2}", this.format_number(total))
					)}</span>
					<button type="button" ${this.page >= totalPages ? "disabled" : ""} data-page="${
			this.page + 1
		}">${frappe.utils.escape_html(this.t("next"))}</button>
				</div>
			</div>
		`);
	},

	page_size_buttons() {
		return this.pageSizeOptions
			.map(
				(size) =>
					`<button class="${
						this.pageSize === size ? "active" : ""
					}" type="button" data-page-size="${size}">${this.format_number(size)}</button>`
			)
			.join("");
	},

	stage_select() {
		const config = this.filter_sheet_config("stage");
		return this.custom_select("stage", this.t(this.stageKey), config.options, this.stageKey);
	},

	option_select(key, placeholder, options, selected) {
		const items = [
			{ value: "", label: placeholder },
			...options.map((option) => ({ value: option, label: option })),
		];
		const label = selected || placeholder;
		return this.custom_select(key, label, items, selected);
	},

	filter_sheet_config(type) {
		if (type === "stage") {
			return {
				title: this.lang === "hi" ? "स्थिति चुनें" : "Choose Status",
				selected: this.stageKey,
				options: ["all", "shg_approved", "vo_approved", "clf_approved"].map((key) => ({
					value: key,
					label: key === "all" ? this.t("all_nomination") : this.t(key),
				})),
			};
		}

		if (type === "vo") {
			return {
				title: this.t("all_vos"),
				selected: this.vo,
				options: [
					{ value: "", label: this.t("all_vos") },
					...(this.listData.vos || []).map((option) => ({
						value: option,
						label: option,
					})),
				],
			};
		}

		if (type === "shg") {
			return {
				title: this.t("all_shgs"),
				selected: this.shg,
				options: [
					{ value: "", label: this.t("all_shgs") },
					...(this.listData.shgs || []).map((option) => ({
						value: option,
						label: option,
					})),
				],
			};
		}

		return null;
	},

	option_tone(value) {
		if (value === "shg_approved" || value === "vo_approved") return "blue";
		if (value === "clf_approved") return "green";
		return "";
	},

	custom_select(type, label, options, selected) {
		return `
			<div class="abh-select-wrap">
				<button class="abh-select-btn" type="button" data-sheet-toggle="${frappe.utils.escape_html(type)}">
					<span>${frappe.utils.escape_html(label)}</span>
					<i aria-hidden="true"></i>
				</button>
			</div>`;
	},

	list_card(row, index = 0) {
		const name = this.full_name(row);
		const updated = this.date_label(row.modified);
		const statusKey = this.row_status_key(row);
		const stageLabel = this.t("nomination_tab");
		const stageIcon = this.icon("nomination_stage");
		const delayMs = Math.min(index, 11) * 35;
		return `
			<button class="abh-list-card" type="button" style="--abh-card-delay:${delayMs}ms" data-name="${frappe.utils.escape_html(
			row.name
		)}">
				<div class="abh-card-main">
					<div>
						<h3>${frappe.utils.escape_html(name)}</h3>
						<div class="abh-village">${this.icon("home")} ${frappe.utils.escape_html(
			row.townvillage || "-"
		)}</div>
					</div>
					${this.avatar(row)}
				</div>
				<div class="abh-card-kicker">${frappe.utils.escape_html(this.t("stage"))}</div>
				<div class="abh-card-stage"><span class="abh-mini-chart">${stageIcon}</span>${frappe.utils.escape_html(
			stageLabel
		)}</div>
				<div class="abh-card-kicker">${frappe.utils.escape_html(this.t("status"))}</div>
				<div class="abh-status-pill"><span></span>${frappe.utils.escape_html(this.t(statusKey))}</div>
				<div class="abh-card-footer">
					<div>
						<strong>${this.icon("median_days")} ${frappe.utils.escape_html(updated)}</strong>
						<span>${frappe.utils.escape_html(this.t("last_updated_card"))}</span>
					</div>
				</div>
			</button>`;
	},

	open_modal(row) {
		$("#abh-detail-modal")
			.html(
				`
			<div class="abh-modal-backdrop">
				<div class="abh-modal-card">
					<button class="abh-modal-close" type="button" data-action="close-modal">×</button>
					<div class="abh-modal-person">
						${this.avatar(row)}
						<div>
							<h2>${frappe.utils.escape_html(this.full_name(row))}</h2>
							<p>${frappe.utils.escape_html(row.townvillage || "-")} · ${frappe.utils.escape_html(
					row.name_of_the_shg || "-"
				)}</p>
						</div>
					</div>
					${this.modal_section(
						"nomination_tab",
						this.stageKey,
						[
							[this.t("group"), row.name_of_the_shg || "-"],
							[this.t("vo"), row.name_of_the_vo || "-"],
							[this.t("nominated_on"), this.date_label(row.creation)],
							[this.t("days_ago"), `${this.days_ago(row.creation)} days`],
						],
						true
					)}
					${this.modal_section("training_tab", "not_yet", [[this.t("training_pending"), ""]], false)}
					${this.modal_section("loan_tab", "not_yet", [[this.t("loan_pending"), ""]], false)}
				</div>
			</div>
		`
			)
			.show();
	},

	close_modal() {
		$("#abh-detail-modal").hide().empty();
	},

	modal_section(titleKey, chipKey, pairs, active) {
		const iconKey =
			titleKey === "training_tab"
				? "training_stage"
				: titleKey === "loan_tab"
				? "loan_stage"
				: "nomination_stage";
		return `
			<div class="abh-modal-section ${active ? "active" : ""}">
				<div class="abh-modal-section-head">
					<div class="abh-card-stage"><span class="abh-mini-chart">${this.icon(
						iconKey
					)}</span>${frappe.utils.escape_html(this.t(titleKey))}</div>
					<div class="abh-status-pill ${active ? "" : "muted"}">${frappe.utils.escape_html(
			this.t(chipKey)
		)}</div>
				</div>
				${pairs
					.map((pair) =>
						pair[1]
							? `<div class="abh-kv"><span>${frappe.utils.escape_html(
									pair[0]
							  )}</span><strong>${frappe.utils.escape_html(pair[1])}</strong></div>`
							: `<p class="abh-muted-note">${frappe.utils.escape_html(pair[0])}</p>`
					)
					.join("")}
			</div>`;
	},

	avatar(row) {
		if (row.photo_of_didi) {
			return `<img class="abh-avatar" src="${frappe.utils.escape_html(
				row.photo_of_didi
			)}" alt="">`;
		}
		const initials = this.full_name(row)
			.split(/\s+/)
			.map((part) => part[0])
			.join("")
			.slice(0, 2)
			.toUpperCase();
		return `<div class="abh-avatar abh-avatar-fallback">${frappe.utils.escape_html(
			initials || "D"
		)}</div>`;
	},

	full_name(row) {
		return `${row.first_name || ""} ${row.last_name || ""}`.trim() || row.name || "-";
	},

	row_status_key(row) {
		if (this.stageKey !== "all") return this.stageKey;
		if (row.workflow_state === "VO Approved") return "vo_approved";
		if (row.workflow_state === "CLF Approved") return "clf_approved";
		return "shg_approved";
	},

	date_label(value) {
		if (!value) return "-";
		return new Date(String(value).replace(" ", "T")).toLocaleDateString("en-IN", {
			day: "2-digit",
			month: "short",
			year: "numeric",
		});
	},

	days_ago(value) {
		if (!value) return 0;
		const date = new Date(String(value).replace(" ", "T"));
		if (Number.isNaN(date.getTime())) return 0;
		return Math.max(0, Math.floor((Date.now() - date.getTime()) / 86400000));
	},

	nomination_card(label_key, value, tone, filters) {
		const href = `/app/nomination-form?filters=${encodeURIComponent(JSON.stringify(filters))}`;
		const target = this.num(value);
		return `
			<a class="abh-flow-step ${tone}" data-stage="${label_key}" href="${href}" title="${frappe.utils.escape_html(
			this.t("open_list")
		)}">
				<div class="abh-flow-node">
					<div class="abh-flow-stage-icon">${this.icon(label_key)}</div>
					<div class="abh-flow-count" data-count-target="${target}">0</div>
				</div>
				<div class="abh-flow-label">${frappe.utils.escape_html(this.t(label_key))}</div>
			</a>`;
	},

	metric_card(label_key, value, tone, icon) {
		const numeric = typeof value !== "string";
		const display = numeric ? 0 : value;
		const target = numeric ? this.num(value) : "";
		return `
			<div class="abh-metric-card ${tone}">
				<div class="abh-icon">${this.icon(label_key, icon)}</div>
				<div>
					<div class="abh-metric-value" ${numeric ? `data-count-target="${target}"` : ""}>${
			numeric ? this.format_number(display) : frappe.utils.escape_html(display)
		}</div>
					<div class="abh-metric-label">${frappe.utils.escape_html(this.t(label_key))}</div>
				</div>
			</div>`;
	},

	animate_counters() {
		if (this.counterFrame) {
			cancelAnimationFrame(this.counterFrame);
			this.counterFrame = null;
		}

		const nodes = Array.from(
			document.querySelectorAll("#clf-dashboard-root [data-count-target]")
		);
		const duration = 850;
		const start = performance.now();

		const tick = (now) => {
			const progress = Math.min(1, (now - start) / duration);
			const eased = 1 - Math.pow(1 - progress, 3);

			nodes.forEach((node) => {
				const target = Number(node.getAttribute("data-count-target") || 0);
				node.textContent = this.format_number(Math.round(target * eased));
			});

			if (progress < 1) {
				this.counterFrame = requestAnimationFrame(tick);
			} else {
				this.counterFrame = null;
			}
		};

		this.counterFrame = requestAnimationFrame(tick);
	},

	icon(key, fallback) {
		const icons = {
			shg_approved:
				'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 11.5a4 4 0 1 1 8 0v1.2h1.2A2.8 2.8 0 0 1 20 15.5V19H4v-3.5a2.8 2.8 0 0 1 2.8-2.8H8v-1.2Z"/><path d="m9.4 11.2 1.7 1.7 3.7-4"/></svg>',
			vo_pending:
				'<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="8"/><path d="M12 7v5l3 2"/></svg>',
			vo_approved:
				'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 11.5 10 17 19 7"/><path d="M4 19h16"/></svg>',
			clf_pending:
				'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 5h12v5c0 4.5-2.4 7.4-6 9-3.6-1.6-6-4.5-6-9V5Z"/><path d="M12 8v4l2.5 1.5"/></svg>',
			clf_approved:
				'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 5h12v5c0 4.5-2.4 7.4-6 9-3.6-1.6-6-4.5-6-9V5Z"/><path d="m9 12 2 2 4-5"/></svg>',
			total_registered:
				'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M16 21v-2a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4v2"/><circle cx="9.5" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
			under_training:
				'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 3h12"/><path d="M6 21h12"/><path d="M8 3v4.5c0 1.4.8 2.7 2.1 3.3L12 12l1.9-1.2A3.7 3.7 0 0 0 16 7.5V3"/><path d="M8 21v-4.5c0-1.4.8-2.7 2.1-3.3L12 12l1.9 1.2a3.7 3.7 0 0 1 2.1 3.3V21"/></svg>',
			passed: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>',
			failed: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>',
			loan_applicants:
				'<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="8" r="3"/><path d="M6 21v-2a6 6 0 0 1 12 0v2"/></svg>',
			loan_disbursed:
				'<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="7" width="18" height="10" rx="2"/><circle cx="12" cy="12" r="2"/><path d="M7 12h.01M17 12h.01"/></svg>',
			amount_disbursed:
				'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5h8M8 9h8M9 5c5 0 5 8 0 8l6 6"/></svg>',
			median_days:
				'<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="8"/><path d="M12 7v5l4 2"/></svg>',
			home: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 11.5 12 5l8 6.5"/><path d="M6.5 10.5V19h11v-8.5"/><path d="M10 19v-5h4v5"/></svg>',
			nomination_stage:
				'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 19h16"/><path d="M7 19V9"/><path d="M12 19V5"/><path d="M17 19v-7"/></svg>',
			training_stage:
				'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m4 8 8-4 8 4-8 4-8-4Z"/><path d="M7 10.5V15c0 1.7 2.2 3 5 3s5-1.3 5-3v-4.5"/></svg>',
			loan_stage:
				'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5h8M8 9h8M9 5c5 0 5 8 0 8l6 6"/></svg>',
		};
		return icons[key] || frappe.utils.escape_html(fallback || "");
	},

	num(value) {
		const parsed = Number(value || 0);
		return Number.isFinite(parsed) ? parsed : 0;
	},

	format_number(value) {
		return this.num(value).toLocaleString("en-IN");
	},

	money(value) {
		return `₹${this.num(value).toLocaleString("en-IN")}`;
	},

	format_time(date) {
		return date.toLocaleString("en-IN", {
			day: "2-digit",
			month: "short",
			hour: "numeric",
			minute: "2-digit",
			hour12: true,
		});
	},
};

function add_clf_dashboard_style() {}

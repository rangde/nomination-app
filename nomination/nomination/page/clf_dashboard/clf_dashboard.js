frappe.pages["clf-dashboard"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "CLF Dashboard",
		single_column: true,
	});

	page.main.html(`
		<div id="abhilasha-dashboard">
			<div class="abh-shell">
				<header class="abh-header">
					<div>
						<div class="abh-kicker" data-i18n="kicker">CLF Overview</div>
						<h1 data-i18n="title">CLF Dashboard</h1>
						<p data-i18n="subtitle">Track nomination, training and loan progress from one view.</p>
					</div>
					<div class="abh-actions">
						<div class="abh-lang" role="group" aria-label="Language">
							<button data-lang="hi">HI</button>
							<button class="active" data-lang="en">EN</button>
						</div>
						<button class="abh-refresh" type="button" data-action="refresh">
							<span class="abh-refresh-icon">↻</span>
							<span data-i18n="refresh">Refresh</span>
						</button>
					</div>
				</header>

				<div id="abh-dashboard-view">
					<section class="abh-overview">
						<div>
							<div class="abh-section-label" data-i18n="overview_title">At a glance</div>
							<p data-i18n="overview_body">Follow each didi from nomination approval to training and loan readiness.</p>
						</div>
						<div class="abh-updated">
							<span data-i18n="last_updated">Last updated</span>
							<strong id="abh-last-updated">-</strong>
						</div>
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

					<section class="abh-section">
						<div class="abh-section-head">
							<span class="abh-dot green"></span>
							<h2 data-i18n="training_heading">Training & Assessment</h2>
						</div>
						<div id="abh-training" class="abh-metric-grid"></div>
					</section>

					<div class="abh-connector" id="abh-connector-loan"></div>

					<section class="abh-section">
						<div class="abh-section-head">
							<span class="abh-dot amber"></span>
							<h2 data-i18n="loan_heading">Loan Process</h2>
						</div>
						<div id="abh-loan" class="abh-metric-grid"></div>
					</section>
				</div>

				<div id="abh-list-view" style="display:none"></div>
				<div id="abh-detail-modal" style="display:none"></div>
			</div>
		</div>
	`);

	add_abhilasha_dashboard_style();
	abhilasha_dashboard.bind_events();
	abhilasha_dashboard.apply_route_state();
	abhilasha_dashboard.load();
	abhilasha_dashboard.interval = setInterval(() => abhilasha_dashboard.load(), 30000);

	$(wrapper).on("remove", () => {
		clearInterval(abhilasha_dashboard.interval);
		$(document).off("click.abhilasha-dashboard");
	});
};

frappe.pages["clf-dashboard"].on_page_show = function () {
	if ($("#abhilasha-dashboard").length) {
		abhilasha_dashboard.apply_route_state();
	}
};

const abhilasha_dashboard = {
	lang: "en",
	interval: null,
	data: null,
	view: "dashboard",
	stageKey: "shg_approved",
	page: 1,
	pageSize: 20,
	pageSizeOptions: [20, 100, 500, 2500],
	stageKeys: ["all", "shg_approved", "vo_pending", "vo_approved", "clf_pending", "clf_approved"],
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
			overview_title: "At a glance",
			overview_body:
				"Follow each didi from nomination approval to training and loan readiness.",
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
			training_connector: "{0} CLF-approved didis have entered training.",
			loan_connector: "{0} didis received loans worth {1}.",
			open_list: "Open list",
			unavailable: "Not available",
			back_dashboard: "Dashboard",
			all: "All",
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
			training_connector: "{0} CLF-स्वीकृत दीदी प्रशिक्षण में हैं।",
			loan_connector: "{0} दीदी को {1} का लोन मिला।",
			open_list: "सूची खोलें",
			unavailable: "उपलब्ध नहीं",
			back_dashboard: "डैशबोर्ड",
			all: "सभी",
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
		$("#abhilasha-dashboard").on("click", "[data-lang]", (event) => {
			this.lang = $(event.currentTarget).data("lang");
			$("#abhilasha-dashboard [data-lang]").removeClass("active");
			$(event.currentTarget).addClass("active");
			this.render_current_view();
		});

		$("#abhilasha-dashboard").on("click", "[data-action='refresh']", () => this.load(true));

		$("#abhilasha-dashboard").on("click", ".abh-flow-step", (event) => {
			event.preventDefault();
			this.open_list($(event.currentTarget).data("stage"));
		});

		$("#abhilasha-dashboard").on("click", "[data-action='back-dashboard']", () => {
			this.view = "dashboard";
			$("#abh-list-view").hide();
			$("#abh-dashboard-view").show();
			this.update_dashboard_route();
			this.render();
		});

		$("#abhilasha-dashboard").on("click", "[data-stage-tab]", (event) => {
			this.stageKey = $(event.currentTarget).data("stage-tab");
			this.page = 1;
			this.load_list();
		});

		$("#abhilasha-dashboard").on("click", "[data-dropdown-toggle]", (event) => {
			event.stopPropagation();
			const $wrap = $(event.currentTarget).closest(".abh-select-wrap");
			$("#abhilasha-dashboard .abh-select-wrap").not($wrap).removeClass("open");
			$wrap.toggleClass("open");
		});

		$("#abhilasha-dashboard").on("click", "[data-dropdown-option]", (event) => {
			event.stopPropagation();
			const type = $(event.currentTarget).data("dropdown-type");
			const value = String($(event.currentTarget).data("value") || "");

			if (type === "stage") {
				this.stageKey = this.normalize_stage(value) || "all";
			} else {
				this[type] = value;
			}

			$("#abhilasha-dashboard .abh-select-wrap").removeClass("open");
			this.page = 1;
			this.load_list();
		});

		$(document).on("click.abhilasha-dashboard", () => {
			$("#abhilasha-dashboard .abh-select-wrap").removeClass("open");
		});

		$("#abhilasha-dashboard").on("input", "[data-filter='search']", (event) => {
			this.search = event.currentTarget.value;
			this.page = 1;
			clearTimeout(this.searchTimer);
			this.searchTimer = setTimeout(() => this.load_list(), 250);
		});

		$("#abhilasha-dashboard").on("click", "[data-sort]", (event) => {
			this.sortBy = $(event.currentTarget).data("sort");
			this.page = 1;
			this.load_list();
		});

		$("#abhilasha-dashboard").on("click", "[data-page]", (event) => {
			this.page = Number($(event.currentTarget).data("page"));
			this.load_list();
		});

		$("#abhilasha-dashboard").on("click", "[data-page-size]", (event) => {
			this.pageSize = Number($(event.currentTarget).data("page-size"));
			this.page = 1;
			this.load_list();
		});

		$("#abhilasha-dashboard").on("click", ".abh-list-card", (event) => {
			const name = $(event.currentTarget).data("name");
			const row = this.listData.rows.find((item) => item.name === name);
			if (row) this.open_modal(row);
		});

		$("#abhilasha-dashboard").on(
			"click",
			"[data-action='close-modal'], .abh-modal-backdrop",
			() => {
				this.close_modal();
			}
		);

		$("#abhilasha-dashboard").on("click", ".abh-modal-card", (event) =>
			event.stopPropagation()
		);
	},

	open_list(stageKey) {
		this.view = "list";
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
		if (spin) $("#abhilasha-dashboard .abh-refresh-icon").addClass("spinning");

		frappe.call({
			method: "nomination.api.dashboard.get_dashboard_metrics",
			callback: (r) => {
				$("#abhilasha-dashboard .abh-refresh-icon").removeClass("spinning");
				if (!r.message) return;
				this.data = r.message;
				this.render();
			},
			error: () => {
				$("#abhilasha-dashboard .abh-refresh-icon").removeClass("spinning");
				frappe.msgprint(__("Unable to load dashboard metrics."));
			},
		});
	},

	render() {
		this.apply_labels();
		if (!this.data) return;

		$("#abh-last-updated").text(this.format_time(new Date()));
		this.render_nomination(this.data.nomination || {});
		this.render_training(this.data.training || {});
		this.render_loan(this.data.loan || {});
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
		$("#abhilasha-dashboard [data-i18n]").each((_, el) => {
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

		$("#abh-connector-training").text(
			this.t("training_connector").replace("{0}", this.format_number(entered || total))
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

		$("#abh-connector-loan").text(
			this.t("loan_connector")
				.replace("{0}", this.format_number(disbursed))
				.replace("{1}", amount)
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
					<button class="abh-back-btn" type="button" data-action="back-dashboard">← ${frappe.utils.escape_html(
						this.t("back_dashboard")
					)}</button>
					<div class="abh-list-total"><strong>${this.format_number(
						total
					)}</strong><span>${frappe.utils.escape_html(this.t("didis"))}</span></div>
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
					<div class="abh-page-size abh-page-size-top">
						${this.page_size_buttons()}
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
							? rows.map((row) => this.list_card(row)).join("")
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
		const options = [
			"all",
			"shg_approved",
			"vo_pending",
			"vo_approved",
			"clf_pending",
			"clf_approved",
		].map((key) => ({
			value: key,
			label: this.t(key),
		}));
		return this.custom_select("stage", this.t(this.stageKey), options, this.stageKey);
	},

	option_select(key, placeholder, options, selected) {
		const items = [
			{ value: "", label: placeholder },
			...options.map((option) => ({ value: option, label: option })),
		];
		const label = selected || placeholder;
		return this.custom_select(key, label, items, selected);
	},

	custom_select(type, label, options, selected) {
		return `
			<div class="abh-select-wrap">
				<button class="abh-select-btn" type="button" data-dropdown-toggle>
					<span>${frappe.utils.escape_html(label)}</span>
					<i aria-hidden="true"></i>
				</button>
				<div class="abh-select-menu" role="listbox">
					${options
						.map((option) => {
							const active = String(option.value) === String(selected || "");
							return `<button class="abh-select-option ${
								active ? "active" : ""
							}" type="button" role="option" aria-selected="${active}" data-dropdown-type="${frappe.utils.escape_html(
								type
							)}" data-dropdown-option data-value="${frappe.utils.escape_html(
								option.value
							)}">${frappe.utils.escape_html(option.label)}</button>`;
						})
						.join("")}
				</div>
			</div>`;
	},

	list_card(row) {
		const name = this.full_name(row);
		const updated = this.date_label(row.modified);
		const statusKey = this.row_status_key(row);
		return `
			<button class="abh-list-card" type="button" data-name="${frappe.utils.escape_html(row.name)}">
				<div class="abh-card-main">
					<div>
						<h3>${frappe.utils.escape_html(name)}</h3>
						<div class="abh-village">⌂ ${frappe.utils.escape_html(row.townvillage || "-")}</div>
					</div>
					${this.avatar(row)}
				</div>
				<div class="abh-card-kicker">${frappe.utils.escape_html(this.t("stage"))}</div>
				<div class="abh-card-stage"><span class="abh-mini-chart">▥</span>${frappe.utils.escape_html(
					this.t("nomination_tab")
				)}</div>
				<div class="abh-card-kicker">${frappe.utils.escape_html(this.t("status"))}</div>
				<div class="abh-status-pill"><span></span>${frappe.utils.escape_html(this.t(statusKey))}</div>
				<div class="abh-card-footer">
					<strong>◷ ${frappe.utils.escape_html(updated)}</strong>
					<span>${frappe.utils.escape_html(this.t("last_updated_card"))}</span>
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
		return `
			<div class="abh-modal-section ${active ? "active" : ""}">
				<div class="abh-modal-section-head">
					<div class="abh-card-stage"><span class="abh-mini-chart">▥</span>${frappe.utils.escape_html(
						this.t(titleKey)
					)}</div>
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
		return `
			<a class="abh-flow-step ${tone}" data-stage="${label_key}" href="${href}" title="${frappe.utils.escape_html(
			this.t("open_list")
		)}">
				<div class="abh-flow-count">${this.format_number(value)}</div>
				<div class="abh-flow-label">${frappe.utils.escape_html(this.t(label_key))}</div>
			</a>`;
	},

	metric_card(label_key, value, tone, icon) {
		return `
			<div class="abh-metric-card ${tone}">
				<div class="abh-icon">${frappe.utils.escape_html(icon)}</div>
				<div>
					<div class="abh-metric-value">${
						typeof value === "string"
							? frappe.utils.escape_html(value)
							: this.format_number(value)
					}</div>
					<div class="abh-metric-label">${frappe.utils.escape_html(this.t(label_key))}</div>
				</div>
			</div>`;
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

function add_abhilasha_dashboard_style() {
	frappe.dom.set_style(`
		#abhilasha-dashboard {
			min-height: calc(100vh - 120px);
			background: #f7f2e8;
			color: #1f2933;
			margin: -15px;
			padding: 24px;
		}

		#abhilasha-dashboard .abh-shell {
			max-width: 1180px;
			margin: 0 auto;
			display: flex;
			flex-direction: column;
			gap: 18px;
		}

		#abhilasha-dashboard .abh-header {
			display: flex;
			justify-content: space-between;
			gap: 18px;
			align-items: flex-start;
		}

		#abhilasha-dashboard .abh-kicker,
		#abhilasha-dashboard .abh-section-label {
			font-size: 12px;
			font-weight: 700;
			letter-spacing: 0.08em;
			text-transform: uppercase;
			color: #8b6f47;
		}

		#abhilasha-dashboard h1 {
			font-size: 34px;
			line-height: 1.1;
			font-weight: 750;
			margin: 4px 0 8px;
			color: #1d1b18;
			letter-spacing: 0;
		}

		#abhilasha-dashboard p {
			max-width: 620px;
			font-size: 14px;
			color: #6b6255;
			margin: 0;
		}

		#abhilasha-dashboard .abh-actions {
			display: flex;
			align-items: center;
			gap: 10px;
			flex-wrap: wrap;
			justify-content: flex-end;
		}

		#abhilasha-dashboard .abh-lang {
			display: flex;
			background: #ece7dc;
			padding: 4px;
			border-radius: 999px;
			border: 1px solid #e0d8c8;
		}

		#abhilasha-dashboard button {
			border: 0;
			font-size: 12px;
			font-weight: 700;
			cursor: pointer;
		}

		#abhilasha-dashboard .abh-lang button {
			min-width: 42px;
			padding: 7px 10px;
			border-radius: 999px;
			background: transparent;
			color: #6b6255;
		}

		#abhilasha-dashboard .abh-lang button.active {
			background: #ffffff;
			color: #1d1b18;
			box-shadow: 0 1px 3px rgba(47, 36, 22, 0.12);
		}

		#abhilasha-dashboard .abh-refresh {
			display: inline-flex;
			align-items: center;
			gap: 7px;
			background: #1d1b18;
			color: #ffffff;
			padding: 10px 14px;
			border-radius: 999px;
		}

		#abhilasha-dashboard .abh-refresh-icon.spinning {
			animation: abh-spin .6s linear;
		}

		#abhilasha-dashboard .abh-overview {
			display: flex;
			justify-content: space-between;
			gap: 18px;
			background: #fffdf8;
			border: 1px solid #e4dccb;
			border-radius: 8px;
			padding: 18px;
		}

		#abhilasha-dashboard .abh-updated {
			min-width: 180px;
			text-align: right;
			color: #7a7267;
			font-size: 12px;
		}

		#abhilasha-dashboard .abh-updated strong {
			display: block;
			color: #1d1b18;
			font-size: 14px;
			margin-top: 4px;
		}

		#abhilasha-dashboard .abh-section {
			background: #fffdf8;
			border: 1px solid #e4dccb;
			border-radius: 8px;
			padding: 18px;
		}

		#abhilasha-dashboard .abh-flow-section {
			background: #ffffff;
			border: 0;
			border-top: 4px solid #1666e8;
			border-radius: 18px;
			box-shadow: 0 14px 34px rgba(33, 28, 19, 0.10);
			padding: 28px 32px 34px;
			overflow: hidden;
		}

		#abhilasha-dashboard .abh-section-head {
			display: flex;
			align-items: center;
			gap: 10px;
			margin-bottom: 14px;
		}

		#abhilasha-dashboard .abh-flow-head {
			gap: 14px;
			margin-bottom: 36px;
		}

		#abhilasha-dashboard .abh-flow-head h2 {
			color: #064cb8;
			font-size: 21px;
			font-weight: 800;
		}

		#abhilasha-dashboard .abh-flow-icon {
			width: 48px;
			height: 48px;
			border-radius: 12px;
			background: #eaf4ff;
			display: inline-flex;
			align-items: flex-end;
			justify-content: center;
			gap: 4px;
			padding: 13px 12px;
			color: #0654c5;
			flex: 0 0 auto;
		}

		#abhilasha-dashboard .abh-flow-icon::before {
			content: "";
			width: 2px;
			height: 23px;
			background: #0654c5;
			border-radius: 2px;
		}

		#abhilasha-dashboard .abh-flow-icon span {
			width: 3px;
			background: #0654c5;
			border-radius: 2px 2px 0 0;
		}

		#abhilasha-dashboard .abh-flow-icon span:nth-child(1) { height: 9px; }
		#abhilasha-dashboard .abh-flow-icon span:nth-child(2) { height: 18px; }
		#abhilasha-dashboard .abh-flow-icon span:nth-child(3) { height: 6px; }

		#abhilasha-dashboard .abh-dot {
			width: 10px;
			height: 10px;
			border-radius: 50%;
			display: inline-block;
		}

		#abhilasha-dashboard .abh-dot.blue { background: #4f7fc8; }
		#abhilasha-dashboard .abh-dot.green { background: #4f8a5a; }
		#abhilasha-dashboard .abh-dot.amber { background: #c68853; }

		#abhilasha-dashboard h2 {
			font-size: 15px;
			font-weight: 750;
			margin: 0;
			color: #1d1b18;
			letter-spacing: 0;
		}

		#abhilasha-dashboard .abh-flow-track {
			position: relative;
			display: grid;
			grid-template-columns: repeat(5, minmax(120px, 1fr));
			align-items: start;
			gap: 20px;
			padding: 0 58px;
		}

		#abhilasha-dashboard .abh-flow-track::before {
			content: "";
			position: absolute;
			top: 22px;
			left: calc(10% + 58px);
			right: calc(10% + 58px);
			height: 1px;
			background: #ddd8cf;
		}

		#abhilasha-dashboard .abh-flow-step {
			position: relative;
			z-index: 1;
			display: flex;
			flex-direction: column;
			align-items: center;
			gap: 12px;
			text-align: center;
			text-decoration: none;
			color: inherit;
		}

		#abhilasha-dashboard .abh-flow-count {
			min-width: 52px;
			height: 40px;
			padding: 0 14px;
			border-radius: 999px;
			display: inline-flex;
			align-items: center;
			justify-content: center;
			font-size: 28px;
			font-weight: 850;
			line-height: 1;
			background: #eaf4ff;
			color: #0757c6;
		}

		#abhilasha-dashboard .abh-flow-step.gray .abh-flow-count {
			background: #eceef2;
			color: #6f7580;
		}

		#abhilasha-dashboard .abh-flow-step.green .abh-flow-count {
			background: #dff7e5;
			color: #12662a;
		}

		#abhilasha-dashboard .abh-flow-label {
			font-size: 14px;
			font-weight: 800;
			color: #222222;
			line-height: 1.25;
			min-height: 36px;
			display: flex;
			align-items: flex-start;
			justify-content: center;
		}

		#abhilasha-dashboard .abh-flow-step:hover .abh-flow-count {
			box-shadow: 0 8px 18px rgba(6, 84, 197, 0.18);
			transform: translateY(-1px);
		}

		#abhilasha-dashboard .abh-metric-grid {
			display: grid;
			grid-template-columns: repeat(4, minmax(160px, 1fr));
			gap: 12px;
		}

		#abhilasha-dashboard .abh-metric-card {
			background: #ffffff;
			border: 1px solid #e6dfd2;
			border-radius: 8px;
			text-decoration: none;
			color: inherit;
			transition: transform .15s ease, box-shadow .15s ease, border-color .15s ease;
		}

		#abhilasha-dashboard .abh-metric-card:hover {
			transform: translateY(-2px);
			box-shadow: 0 10px 24px rgba(47, 36, 22, 0.10);
		}

		#abhilasha-dashboard .abh-metric-label {
			font-size: 13px;
			font-weight: 650;
			color: #4b5563;
		}

		#abhilasha-dashboard .abh-connector {
			align-self: center;
			background: #1d1b18;
			color: #ffffff;
			font-size: 12px;
			font-weight: 700;
			border-radius: 999px;
			padding: 8px 14px;
			margin: -4px 0;
		}

		#abhilasha-dashboard .abh-metric-card {
			display: flex;
			align-items: center;
			gap: 14px;
			padding: 16px;
			min-height: 98px;
		}

		#abhilasha-dashboard .abh-icon {
			width: 42px;
			height: 42px;
			border-radius: 50%;
			display: grid;
			place-items: center;
			font-size: 12px;
			font-weight: 800;
			flex: 0 0 auto;
		}

		#abhilasha-dashboard .abh-metric-card.blue .abh-icon { background: #e7f0ff; color: #315f9d; }
		#abhilasha-dashboard .abh-metric-card.green .abh-icon { background: #e5f4e8; color: #356b42; }
		#abhilasha-dashboard .abh-metric-card.amber .abh-icon { background: #fff2df; color: #8a5725; }
		#abhilasha-dashboard .abh-metric-card.red .abh-icon { background: #fde8e8; color: #9b2c2c; }
		#abhilasha-dashboard .abh-metric-card.gray .abh-icon { background: #eceae3; color: #5d5851; }

		#abhilasha-dashboard .abh-metric-value {
			font-size: 24px;
			font-weight: 800;
			color: #1d1b18;
			line-height: 1.1;
		}

		#abhilasha-dashboard .abh-list-page {
			min-height: calc(100vh - 150px);
		}

		#abhilasha-dashboard .abh-list-top {
			display: flex;
			justify-content: space-between;
			align-items: flex-start;
			gap: 18px;
			margin-bottom: 26px;
		}

		#abhilasha-dashboard .abh-back-btn {
			background: #ece9e0;
			color: #1f1f1f;
			border-radius: 16px;
			padding: 16px 28px;
			font-size: 16px;
			font-weight: 800;
		}

		#abhilasha-dashboard .abh-list-total {
			min-width: 88px;
			min-height: 82px;
			border-radius: 18px;
			background: #eef3fb;
			display: flex;
			flex-direction: column;
			align-items: center;
			justify-content: center;
			color: #1d1d1d;
		}

		#abhilasha-dashboard .abh-list-total strong {
			font-size: 32px;
			line-height: 1;
			font-weight: 850;
		}

		#abhilasha-dashboard .abh-list-total span {
			font-size: 13px;
			color: #5f6773;
			font-weight: 700;
		}

		#abhilasha-dashboard .abh-list-title {
			font-size: 31px;
			margin: 0 0 60px;
			color: #1c1c1c;
		}

		#abhilasha-dashboard .abh-tabs-row {
			display: flex;
			align-items: center;
			justify-content: space-between;
			gap: 14px;
			flex-wrap: wrap;
			margin-bottom: 18px;
		}

		#abhilasha-dashboard .abh-tabs {
			display: flex;
			gap: 10px;
			flex-wrap: wrap;
			min-width: 0;
		}

		#abhilasha-dashboard .abh-tab {
			border-radius: 24px;
			padding: 16px 24px;
			background: #ece9e0;
			color: #404954;
			font-size: 14px;
			font-weight: 850;
		}

		#abhilasha-dashboard .abh-tab.active {
			background: #1d1d1d;
			color: #ffffff;
		}

		#abhilasha-dashboard .abh-tab:disabled {
			opacity: 0.85;
			cursor: not-allowed;
		}

		#abhilasha-dashboard .abh-list-rule {
			height: 1px;
			background: #ddd7cb;
			margin: 0 0 18px;
		}

		#abhilasha-dashboard .abh-filter-row {
			display: grid;
			grid-template-columns: repeat(4, minmax(190px, 1fr));
			align-items: center;
			gap: 12px;
			margin-bottom: 16px;
		}

		#abhilasha-dashboard .abh-list-tools {
			display: flex;
			align-items: center;
			gap: 12px;
			flex-wrap: wrap;
			margin-bottom: 18px;
			justify-content: flex-end;
			margin-bottom: 26px;
		}

		#abhilasha-dashboard .abh-select-wrap {
			position: relative;
			min-width: 0;
			z-index: 3;
		}

		#abhilasha-dashboard .abh-select-btn {
			width: 100%;
			height: 58px;
			border-radius: 10px;
			border: 1px solid #d5d8dd;
			background: #ffffff;
			padding: 0 44px 0 18px;
			font-size: 15px;
			font-weight: 800;
			color: #222222;
			box-shadow: 0 1px 2px rgba(31, 31, 31, 0.03);
			outline: 0;
			transition: border-color .15s ease, box-shadow .15s ease;
			display: flex;
			align-items: center;
			justify-content: space-between;
			gap: 12px;
			text-align: left;
		}

		#abhilasha-dashboard .abh-select-btn span {
			min-width: 0;
			overflow: hidden;
			text-overflow: ellipsis;
			white-space: nowrap;
		}

		#abhilasha-dashboard .abh-select-btn i {
			width: 9px;
			height: 9px;
			border-right: 2px solid #28323f;
			border-bottom: 2px solid #28323f;
			transform: translateY(-2px) rotate(45deg);
			flex: 0 0 auto;
			transition: transform .15s ease;
		}

		#abhilasha-dashboard .abh-select-btn:hover,
		#abhilasha-dashboard .abh-search:hover {
			border-color: #b9c0ca;
		}

		#abhilasha-dashboard .abh-select-wrap.open .abh-select-btn,
		#abhilasha-dashboard .abh-select-btn:focus,
		#abhilasha-dashboard .abh-search:focus-within {
			border-color: #4f7fc8;
			box-shadow: 0 0 0 3px rgba(79, 127, 200, 0.14);
		}

		#abhilasha-dashboard .abh-select-wrap.open {
			z-index: 20;
		}

		#abhilasha-dashboard .abh-select-wrap.open .abh-select-btn i {
			transform: translateY(2px) rotate(225deg);
		}

		#abhilasha-dashboard .abh-select-menu {
			position: absolute;
			top: calc(100% + 8px);
			left: 0;
			right: 0;
			display: none;
			max-height: 260px;
			overflow: auto;
			background: #ffffff;
			border: 1px solid #d8dce2;
			border-radius: 10px;
			padding: 6px;
			box-shadow: 0 14px 34px rgba(31, 31, 31, 0.16);
		}

		#abhilasha-dashboard .abh-select-wrap.open .abh-select-menu {
			display: grid;
			gap: 2px;
		}

		#abhilasha-dashboard .abh-select-option {
			width: 100%;
			min-height: 38px;
			border-radius: 8px;
			background: transparent;
			color: #1f2933;
			padding: 9px 12px;
			font-size: 14px;
			font-weight: 700;
			text-align: left;
			overflow-wrap: anywhere;
		}

		#abhilasha-dashboard .abh-select-option:hover,
		#abhilasha-dashboard .abh-select-option.active {
			background: #eaf4ff;
			color: #064cb8;
		}

		#abhilasha-dashboard .abh-select-option.active {
			font-weight: 850;
		}

		#abhilasha-dashboard .abh-search {
			width: 100%;
			min-width: 0;
			height: 58px;
			border: 1px solid #d5d8dd;
			border-radius: 10px;
			background: #ffffff;
			display: flex;
			align-items: center;
			gap: 10px;
			padding: 0 16px;
			box-shadow: 0 1px 2px rgba(31, 31, 31, 0.03);
			transition: border-color .15s ease, box-shadow .15s ease;
		}

		#abhilasha-dashboard .abh-search span {
			color: #6b7280;
			font-size: 20px;
		}

		#abhilasha-dashboard .abh-search input {
			border: 0;
			outline: 0;
			width: 100%;
			font-size: 15px;
			font-weight: 700;
			background: transparent;
		}

		#abhilasha-dashboard .abh-sort {
			display: inline-flex;
			border-radius: 12px;
			background: #ece9e0;
			padding: 4px;
		}

		#abhilasha-dashboard .abh-sort button {
			padding: 14px 16px;
			border-radius: 9px;
			background: #fffdf8;
			color: #1d1d1d;
			font-size: 14px;
			font-weight: 850;
		}

		#abhilasha-dashboard .abh-sort button.active {
			background: #1d1d1d;
			color: #ffffff;
		}

		#abhilasha-dashboard .abh-card-grid {
			display: grid;
			grid-template-columns: repeat(4, minmax(260px, 1fr));
			gap: 24px;
		}

		#abhilasha-dashboard .abh-list-card {
			border: 1px solid #e2e4e8;
			border-radius: 24px;
			background: #ffffff;
			padding: 24px 24px 0;
			min-height: 200px;
			text-align: left;
			box-shadow: 0 12px 28px rgba(31, 31, 31, 0.06);
			overflow: hidden;
			display: flex;
			flex-direction: column;
			color: #222222;
		}

		#abhilasha-dashboard .abh-list-card:hover {
			transform: translateY(-3px);
			box-shadow: 0 18px 36px rgba(31, 31, 31, 0.10);
		}

		#abhilasha-dashboard .abh-card-main {
			display: flex;
			justify-content: space-between;
			gap: 14px;
			min-height: 96px;
		}

		#abhilasha-dashboard .abh-card-main > div:first-child {
			min-width: 0;
			flex: 1 1 auto;
		}

		#abhilasha-dashboard .abh-list-card h3 {
			font-size: 18px;
			line-height: 1.15;
			margin: 0 0 14px;
			font-weight: 850;
			color: #111111;
			overflow-wrap: anywhere;
		}

		#abhilasha-dashboard .abh-village {
			font-size: 16px;
			font-weight: 800;
			color: #6c665c;
			overflow-wrap: anywhere;
		}

		#abhilasha-dashboard .abh-avatar {
			width: 72px;
			height: 72px;
			border-radius: 18px;
			object-fit: cover;
			background: #f1eee8;
			flex: 0 0 auto;
		}

		#abhilasha-dashboard .abh-avatar-fallback {
			display: grid;
			place-items: center;
			font-size: 25px;
			font-weight: 850;
			color: #064cb8;
			background: #eaf4ff;
		}

		#abhilasha-dashboard .abh-card-kicker {
			font-size: 12px;
			font-weight: 850;
			letter-spacing: 0.06em;
			text-transform: uppercase;
			color: #9d978d;
			margin-top: 16px;
		}

		#abhilasha-dashboard .abh-card-stage {
			display: flex;
			align-items: center;
			gap: 10px;
			font-size: 19px;
			font-weight: 850;
			color: #202020;
			margin-top: 8px;
			min-width: 0;
		}

		#abhilasha-dashboard .abh-mini-chart {
			color: #4f7fc8;
			font-size: 18px;
			flex: 0 0 auto;
		}

		#abhilasha-dashboard .abh-status-pill {
			align-self: flex-start;
			display: inline-flex;
			align-items: center;
			gap: 9px;
			border-radius: 999px;
			background: #e3f2ff;
			color: #0654c5;
			padding: 8px 12px;
			font-size: 16px;
			font-weight: 850;
			margin-top: 10px;
			margin-bottom: 18px;
			max-width: 100%;
			overflow-wrap: anywhere;
		}

		#abhilasha-dashboard .abh-status-pill span {
			width: 10px;
			height: 10px;
			border-radius: 50%;
			background: #0757c6;
		}

		#abhilasha-dashboard .abh-status-pill.muted {
			background: #f5f5f5;
			color: #a5a5a5;
			font-size: 14px;
			margin: 0;
		}

		#abhilasha-dashboard .abh-card-footer {
			background: #eaf4ff;
			margin: auto -24px 0;
			padding: 20px 24px 22px;
			display: flex;
			flex-direction: column;
			gap: 10px;
		}

		#abhilasha-dashboard .abh-card-footer strong {
			font-size: 19px;
			line-height: 1.25;
			color: #202020;
		}

		#abhilasha-dashboard .abh-card-footer span {
			font-size: 12px;
			font-weight: 850;
			letter-spacing: 0.06em;
			text-transform: uppercase;
			color: #8490a2;
		}

		#abhilasha-dashboard .abh-empty,
		#abhilasha-dashboard .abh-list-loading {
			grid-column: 1 / -1;
			background: #ffffff;
			border: 1px solid #e2e4e8;
			border-radius: 16px;
			padding: 32px;
			font-weight: 800;
			color: #6b6255;
		}

		#abhilasha-dashboard .abh-list-loading-wrap {
			min-height: calc(100vh - 170px);
			display: grid;
			place-items: center;
		}

		#abhilasha-dashboard .abh-pager {
			display: flex;
			justify-content: center;
			align-items: center;
			gap: 12px;
			flex-wrap: wrap;
			margin: 28px 0 8px;
			font-weight: 800;
		}

		#abhilasha-dashboard .abh-pager button {
			background: #1d1d1d;
			color: #ffffff;
			border-radius: 10px;
			padding: 12px 18px;
		}

		#abhilasha-dashboard .abh-pager button:disabled {
			opacity: 0.35;
			cursor: not-allowed;
		}

		#abhilasha-dashboard .abh-page-size {
			display: inline-flex;
			align-items: center;
			gap: 4px;
			border-radius: 10px;
			background: #ece9e0;
			padding: 4px;
		}

		#abhilasha-dashboard .abh-page-size button {
			background: transparent;
			color: #4b5563;
			border-radius: 8px;
			padding: 10px 13px;
		}

		#abhilasha-dashboard .abh-page-size button.active {
			background: #1d1d1d;
			color: #ffffff;
		}

		#abhilasha-dashboard .abh-page-size-top {
			flex: 0 0 auto;
			margin-left: auto;
		}

		#abh-detail-modal {
			position: fixed;
			inset: 0;
			z-index: 1050;
		}

		#abhilasha-dashboard .abh-modal-backdrop {
			position: fixed;
			inset: 0;
			background: rgba(0, 0, 0, 0.52);
			display: flex;
			justify-content: center;
			align-items: flex-start;
			padding: 38px 18px;
			overflow: auto;
		}

		#abhilasha-dashboard .abh-modal-card {
			position: relative;
			width: min(660px, 100%);
			background: #ffffff;
			border-radius: 26px;
			padding: 34px 24px 24px;
			box-shadow: 0 24px 70px rgba(0, 0, 0, 0.25);
		}

		#abhilasha-dashboard .abh-modal-close {
			position: absolute;
			top: 18px;
			right: 18px;
			width: 50px;
			height: 50px;
			border-radius: 50%;
			background: #ffffff;
			box-shadow: 0 4px 14px rgba(0, 0, 0, 0.12);
			font-size: 24px;
			color: #394150;
		}

		#abhilasha-dashboard .abh-modal-person {
			display: flex;
			align-items: center;
			gap: 22px;
			margin: 0 70px 30px 12px;
		}

		#abhilasha-dashboard .abh-modal-person h2 {
			font-size: 30px;
			margin: 0 0 8px;
		}

		#abhilasha-dashboard .abh-modal-person p {
			font-size: 16px;
			font-weight: 800;
			color: #6c665c;
		}

		#abhilasha-dashboard .abh-modal-section {
			border-radius: 18px;
			border: 1px solid #eef0f3;
			padding: 26px;
			margin-top: 14px;
			background: #fffdf9;
		}

		#abhilasha-dashboard .abh-modal-section.active {
			border-color: #8db6ff;
		}

		#abhilasha-dashboard .abh-modal-section-head {
			display: flex;
			align-items: center;
			justify-content: space-between;
			gap: 12px;
			padding-bottom: 16px;
			border-bottom: 1px solid #ece7df;
			margin-bottom: 2px;
		}

		#abhilasha-dashboard .abh-kv {
			display: flex;
			justify-content: space-between;
			gap: 16px;
			padding: 17px 0;
			border-bottom: 1px solid #ece7df;
			font-size: 16px;
		}

		#abhilasha-dashboard .abh-kv span {
			color: #8a8277;
			font-weight: 800;
		}

		#abhilasha-dashboard .abh-kv strong {
			color: #111111;
			font-size: 18px;
			text-align: right;
		}

		#abhilasha-dashboard .abh-muted-note {
			margin-top: 18px;
			color: #beb8af;
			font-weight: 700;
		}

		@keyframes abh-spin {
			to { transform: rotate(360deg); }
		}

		@media (max-width: 900px) {
			#abhilasha-dashboard {
				padding: 16px;
			}

			#abhilasha-dashboard .abh-header,
			#abhilasha-dashboard .abh-overview {
				flex-direction: column;
			}

			#abhilasha-dashboard .abh-actions {
				justify-content: flex-start;
			}

			#abhilasha-dashboard .abh-updated {
				text-align: left;
			}

			#abhilasha-dashboard .abh-metric-grid {
				grid-template-columns: repeat(2, minmax(0, 1fr));
			}

			#abhilasha-dashboard .abh-flow-track {
				padding: 0;
				grid-template-columns: repeat(2, minmax(0, 1fr));
			}

			#abhilasha-dashboard .abh-flow-track::before {
				display: none;
			}

			#abhilasha-dashboard .abh-card-grid {
				grid-template-columns: repeat(2, minmax(0, 1fr));
				gap: 18px;
			}

			#abhilasha-dashboard .abh-filter-row {
				grid-template-columns: repeat(2, minmax(0, 1fr));
			}

			#abhilasha-dashboard .abh-tabs-row,
			#abhilasha-dashboard .abh-list-tools {
				align-items: flex-start;
			}

			#abhilasha-dashboard .abh-page-size-top {
				margin-left: 0;
			}
		}

		@media (max-width: 520px) {
			#abhilasha-dashboard h1 {
				font-size: 26px;
			}

			#abhilasha-dashboard .abh-metric-grid {
				grid-template-columns: 1fr;
			}

			#abhilasha-dashboard .abh-flow-section {
				padding: 22px 18px 24px;
				border-radius: 14px;
			}

			#abhilasha-dashboard .abh-flow-track {
				grid-template-columns: 1fr;
				gap: 16px;
			}

			#abhilasha-dashboard .abh-card-grid {
				grid-template-columns: 1fr;
			}

			#abhilasha-dashboard .abh-filter-row {
				grid-template-columns: 1fr;
			}

			#abhilasha-dashboard .abh-list-card {
				min-height: 420px;
				padding: 24px 24px 0;
			}

			#abhilasha-dashboard .abh-card-footer {
				margin-left: -24px;
				margin-right: -24px;
			}

			#abhilasha-dashboard .abh-sort,
			#abhilasha-dashboard .abh-page-size,
			#abhilasha-dashboard .abh-search {
				width: 100%;
			}

			#abhilasha-dashboard .abh-page-size {
				justify-content: space-between;
			}
		}
	`);
}

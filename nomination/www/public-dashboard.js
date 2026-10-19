frappe.ready(() => {
	const root = document.getElementById("public-dashboard");
	if (!root) return;

	const refresh = root.querySelector("#dashboard-refresh");
	const status = root.querySelector("#dashboard-status");
	const metrics = root.querySelector("#dashboard-metrics");
	const formatter = new Intl.NumberFormat(document.documentElement.lang || "en-IN", {
		maximumFractionDigits: 2,
	});
	let loading = false;
	let hasData = false;

	async function loadMetrics() {
		if (loading) return;
		loading = true;
		refresh.disabled = true;
		metrics.setAttribute("aria-busy", "true");
		status.classList.remove("has-error");
		status.textContent = __("Loading metrics…");
		const controller = new AbortController();
		const timeout = setTimeout(() => controller.abort(), 45000);

		try {
			const response = await fetch(
				"/api/method/nomination.api.public_dashboard.get_public_dashboard_metrics",
				{ signal: controller.signal, headers: { Accept: "application/json" } }
			);
			if (!response.ok) throw new Error("Metrics request failed");
			const { message: data } = await response.json();
			if (!data?.nomination || !data?.training || !data?.loan) {
				throw new Error("Invalid metrics response");
			}
			root.querySelectorAll("[data-metric]").forEach((card) => {
				const value = data[card.dataset.section][card.dataset.metric];
				const available = typeof value === "number" && Number.isFinite(value);
				card.textContent = available ? formatter.format(value) : "—";
				card.setAttribute(
					"aria-label",
					available ? card.textContent : __("Not available")
				);
			});
			hasData = true;
			// The server timestamp uses the site's timezone, so keep it as supplied.
			status.textContent = data.updated_at
				? __("Last updated: {0} (site time)", [
						data.updated_at.replace("T", " ").split(".")[0],
				  ])
				: __("Metrics loaded.");
		} catch {
			status.classList.add("has-error");
			status.textContent = hasData
				? __("Unable to refresh. Showing previously loaded metrics; please try again.")
				: __("Unable to load metrics. Please try again.");
		} finally {
			clearTimeout(timeout);
			loading = false;
			refresh.disabled = false;
			metrics.setAttribute("aria-busy", "false");
		}
	}

	refresh.addEventListener("click", loadMetrics);
	loadMetrics();
	setInterval(() => {
		if (!document.hidden) loadMetrics();
	}, 60000);
});

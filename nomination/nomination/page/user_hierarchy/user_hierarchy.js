frappe.pages["user-hierarchy"].on_page_load = function (wrapper) {
	let page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "User Hierarchy",
		single_column: true,
	});

	page.main.html(`<div id="hierarchy-root"></div>`);
	add_hierarchy_style();
	load_hierarchy();
};

function load_hierarchy() {
	frappe.call({
		method: "nomination.api.user.get_user_hierarchy",
		callback: function (r) {
			if (!r.message || !r.message.length) {
				$("#hierarchy-root").html(
					`<p style="color:var(--text-muted);padding:2rem">No hierarchy data found.</p>`
				);
				return;
			}
			const html = r.message.map((node) => render_node(node)).join("");
			$("#hierarchy-root").html(`<div class="h-tree">${html}</div>`);
		},
		error: function () {
			frappe.msgprint(__("Unable to load hierarchy."));
		},
	});
}

function render_node(node) {
	const children =
		node.children && node.children.length
			? `<ul>${node.children.map((c) => `<li>${render_node(c)}</li>`).join("")}</ul>`
			: "";

	return `
		<div class="h-node">
			<div class="h-card">
				<div class="h-name">${frappe.utils.escape_html(node.full_name)}</div>
				<div class="h-email">${frappe.utils.escape_html(node.user)}</div>
			</div>
			${children}
		</div>`;
}

function add_hierarchy_style() {
	frappe.dom.set_style(`
		#hierarchy-root {
			padding: 2rem 1rem;
			overflow-x: auto;
		}

		.h-tree {
			display: flex;
			flex-direction: column;
			gap: 0.5rem;
		}

		/* Indented tree lines */
		.h-node ul {
			list-style: none;
			margin: 0.5rem 0 0 1.5rem;
			padding: 0;
			border-left: 2px solid var(--border-color);
			display: flex;
			flex-direction: column;
			gap: 0.5rem;
		}

		.h-node ul > li {
			position: relative;
			padding-left: 1.25rem;
		}

		.h-node ul > li::before {
			content: "";
			position: absolute;
			left: 0;
			top: 1.1rem;
			width: 1.1rem;
			height: 2px;
			background: var(--border-color);
		}

		.h-card {
			display: inline-flex;
			flex-direction: column;
			gap: 2px;
			background: var(--card-bg);
			border: 0.5px solid var(--border-color);
			border-left: 3px solid #378ADD;
			border-radius: 6px;
			padding: 0.5rem 1rem;
			min-width: 200px;
		}

		.h-name {
			font-size: 13px;
			font-weight: 500;
			color: var(--text-color);
		}

		.h-email {
			font-size: 11px;
			color: var(--text-muted);
		}
	`);
}

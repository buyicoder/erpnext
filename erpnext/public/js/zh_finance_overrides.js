import {
	format_month_year_text,
	localize_audit_doctype_text,
	localize_assignment_actions_label,
	localize_compact_cny_element,
	localize_datatable_filter_title,
	localize_login_activity_text,
	localize_list_filter_title,
	localize_list_sort_title,
	localize_list_value_title,
	localize_open_link_title,
	localize_photoswipe_title,
	localize_quill_accessibility_value,
	localize_sidebar_editor_text,
	localize_awesomplete_status_text,
	localize_timeline_element,
	localize_tree_level_label,
	localize_version_value_text,
} from "./zh_finance_format.mjs";

if (frappe.boot.lang === "zh") {
	Object.assign((frappe.utils.zh_finance ||= {}), {
		localize_audit_doctype_text,
		localize_login_activity_text,
	});

	Object.assign(frappe._messages, {
		"Add Sidebar Item": "添加侧栏项目",
		"Begin typing for results.": "输入关键词搜索。",
		"Book Advance Payments In Separate Party Account": "启用预收/付款科目",
		Masters: "基础资料",
		Reports: "报表",
	});

	const cny_amount_selector = [
		".number",
		".list-row-container .filterable div",
		"[data-fieldtype='Currency'] .static-area div",
		".datatable .dt-cell__content > div",
		".datatable .dt-cell__content div[style*='text-align: right']",
		".control-value",
		".summary-value",
	].join(", ");
	const awesomplete_status_selector = ".awesomplete [role='status']";
	const chart_date_selector = ".chart-container svg .x.axis text";
	const timeline_selector = ".timeline-content";
	const version_value_selector = '.timeline-content a[href^="/desk/version/"] b';
	const administrator_link_selector = 'a[href="/desk/user/Administrator"]';
	const datatable_filter_selector = ".datatable input.dt-filter[title^='Filter based on ']";
	const tree_level_selector = "#tree-level[aria-label='Tree Level']";
	const assignment_actions_selector =
		".dialog-assignment-row .btn-group[role='group'][aria-label='Actions']";
	const photoswipe_control_selector = ".pswp .pswp__button[title]";
	const open_link_selector = 'a[target="_blank"][title="Open Link"]';
	const list_sort_selector = ".list-row-head [data-sort-by][title]";
	const list_filter_selector = ".filter-button[title$='Filter Applied'], .filter-button[title$='Filters Applied']";
	const list_value_title_selector = ".list-row .ellipsis[title]";
	const sidebar_editor_selector = [
		'.body-sidebar [data-name="add-sidebar-item"] .sidebar-item-label',
		".body-sidebar .bottom-edit-controls .discard-button",
		".body-sidebar .bottom-edit-controls .save-sidebar",
	].join(", ");
	const quill_accessibility_selector =
		".ql-container [aria-label], .ql-tooltip-editor input[data-video]";
	const localize_compact_cny = (root = document) => {
		if (!root) return;
		const elements = root.matches?.(cny_amount_selector)
			? [root]
			: root.querySelectorAll?.(cny_amount_selector) || [];
		elements.forEach((element) => {
			const result = localize_compact_cny_element(element, Node.TEXT_NODE);
			if (!result) return;
			const cell = element.closest?.(".dt-cell__content");
			if (cell?.title === result.original) cell.title = result.localized;
		});
	};
	const localize_chart_dates = (root = document) => {
		if (!root) return;
		const elements = root.matches?.(chart_date_selector)
			? [root]
			: root.querySelectorAll?.(chart_date_selector) || [];
		elements.forEach((element) => {
			const localized = format_month_year_text(element.textContent);
			if (localized !== element.textContent) element.textContent = localized;
		});
	};
	const localize_awesomplete_status = (root = document) => {
		if (!root) return;
		const elements = root.matches?.(awesomplete_status_selector)
			? [root]
			: root.querySelectorAll?.(awesomplete_status_selector) || [];
		elements.forEach((element) => {
			const localized = localize_awesomplete_status_text(element.textContent);
			if (localized !== element.textContent) element.textContent = localized;
		});
	};
	const localize_timeline = (root = document) => {
		if (!root) return;
		const elements = root.matches?.(timeline_selector)
			? [root]
			: root.querySelectorAll?.(timeline_selector) || [];
		elements.forEach((element) => {
			localize_timeline_element(element, __, Node.TEXT_NODE);
		});

		const administrator_links = root.matches?.(administrator_link_selector)
			? [root]
			: root.querySelectorAll?.(administrator_link_selector) || [];
		administrator_links.forEach((link) => {
			if (link.textContent.trim() === "Administrator") link.textContent = __("Administrator");
		});

		const version_values = root.matches?.(version_value_selector)
			? [root]
			: root.querySelectorAll?.(version_value_selector) || [];
		version_values.forEach((value) => {
			const localized = localize_version_value_text(value.textContent, __);
			if (localized !== value.textContent) value.textContent = localized;
		});
	};
	const localize_datatable_controls = (root = document) => {
		if (!root) return;
		const filters = root.matches?.(datatable_filter_selector)
			? [root]
			: root.querySelectorAll?.(datatable_filter_selector) || [];
		filters.forEach((input) => {
			input.title = localize_datatable_filter_title(input.title, __);
		});

		const tree_levels = root.matches?.(tree_level_selector)
			? [root]
			: root.querySelectorAll?.(tree_level_selector) || [];
		tree_levels.forEach((input) => {
			input.setAttribute(
				"aria-label",
				localize_tree_level_label(input.getAttribute("aria-label"), __),
			);
		});
	};
	const localize_assignment_actions = (root = document) => {
		if (!root) return;
		const elements = root.matches?.(assignment_actions_selector)
			? [root]
			: root.querySelectorAll?.(assignment_actions_selector) || [];
		elements.forEach((element) => {
			const original = element.getAttribute("aria-label");
			const localized = localize_assignment_actions_label(original, __);
			if (localized !== original) element.setAttribute("aria-label", localized);
		});
	};
	const localize_photoswipe_controls = (root = document) => {
		if (!root) return;
		const elements = root.matches?.(photoswipe_control_selector)
			? [root]
			: root.querySelectorAll?.(photoswipe_control_selector) || [];
		elements.forEach((element) => {
			const original = element.title;
			const localized = localize_photoswipe_title(original);
			if (localized !== original) element.title = localized;
		});
	};
	const localize_open_links = (root = document) => {
		if (!root) return;
		const elements = root.matches?.(open_link_selector)
			? [root]
			: root.querySelectorAll?.(open_link_selector) || [];
		elements.forEach((element) => {
			const localized = localize_open_link_title(element.title, __);
			if (localized !== element.title) element.title = localized;
		});
	};
	const localize_list_titles = (root = document) => {
		if (!root) return;
		const filter_controls = root.matches?.(list_filter_selector)
			? [root]
			: root.querySelectorAll?.(list_filter_selector) || [];
		filter_controls.forEach((element) => {
			element.title = localize_list_filter_title(element.title, __);
		});

		const sort_controls = root.matches?.(list_sort_selector)
			? [root]
			: root.querySelectorAll?.(list_sort_selector) || [];
		sort_controls.forEach((element) => {
			element.title = localize_list_sort_title(element.title, element.textContent, __);
		});

		const value_titles = root.matches?.(list_value_title_selector)
			? [root]
			: root.querySelectorAll?.(list_value_title_selector) || [];
		value_titles.forEach((element) => {
			element.title = localize_list_value_title(element.title, element.textContent, __);
		});
	};
	const localize_sidebar_editor = (root = document) => {
		if (!root) return;
		const in_sidebar =
			root === document ||
			root.matches?.(".body-sidebar") ||
			root.closest?.(".body-sidebar") ||
			root.querySelector?.(".body-sidebar");
		if (!in_sidebar) return;
		const elements = root.matches?.(sidebar_editor_selector)
			? [root]
			: root.querySelectorAll?.(sidebar_editor_selector) || [];
		elements.forEach((element) => {
			const localized = localize_sidebar_editor_text(element.textContent, __);
			if (localized !== element.textContent) element.textContent = localized;
		});
	};
	const localize_quill_accessibility = (root = document) => {
		if (!root) return;
		const elements = root.matches?.(quill_accessibility_selector)
			? [root]
			: root.querySelectorAll?.(quill_accessibility_selector) || [];
		elements.forEach((element) => {
			for (const attribute of ["aria-label", "data-video"]) {
				const original = element.getAttribute(attribute);
				if (!original) continue;
				const localized = localize_quill_accessibility_value(attribute, original);
				if (localized !== original) element.setAttribute(attribute, localized);
			}
		});
	};

	localize_compact_cny();
	localize_awesomplete_status();
	localize_chart_dates();
	localize_timeline();
	localize_datatable_controls();
	localize_assignment_actions();
	localize_photoswipe_controls();
	localize_open_links();
	localize_list_titles();
	localize_sidebar_editor();
	localize_quill_accessibility();
	new MutationObserver((mutations) => {
		mutations.forEach((mutation) => {
			if (mutation.type === "attributes") {
				localize_datatable_controls(mutation.target);
				localize_assignment_actions(mutation.target);
				localize_photoswipe_controls(mutation.target);
				localize_open_links(mutation.target);
				localize_list_titles(mutation.target);
				localize_quill_accessibility(mutation.target);
				return;
			}
			if (mutation.type === "characterData") {
				localize_compact_cny(mutation.target.parentElement);
				localize_awesomplete_status(mutation.target.parentElement);
				localize_chart_dates(mutation.target.parentElement);
				localize_timeline(mutation.target.parentElement);
				localize_datatable_controls(mutation.target.parentElement);
				localize_list_titles(mutation.target.parentElement);
				localize_sidebar_editor(mutation.target.parentElement);
				localize_quill_accessibility(mutation.target.parentElement);
				return;
			}
			mutation.addedNodes.forEach((node) => {
				if (node.nodeType === Node.TEXT_NODE) {
					localize_compact_cny(node.parentElement);
					localize_awesomplete_status(node.parentElement);
					localize_chart_dates(node.parentElement);
					localize_timeline(node.parentElement);
					localize_datatable_controls(node.parentElement);
					localize_list_titles(node.parentElement);
					localize_sidebar_editor(node.parentElement);
					localize_quill_accessibility(node.parentElement);
					return;
				}
				if (node.nodeType !== Node.ELEMENT_NODE) return;
				localize_compact_cny(node);
				localize_awesomplete_status(node);
				localize_chart_dates(node);
				localize_timeline(node);
				localize_datatable_controls(node);
				localize_assignment_actions(node);
				localize_photoswipe_controls(node);
				localize_open_links(node);
				localize_list_titles(node);
				localize_sidebar_editor(node);
				localize_quill_accessibility(node);
			});
		});
	}).observe(document.body, {
		attributeFilter: ["aria-label", "title"],
		attributes: true,
		characterData: true,
		childList: true,
		subtree: true,
	});
}

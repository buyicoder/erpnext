import {
	format_month_year_text,
	localize_audit_doctype_text,
	localize_compact_cny_element,
	localize_datatable_filter_title,
	localize_login_activity_text,
	localize_list_sort_title,
	localize_list_value_title,
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
	const list_sort_selector = ".list-row-head [data-sort-by][title]";
	const list_value_title_selector = ".list-row .ellipsis[title]";
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
	const localize_list_titles = (root = document) => {
		if (!root) return;
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

	localize_compact_cny();
	localize_awesomplete_status();
	localize_chart_dates();
	localize_timeline();
	localize_datatable_controls();
	localize_list_titles();
	new MutationObserver((mutations) => {
		mutations.forEach((mutation) => {
			if (mutation.type === "characterData") {
				localize_compact_cny(mutation.target.parentElement);
				localize_awesomplete_status(mutation.target.parentElement);
				localize_chart_dates(mutation.target.parentElement);
				localize_timeline(mutation.target.parentElement);
				localize_datatable_controls(mutation.target.parentElement);
				localize_list_titles(mutation.target.parentElement);
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
					return;
				}
				if (node.nodeType !== Node.ELEMENT_NODE) return;
				localize_compact_cny(node);
				localize_awesomplete_status(node);
				localize_chart_dates(node);
				localize_timeline(node);
				localize_datatable_controls(node);
				localize_list_titles(node);
			});
		});
	}).observe(document.body, {
		characterData: true,
		childList: true,
		subtree: true,
	});
}

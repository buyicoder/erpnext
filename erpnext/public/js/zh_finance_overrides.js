import {
	format_compact_cny_text,
	format_month_year_text,
	localize_awesomplete_status_text,
} from "./zh_finance_format.mjs";

if (frappe.boot.lang === "zh") {
	Object.assign(frappe._messages, {
		"Begin typing for results.": "输入关键词搜索。",
		Masters: "基础资料",
		Reports: "报表",
	});

	const cny_amount_selector = [
		".number",
		".list-row-container .filterable div",
		"[data-fieldtype='Currency'] .static-area div",
		".control-value",
		".summary-value",
	].join(", ");
	const awesomplete_status_selector = ".awesomplete [role='status']";
	const chart_date_selector = ".chart-container svg text";
	const localize_compact_cny = (root = document) => {
		if (!root) return;
		const elements = root.matches?.(cny_amount_selector)
			? [root]
			: root.querySelectorAll?.(cny_amount_selector) || [];
		elements.forEach((element) => {
			const localized = format_compact_cny_text(element.textContent);
			if (localized !== element.textContent) element.textContent = localized;
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

	localize_compact_cny();
	localize_awesomplete_status();
	localize_chart_dates();
	new MutationObserver((mutations) => {
		mutations.forEach((mutation) => {
			if (mutation.type === "characterData") {
				localize_compact_cny(mutation.target.parentElement);
				localize_awesomplete_status(mutation.target.parentElement);
				localize_chart_dates(mutation.target.parentElement);
				return;
			}
			mutation.addedNodes.forEach((node) => {
				if (node.nodeType === Node.TEXT_NODE) {
					localize_compact_cny(node.parentElement);
					localize_awesomplete_status(node.parentElement);
					localize_chart_dates(node.parentElement);
					return;
				}
				if (node.nodeType !== Node.ELEMENT_NODE) return;
				localize_compact_cny(node);
				localize_awesomplete_status(node);
				localize_chart_dates(node);
			});
		});
	}).observe(document.body, {
		characterData: true,
		childList: true,
		subtree: true,
	});
}

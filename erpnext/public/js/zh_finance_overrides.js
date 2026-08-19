import {
	format_compact_cny_text,
	localize_awesomplete_status_text,
} from "./zh_finance_format.mjs";

if (frappe.boot.lang === "zh") {
	Object.assign(frappe._messages, {
		"Begin typing for results.": "输入关键词搜索。",
		Masters: "基础资料",
		Reports: "报表",
	});

	const cny_amount_selector = ".number, .list-row-container .filterable div";
	const awesomplete_status_selector = ".awesomplete [role='status']";
	const localize_compact_cny = (root = document) => {
		const elements = root.matches?.(cny_amount_selector)
			? [root]
			: root.querySelectorAll?.(cny_amount_selector) || [];
		elements.forEach((element) => {
			element.textContent = format_compact_cny_text(element.textContent);
		});
	};
	const localize_awesomplete_status = (root = document) => {
		if (!root) return;
		const elements = root.matches?.(awesomplete_status_selector)
			? [root]
			: root.querySelectorAll?.(awesomplete_status_selector) || [];
		elements.forEach((element) => {
			element.textContent = localize_awesomplete_status_text(element.textContent);
		});
	};

	localize_compact_cny();
	localize_awesomplete_status();
	new MutationObserver((mutations) => {
		mutations.forEach((mutation) => {
			if (mutation.type === "characterData") {
				localize_awesomplete_status(mutation.target.parentElement);
				return;
			}
			mutation.addedNodes.forEach((node) => {
				if (node.nodeType !== Node.ELEMENT_NODE) return;
				localize_compact_cny(node);
				localize_awesomplete_status(node);
			});
		});
	}).observe(document.body, {
		characterData: true,
		childList: true,
		subtree: true,
	});
}

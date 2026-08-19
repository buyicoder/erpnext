import { format_compact_cny_text } from "./zh_finance_format.mjs";

if (frappe.boot.lang === "zh") {
	Object.assign(frappe._messages, {
		"Begin typing for results.": "输入关键词搜索。",
		Masters: "基础资料",
		Reports: "报表",
	});

	const cny_amount_selector = ".number, .list-row-container .filterable div";
	const localize_compact_cny = (root = document) => {
		const elements = root.matches?.(cny_amount_selector)
			? [root]
			: root.querySelectorAll?.(cny_amount_selector) || [];
		elements.forEach((element) => {
			element.textContent = format_compact_cny_text(element.textContent);
		});
	};

	localize_compact_cny();
	new MutationObserver((mutations) => {
		mutations.forEach((mutation) => {
			mutation.addedNodes.forEach((node) => {
				if (node.nodeType === Node.ELEMENT_NODE) localize_compact_cny(node);
			});
		});
	}).observe(document.body, {
		childList: true,
		subtree: true,
	});
}

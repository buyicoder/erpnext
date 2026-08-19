import { format_compact_cny_text } from "./zh_finance_format.mjs";

if (frappe.boot.lang === "zh") {
	Object.assign(frappe._messages, {
		Masters: "基础资料",
		Reports: "报表",
	});

	const localize_compact_cny = () => {
		document.querySelectorAll(".number").forEach((element) => {
			element.textContent = format_compact_cny_text(element.textContent);
		});
	};

	localize_compact_cny();
	new MutationObserver(localize_compact_cny).observe(document.body, {
		childList: true,
		subtree: true,
	});
}

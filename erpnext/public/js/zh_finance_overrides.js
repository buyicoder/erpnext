if (frappe.boot.lang === "zh") {
	Object.assign(frappe._messages, {
		Masters: "基础资料",
		Reports: "报表",
	});

	const compact_cny_units = { K: 0.1, M: 100, B: 100000 };
	const localize_compact_cny = () => {
		document.querySelectorAll(".number").forEach((element) => {
			const match = element.textContent.trim().match(/^CNY\s+([\d,.]+)\s+([KMB])$/);
			if (!match) return;

			const amount_in_ten_thousands =
				Number.parseFloat(match[1].replaceAll(",", "")) * compact_cny_units[match[2]];
			const rounded_amount = Math.round((amount_in_ten_thousands + Number.EPSILON) * 100) / 100;
			element.textContent = `¥${rounded_amount.toFixed(2)}万`;
		});
	};

	localize_compact_cny();
	new MutationObserver(localize_compact_cny).observe(document.body, {
		childList: true,
		subtree: true,
	});
}

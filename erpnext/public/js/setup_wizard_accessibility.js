frappe.provide("erpnext.setup");

erpnext.setup.localize_awesomplete_status_text = function (text) {
	if (text === "Begin typing for results.") return "输入关键词搜索。";
	if (text === "No results found") return "未找到结果";

	let match = text.match(/^Type (\d+) or more characters for results\.$/);
	if (match) return `请至少输入 ${match[1]} 个字符。`;

	match = text.match(/^(\d+) results found$/);
	if (match) return `找到 ${match[1]} 条结果`;

	match = text.match(/^(.+), list item (\d+) of (\d+)$/);
	if (match) return `${match[1]}，第 ${match[2]} 项，共 ${match[3]} 项`;

	return text;
};

erpnext.setup.localize_awesomplete_statuses = function (root = document) {
	let selected_language =
		document.querySelector('[data-fieldname="language"] input')?.value ||
		frappe.wizard?.values?.language;
	let is_chinese = selected_language
		? selected_language === "中文"
		: document.documentElement.lang.toLowerCase().startsWith("zh");
	if (!is_chinese) return;

	let selector = ".awesomplete [role='status']";
	let elements = root.matches?.(selector) ? [root] : root.querySelectorAll?.(selector) || [];
	for (let element of elements) {
		let localized = erpnext.setup.localize_awesomplete_status_text(element.textContent);
		if (localized !== element.textContent) element.textContent = localized;
	}
};

erpnext.setup.localize_awesomplete_statuses();
new MutationObserver((mutations) => {
	let selector = ".awesomplete [role='status']";
	for (let mutation of mutations) {
		if (mutation.type === "characterData") {
			let parent = mutation.target.parentElement;
			if (parent?.matches(selector)) erpnext.setup.localize_awesomplete_statuses(parent);
		}
		for (let node of mutation.addedNodes || []) {
			let candidate = node.nodeType === Node.TEXT_NODE ? node.parentElement : node;
			if (
				candidate?.matches?.(selector) ||
				candidate?.querySelector?.(selector)
			) {
				erpnext.setup.localize_awesomplete_statuses(candidate);
			}
		}
	}
}).observe(document.body, { childList: true, characterData: true, subtree: true });

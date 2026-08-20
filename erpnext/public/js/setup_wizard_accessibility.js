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

erpnext.setup.is_chinese_language_selected = function () {
	let selected_language =
		document.querySelector('[data-fieldname="language"] input')?.value ||
		frappe.wizard?.values?.language;
	return selected_language
		? selected_language === "中文"
		: document.documentElement.lang.toLowerCase().startsWith("zh");
};

erpnext.setup.localize_awesomplete_statuses = function (root = document) {
	if (!erpnext.setup.is_chinese_language_selected()) return;

	let selector = ".awesomplete [role='status']";
	let elements = root.matches?.(selector)
		? [root]
		: root.querySelectorAll?.(root.matches?.(".awesomplete") ? "[role='status']" : selector) || [];
	for (let element of elements) {
		let localized = erpnext.setup.localize_awesomplete_status_text(element.textContent);
		if (localized !== element.textContent) element.textContent = localized;
	}
};

erpnext.setup.localize_theme_toggle = function (root = document) {
	let selector = ".toggle-theme-btn";
	let elements = root.matches?.(selector) ? [root] : root.querySelectorAll?.(selector) || [];
	for (let element of elements) {
		let label = erpnext.setup.is_chinese_language_selected() ? __("Toggle Theme") : "Toggle Theme";
		for (let attribute of ["data-label", "aria-label", "title"]) {
			element.setAttribute(attribute, label);
		}
	}
};

erpnext.setup.localize_awesomplete_statuses();
erpnext.setup.localize_theme_toggle();
new MutationObserver((mutations) => {
	let selector = ".awesomplete [role='status']";
	let theme_selector = ".toggle-theme-btn";
	for (let mutation of mutations) {
		if (mutation.type === "characterData") {
			let parent = mutation.target.parentElement;
			if (parent?.matches(selector)) {
				erpnext.setup.localize_awesomplete_statuses();
				erpnext.setup.localize_theme_toggle();
			}
		}
		for (let node of mutation.addedNodes || []) {
			let candidate = node.nodeType === Node.TEXT_NODE ? node.parentElement : node;
			if (
				candidate?.matches?.(selector) ||
				candidate?.matches?.(".awesomplete") ||
				candidate?.querySelector?.(".awesomplete")
			) {
				erpnext.setup.localize_awesomplete_statuses();
				erpnext.setup.localize_theme_toggle();
			}
			if (
				candidate?.matches?.(theme_selector) ||
				candidate?.querySelector?.(theme_selector)
			) {
				erpnext.setup.localize_theme_toggle(candidate);
			}
		}
	}
}).observe(document.body, { childList: true, characterData: true, subtree: true });

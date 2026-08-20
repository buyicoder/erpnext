import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

import { localize_awesomplete_status_text } from "../public/js/zh_finance_format.mjs";

const source = fs.readFileSync(
	path.resolve(
		path.dirname(fileURLToPath(import.meta.url)),
		"../public/js/setup_wizard_accessibility.js",
	),
	"utf8",
);

function loadSetupAccessibility({
	fieldLanguage = "中文",
	wizardLanguage = "中文",
	htmlLanguage = "zh",
	initialStatuses = [],
} = {}) {
	const context = {
		erpnext: { setup: {} },
		frappe: { provide() {}, wizard: { values: { language: wizardLanguage } } },
		document: {
			body: {},
			documentElement: { lang: htmlLanguage },
			querySelector: () => (fieldLanguage == null ? null : { value: fieldLanguage }),
			querySelectorAll: () => initialStatuses,
		},
		MutationObserver: class {
			constructor(callback) {
				context.observerCallback = callback;
			}
			observe() {}
		},
		Node: { ELEMENT_NODE: 1, TEXT_NODE: 3 },
	};
	vm.runInNewContext(source, context);
	return context;
}

test("setup wizard accessibility messages stay aligned with the shared Chinese formatter", () => {
	const { erpnext } = loadSetupAccessibility();
	const setup = erpnext.setup;
	for (const message of [
		"Begin typing for results.",
		"Type 2 or more characters for results.",
		"No results found",
		"3 results found",
		"中国, list item 2 of 3",
		", list item 1 of 1",
		"业务原文",
	]) {
		assert.equal(
			setup.localize_awesomplete_status_text(message),
			localize_awesomplete_status_text(message),
		);
	}
});

test("localizes setup status nodes only while Chinese is selected", () => {
	const { erpnext } = loadSetupAccessibility();
	const setup = erpnext.setup;
	const status = { textContent: "1 results found", matches: () => true };

	setup.localize_awesomplete_statuses(status);
	assert.equal(status.textContent, "找到 1 条结果");
});

test("keeps status text unchanged after switching the setup language to English", () => {
	const context = loadSetupAccessibility({
		fieldLanguage: "English",
		wizardLanguage: "English",
		htmlLanguage: "zh",
	});
	const status = {
		textContent: "1 results found",
		matches: (selector) => selector === ".awesomplete [role='status']",
	};
	const textNode = { nodeType: context.Node.TEXT_NODE, parentElement: status };

	context.erpnext.setup.localize_awesomplete_statuses(status);
	context.observerCallback([{ type: "childList", addedNodes: [textNode] }]);

	assert.equal(status.textContent, "1 results found");
});

test("localizes statuses present on the first render", () => {
	const status = { textContent: "Begin typing for results." };

	loadSetupAccessibility({ initialStatuses: [status] });

	assert.equal(status.textContent, "输入关键词搜索。");
});

test("localizes characterData updates in an existing status node", () => {
	const context = loadSetupAccessibility();
	const status = {
		textContent: "No results found",
		matches: (selector) => selector === ".awesomplete [role='status']",
	};

	context.observerCallback([
		{ type: "characterData", target: { parentElement: status }, addedNodes: [] },
	]);

	assert.equal(status.textContent, "未找到结果");
});

test("localizes Awesomplete text nodes added after the initial render", () => {
	const context = loadSetupAccessibility();
	const status = {
		textContent: "1 results found",
		matches: (selector) => selector === ".awesomplete [role='status']",
	};
	const textNode = { nodeType: context.Node.TEXT_NODE, parentElement: status };

	context.observerCallback([{ type: "childList", addedNodes: [textNode] }]);

	assert.equal(status.textContent, "找到 1 条结果");
});

test("localizes statuses nested in newly added elements", () => {
	const context = loadSetupAccessibility();
	const status = { textContent: "No results found" };
	const wrapper = {
		nodeType: context.Node.ELEMENT_NODE,
		matches: (selector) => selector === ".awesomplete",
		querySelector: () => null,
		querySelectorAll: (selector) => (selector === "[role='status']" ? [status] : []),
	};

	context.observerCallback([{ type: "childList", addedNodes: [wrapper] }]);

	assert.equal(status.textContent, "未找到结果");
});

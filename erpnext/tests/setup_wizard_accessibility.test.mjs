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
	initialThemeButtons = [],
} = {}) {
	const context = {
		erpnext: { setup: {} },
		frappe: { provide() {}, wizard: { values: { language: wizardLanguage } } },
		statuses: initialStatuses,
		themeButtons: initialThemeButtons,
		fieldLanguage,
		__: (message) => (message === "Toggle Theme" ? "切换主题" : message),
		document: {
			body: {},
			documentElement: { lang: htmlLanguage },
			querySelector: () =>
				context.fieldLanguage == null ? null : { value: context.fieldLanguage },
			querySelectorAll: (selector) =>
				selector === ".toggle-theme-btn"
					? context.themeButtons
					: context.statuses,
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

test("gives the setup theme toggle a Chinese accessible name", () => {
	const attributes = { "data-label": "Toggle Theme" };
	const button = {
		matches: (selector) => selector === ".toggle-theme-btn",
		getAttribute: (name) => attributes[name],
		setAttribute: (name, value) => {
			attributes[name] = value;
		},
	};
	loadSetupAccessibility({ initialThemeButtons: [button] });

	assert.deepEqual(attributes, {
		"data-label": "切换主题",
		"aria-label": "切换主题",
		title: "切换主题",
	});
});

test("restores the setup theme toggle after switching back to English", () => {
	const attributes = { "data-label": "Toggle Theme" };
	const button = {
		matches: (selector) => selector === ".toggle-theme-btn",
		getAttribute: (name) => attributes[name],
		setAttribute: (name, value) => {
			attributes[name] = value;
		},
	};
	const context = loadSetupAccessibility({ initialThemeButtons: [button] });
	context.fieldLanguage = "English";
	context.erpnext.setup.localize_theme_toggle();

	assert.deepEqual(attributes, {
		"data-label": "Toggle Theme",
		"aria-label": "Toggle Theme",
		title: "Toggle Theme",
	});
});

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
	context.statuses = [status];

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
	context.statuses = [status];

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
	context.statuses = [status];

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
	context.statuses = [status];

	context.observerCallback([{ type: "childList", addedNodes: [wrapper] }]);

	assert.equal(status.textContent, "未找到结果");
});

test("a later language status update also localizes existing setup statuses", () => {
	const context = loadSetupAccessibility();
	const languageStatus = {
		textContent: "1 results found",
		matches: (selector) => selector === ".awesomplete [role='status']",
	};
	const countryStatus = { textContent: "Begin typing for results." };
	context.statuses = [languageStatus, countryStatus];
	const textNode = { nodeType: context.Node.TEXT_NODE, parentElement: languageStatus };

	context.observerCallback([{ type: "childList", addedNodes: [textNode] }]);

	assert.deepEqual(
		context.statuses.map((status) => status.textContent),
		["找到 1 条结果", "输入关键词搜索。"],
	);
});

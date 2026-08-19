import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import vm from "node:vm";

const source = readFileSync(
	new URL("../public/js/zh_audit_list.js", import.meta.url),
	"utf8",
);

const translations = {
	"{0} logged in": "{0}已登录",
	Administrator: "管理员",
	"Sales Invoice": "销售发票",
};

const translate = (message, values = []) =>
	values.reduce(
		(result, value, index) => result.replace(`{${index}}`, value),
		translations[message] || message,
	);

const zhFinance = {
	localize_login_activity_text(value, translator) {
		const match = value.match(/^(.+) logged in$/);
		return match ? translator("{0} logged in", [translator(match[1])]) : value;
	},
	localize_audit_doctype_text(value, translator) {
		return translator(value);
	},
};

const runHook = (lang, listviewSettings) =>
	vm.runInNewContext(source, {
		__: translate,
		frappe: {
			boot: { lang },
			listview_settings: listviewSettings,
			utils: { zh_finance: zhFinance },
		},
	});

test("loads Activity Log hook without requiring Access Log settings", () => {
	const getIndicator = () => ["登录", "green"];
	const onload = () => "native-onload";
	const existingFormatter = (value) => `native:${value}`;
	const activitySettings = {
		formatters: { creation: existingFormatter },
		get_indicator: getIndicator,
		onload,
	};

	assert.doesNotThrow(() => runHook("zh", { "Activity Log": activitySettings }));
	assert.equal(activitySettings.get_indicator, getIndicator);
	assert.equal(activitySettings.onload, onload);
	assert.equal(activitySettings.formatters.creation, existingFormatter);
	assert.equal(
		activitySettings.formatters.subject("Administrator logged in", {}, {}),
		"管理员已登录",
	);
});

test("loads Access Log hook without requiring Activity Log settings", () => {
	const getIndicator = () => ["导出", "blue"];
	const existingFormatter = (value) => `native:${value}`;
	const accessSettings = {
		formatters: { creation: existingFormatter },
		get_indicator: getIndicator,
	};

	assert.doesNotThrow(() => runHook("zh", { "Access Log": accessSettings }));
	assert.equal(accessSettings.get_indicator, getIndicator);
	assert.equal(accessSettings.formatters.creation, existingFormatter);
	assert.equal(
		accessSettings.formatters.export_from("Sales Invoice", {}, {}),
		"销售发票",
	);
});

test("does not modify native list settings outside Chinese locale", () => {
	const existingFormatter = (value) => `native:${value}`;
	const activitySettings = { formatters: { subject: existingFormatter } };

	runHook("en", { "Activity Log": activitySettings });
	assert.equal(activitySettings.formatters.subject, existingFormatter);
});

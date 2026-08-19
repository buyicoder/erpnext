import assert from "node:assert/strict";
import test from "node:test";

import {
	format_compact_cny_text,
	format_month_year_text,
	localize_audit_doctype_text,
	localize_login_activity_text,
	localize_awesomplete_status_text,
} from "../public/js/zh_finance_format.mjs";

test("uses Chinese yuan, ten-thousand and hundred-million units", () => {
	assert.equal(format_compact_cny_text("CNY 1 K"), "¥1,000.00");
	assert.equal(format_compact_cny_text("CNY 363.00 K"), "¥36.30万");
	assert.equal(format_compact_cny_text("CNY 12.5 M"), "¥1,250.00万");
	assert.equal(format_compact_cny_text("CNY 1 B"), "¥10.00亿");
	assert.equal(format_compact_cny_text("CNY 229,000.00"), "¥22.90万");
	assert.equal(format_compact_cny_text("CNY 363.00"), "¥363.00");
});

test("formats report-cell CNY amounts without compact units", () => {
	assert.equal(format_compact_cny_text("CNY 0.00"), "¥0.00");
	assert.equal(format_compact_cny_text(" CNY 1,234.56 "), "¥1,234.56");
});

test("uses Chinese year-month order for chart labels", () => {
	assert.equal(format_month_year_text("Aug 2026"), "2026年8月");
	assert.equal(format_month_year_text("Jan 2025"), "2025年1月");
	[
		"Jan",
		"Feb",
		"Mar",
		"Apr",
		"May",
		"Jun",
		"Jul",
		"Aug",
		"Sep",
		"Oct",
		"Nov",
		"Dec",
	].forEach((month, index) => {
		assert.equal(format_month_year_text(month), `${index + 1}月`);
	});
	assert.equal(format_month_year_text("Jan (金额)"), "1月 (金额)");
	assert.equal(format_month_year_text("月度"), "月度");
	assert.equal(format_month_year_text("Jan sales"), "Jan sales");
	assert.equal(format_month_year_text("constructor"), "constructor");
});

test("preserves values outside the compact CNY contract", () => {
	assert.equal(format_compact_cny_text("USD 363.00 K"), "USD 363.00 K");
	assert.equal(format_compact_cny_text("¥363.00"), "¥363.00");
});

test("localizes every Awesomplete accessibility status", () => {
	assert.equal(localize_awesomplete_status_text("Begin typing for results."), "输入关键词搜索。");
	assert.equal(localize_awesomplete_status_text("Type 2 or more characters for results."), "请至少输入 2 个字符。");
	assert.equal(localize_awesomplete_status_text("No results found"), "未找到结果");
	assert.equal(localize_awesomplete_status_text("3 results found"), "找到 3 条结果");
	assert.equal(localize_awesomplete_status_text("ABC, list item 2 of 3"), "ABC，第 2 项，共 3 项");
	assert.equal(localize_awesomplete_status_text("已翻译"), "已翻译");
});

test("localizes persisted audit labels without changing their stored values", () => {
	const translations = {
		"{0} logged in": "{0}已登录",
		Administrator: "管理员",
		"Sales Invoice": "销售发票",
	};
	const translate = (message, values = []) =>
		(values || []).reduce(
			(result, value, index) => result.replace(`{${index}}`, value),
			translations[message] || message,
		);

	assert.equal(localize_login_activity_text("占永杰 logged in", translate), "占永杰已登录");
	assert.equal(
		localize_login_activity_text("Administrator logged in", translate),
		"管理员已登录",
	);
	assert.equal(localize_login_activity_text("已完成数据导出", translate), "已完成数据导出");
	assert.equal(localize_audit_doctype_text("Sales Invoice", translate), "销售发票");
	assert.equal(localize_audit_doctype_text("自定义来源", translate), "自定义来源");
});

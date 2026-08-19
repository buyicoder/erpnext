import assert from "node:assert/strict";
import test from "node:test";

import {
	format_compact_cny_text,
	format_month_year_text,
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

test("uses Chinese year-month order for chart labels", () => {
	assert.equal(format_month_year_text("Aug 2026"), "2026年8月");
	assert.equal(format_month_year_text("Jan 2025"), "2025年1月");
	assert.equal(format_month_year_text("月度"), "月度");
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

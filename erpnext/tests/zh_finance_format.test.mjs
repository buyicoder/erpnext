import assert from "node:assert/strict";
import test from "node:test";

import {
	format_compact_cny_text,
	format_month_year_text,
	localize_audit_doctype_text,
	localize_compact_cny_element,
	localize_datatable_filter_title,
	localize_login_activity_text,
	localize_list_filter_title,
	localize_list_sort_title,
	localize_list_value_title,
	localize_quill_accessibility_value,
	localize_sidebar_editor_text,
	localize_awesomplete_status_text,
	localize_timeline_element,
	localize_timeline_text,
	localize_tree_level_label,
	localize_version_value_text,
} from "../public/js/zh_finance_format.mjs";

test("localizes Quill toolbar accessibility labels and video prompt", () => {
	const labels = {
		bold: "粗体",
		italic: "斜体",
		underline: "下划线",
		strike: "删除线",
		blockquote: "引用块",
		"code-block": "代码块",
		"direction: rtl": "从右向左",
		link: "链接",
		image: "图片",
		"list: ordered": "有序列表",
		"list: bullet": "无序列表",
		clean: "清除格式",
	};
	for (const [source, translation] of Object.entries(labels)) {
		assert.equal(localize_quill_accessibility_value("aria-label", source), translation);
	}
	assert.equal(localize_quill_accessibility_value("data-video", "Embed URL"), "输入视频地址");
	assert.equal(localize_quill_accessibility_value("aria-label", "custom-action"), "custom-action");
	assert.equal(localize_quill_accessibility_value("data-link", "https://quilljs.com"), "https://quilljs.com");
});

test("localizes only the hard-coded workspace sidebar editor controls", () => {
	const translate = (message) =>
		({ "Add Sidebar Item": "添加侧栏项目", Discard: "放弃更改", Save: "保存" })[message] ||
		message;
	assert.equal(localize_sidebar_editor_text("Add Sidebar Item", translate), "添加侧栏项目");
	assert.equal(localize_sidebar_editor_text("Discard", translate), "放弃更改");
	assert.equal(localize_sidebar_editor_text("Save", translate), "保存");
	assert.equal(localize_sidebar_editor_text("Customer Save", translate), "Customer Save");
	assert.equal(localize_sidebar_editor_text("保存", translate), "保存");
});

test("uses Chinese yuan, ten-thousand and hundred-million units", () => {
	assert.equal(format_compact_cny_text("CNY 1 K"), "¥1,000.00");
	assert.equal(format_compact_cny_text("CNY 363.00 K"), "¥36.30万");
	assert.equal(format_compact_cny_text("CNY 12.5 M"), "¥1,250.00万");
	assert.equal(format_compact_cny_text("CNY 1 B"), "¥10.00亿");
	assert.equal(format_compact_cny_text("CNY 229,000.00"), "¥22.90万");
	assert.equal(format_compact_cny_text("CNY 363.00"), "¥363.00");
	assert.equal(format_compact_cny_text("CNY -363.00 K"), "-¥36.30万");
	assert.equal(format_compact_cny_text("CNY -1 B"), "-¥10.00亿");
	assert.equal(format_compact_cny_text("CNY -363.00"), "-¥363.00");
});

test("localizes report datatable accessibility labels", () => {
	const translate = (message, values = []) =>
		({ "Filter based on {0}": `按 ${values[0]} 筛选`, "Tree Level": "树形层级" })[
			message
		] || message;
	assert.equal(localize_datatable_filter_title("Filter based on 科目", translate), "按 科目 筛选");
	assert.equal(localize_datatable_filter_title("按科目筛选", translate), "按科目筛选");
	assert.equal(localize_tree_level_label("Tree Level", translate), "树形层级");
	assert.equal(localize_tree_level_label("Level", translate), "Level");
});

test("localizes list sorting and translated-value tooltips", () => {
	const translate = (message, values = []) =>
		({
			"Click to sort by {0}": `点击按${values[0]}排序`,
			Receive: "收款",
			Pay: "付款",
		})[message] || message;

	assert.equal(
		localize_list_sort_title("点击按Customer Name排序", "客户名称", translate),
		"点击按客户名称排序",
	);
	assert.equal(localize_list_value_title("付款类型: Receive", "收款", translate), "付款类型: 收款");
	assert.equal(localize_list_value_title("客户: Grant Plastics Ltd.", "Grant Plastics Ltd.", translate), "客户: Grant Plastics Ltd.");
	assert.equal(localize_list_value_title("付款类型: Receive", "其他值", translate), "付款类型: Receive");
});

test("localizes singular and plural applied-filter tooltips", () => {
	const translate = (message, values = []) =>
		message === "{0} Filters Applied" ? `已应用 ${values[0]} 个筛选条件` : message;

	assert.equal(localize_list_filter_title("1 Filter Applied", translate), "已应用 1 个筛选条件");
	assert.equal(localize_list_filter_title("3 Filters Applied", translate), "已应用 3 个筛选条件");
	assert.equal(localize_list_filter_title("Filter Applied", translate), "Filter Applied");
});

test("localizes nested CNY text without replacing its wrapper", () => {
	const textNode = { nodeType: 3, textContent: "CNY 363.00 K" };
	const span = { nodeType: 1, className: "amount", childNodes: [textNode] };
	const element = { childNodes: [span] };

	assert.deepEqual(localize_compact_cny_element(element), {
		localized: "¥36.30万",
		original: "CNY 363.00 K",
	});
	assert.equal(element.childNodes[0], span);
	assert.equal(span.className, "amount");
	assert.equal(textNode.textContent, "¥36.30万");
	assert.equal(localize_compact_cny_element(element), null);
});

test("localizes exact persisted timeline values while preserving surrounding whitespace", () => {
	const translate = (message) =>
		({
			"To Deliver and Bill": "待出货与开票",
			"To Receive and Bill": "待入库与开票",
			"Grant Plastics Ltd.": "不应翻译的客户名",
		})[message] || message;

	assert.equal(localize_timeline_text(" To Deliver and Bill", translate), " 待出货与开票");
	assert.equal(localize_timeline_text("To Receive and Bill ", translate), "待入库与开票 ");
	assert.equal(localize_timeline_text(" · 昨天", translate), " · 昨天");
	assert.equal(localize_timeline_text("Grant Plastics Ltd.", translate), "Grant Plastics Ltd.");
});

test("localizes only null values inside generated version changes", () => {
	const translate = (message) => ({ "Not Set": "空值" })[message] || message;
	assert.equal(localize_version_value_text("null", translate), "空值");
	assert.equal(localize_version_value_text(" null ", translate), "空值");
	assert.equal(localize_version_value_text("customer null", translate), "customer null");
	assert.equal(localize_version_value_text("0", translate), "0");
});

test("localizes only direct approved timeline values and is idempotent", () => {
	const statusNode = { nodeType: 3, textContent: " To Deliver and Bill" };
	const businessNode = { nodeType: 3, textContent: "Grant Plastics Ltd." };
	const nestedTimestamp = { nodeType: 1, textContent: "To Deliver and Bill" };
	const element = { childNodes: [statusNode, businessNode, nestedTimestamp] };
	const translate = (message) =>
		({
			"To Deliver and Bill": "待出货与开票",
			"Grant Plastics Ltd.": "不应翻译的客户名",
		})[message] || message;

	assert.equal(localize_timeline_element(element, translate), 1);
	assert.equal(statusNode.textContent, " 待出货与开票");
	assert.equal(businessNode.textContent, "Grant Plastics Ltd.");
	assert.equal(nestedTimestamp.textContent, "To Deliver and Bill");
	assert.equal(localize_timeline_element(element, translate), 0);
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

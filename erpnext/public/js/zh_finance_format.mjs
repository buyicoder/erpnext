const COMPACT_CNY_MULTIPLIERS = {
	K: 1_000,
	M: 1_000_000,
	B: 1_000_000_000,
};

const format_decimal = (value) =>
	new Intl.NumberFormat("zh-CN", {
		minimumFractionDigits: 2,
		maximumFractionDigits: 2,
	}).format(value);

export const format_compact_cny_text = (text) => {
	const match = text.trim().match(/^CNY\s+(-?[\d,.]+)(?:\s*([KMB]))?$/);
	if (!match) return text;

	const compact_value = Number.parseFloat(match[1].replaceAll(",", ""));
	if (!Number.isFinite(compact_value)) return text;

	const amount = compact_value * (COMPACT_CNY_MULTIPLIERS[match[2]] || 1);
	const sign = amount < 0 ? "-" : "";
	const absolute_amount = Math.abs(amount);
	if (absolute_amount >= 100_000_000) {
		return `${sign}¥${format_decimal(absolute_amount / 100_000_000)}亿`;
	}
	if (absolute_amount >= 10_000) {
		return `${sign}¥${format_decimal(absolute_amount / 10_000)}万`;
	}
	return `${sign}¥${format_decimal(absolute_amount)}`;
};

export const localize_compact_cny_element = (element, text_node_type = 3) => {
	const text_nodes = [];
	const visit = (node) => {
		if (node.nodeType === text_node_type) {
			if (node.textContent.trimStart().startsWith("CNY ")) text_nodes.push(node);
			return;
		}
		node.childNodes?.forEach(visit);
	};
	element.childNodes.forEach(visit);
	if (text_nodes.length !== 1) return null;

	const node = text_nodes[0];
	const original = node.textContent.trim();
	const localized = format_compact_cny_text(node.textContent);
	if (localized === node.textContent) return null;
	node.textContent = localized;
	return { localized, original };
};

export const localize_awesomplete_status_text = (text) => {
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

export const localize_login_activity_text = (text, translate) => {
	const match = text.match(/^(.+) logged in$/);
	return match ? translate("{0} logged in", [translate(match[1])]) : text;
};

export const localize_audit_doctype_text = (text, translate) => translate(text);

export const localize_datatable_filter_title = (text, translate) => {
	const match = text.match(/^Filter based on (.+)$/);
	return match ? translate("Filter based on {0}", [match[1]]) : text;
};

export const localize_tree_level_label = (text, translate) =>
	text === "Tree Level" ? translate(text) : text;

export const localize_assignment_actions_label = (text, translate) =>
	text === "Actions" ? translate(text) : text;

const PHOTOSWIPE_TITLES = {
	"Close (Esc)": "关闭（Esc）",
	Share: "共享",
	"Toggle fullscreen": "切换全屏",
	"Zoom in/out": "放大或缩小",
	"Previous (arrow left)": "上一张（左方向键）",
	"Next (arrow right)": "下一张（右方向键）",
};

export const localize_photoswipe_title = (title) =>
	Object.hasOwn(PHOTOSWIPE_TITLES, title) ? PHOTOSWIPE_TITLES[title] : title;

export const localize_list_sort_title = (title, visible_label, translate) => {
	if (!title || !visible_label) return title;
	return translate("Click to sort by {0}", [visible_label.trim()]);
};

export const localize_list_filter_title = (title, translate) => {
	const match = title?.match(/^(\d+) Filters? Applied$/);
	return match ? translate("{0} Filters Applied", [match[1]]) : title;
};

export const localize_list_value_title = (title, visible_value, translate) => {
	const match = title?.match(/^(.+): (.+)$/);
	if (!match) return title;
	const localized_value = translate(match[2]);
	if (localized_value === match[2] || localized_value !== visible_value.trim()) return title;
	return `${match[1]}: ${localized_value}`;
};

const SIDEBAR_EDITOR_LABELS = new Set(["Add Sidebar Item", "Discard", "Save"]);

export const localize_sidebar_editor_text = (text, translate) => {
	const normalized = text.trim();
	if (!SIDEBAR_EDITOR_LABELS.has(normalized)) return text;
	return text.replace(normalized, translate(normalized));
};

const QUILL_ACCESSIBILITY_LABELS = {
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

export const localize_quill_accessibility_value = (attribute, value) => {
	if (attribute === "aria-label") return QUILL_ACCESSIBILITY_LABELS[value] || value;
	if (attribute === "data-video" && value === "Embed URL") return "输入视频地址";
	return value;
};

const LOCALIZABLE_TIMELINE_VALUES = new Set(["To Deliver and Bill", "To Receive and Bill"]);

export const localize_version_value_text = (text, translate) =>
	text.trim() === "null" ? translate("Not Set") : text;

export const localize_timeline_text = (text, translate) => {
	const normalized = text.trim();
	if (!LOCALIZABLE_TIMELINE_VALUES.has(normalized)) return text;

	const localized = translate(normalized);
	return localized === normalized ? text : text.replace(normalized, localized);
};

export const localize_timeline_element = (element, translate, text_node_type = 3) => {
	let writes = 0;
	element.childNodes.forEach((node) => {
		if (node.nodeType !== text_node_type) return;
		const localized = localize_timeline_text(node.textContent, translate);
		if (localized === node.textContent) return;
		node.textContent = localized;
		writes += 1;
	});
	return writes;
};

const MONTHS = {
	Jan: 1,
	Feb: 2,
	Mar: 3,
	Apr: 4,
	May: 5,
	Jun: 6,
	Jul: 7,
	Aug: 8,
	Sep: 9,
	Oct: 10,
	Nov: 11,
	Dec: 12,
};

export const format_month_year_text = (text) => {
	const normalized = text.trim();
	const month_label = normalized.match(/^([A-Z][a-z]{2})(\s+\([^)]*\))?$/);
	if (month_label && Object.hasOwn(MONTHS, month_label[1])) {
		return `${MONTHS[month_label[1]]}月${month_label[2] || ""}`;
	}

	const match = normalized.match(/^([A-Z][a-z]{2})\s+(\d{4})$/);
	if (!match || !Object.hasOwn(MONTHS, match[1])) return text;
	return `${match[2]}年${MONTHS[match[1]]}月`;
};

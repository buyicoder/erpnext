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
	const match = text.trim().match(/^CNY\s+([\d,.]+)(?:\s*([KMB]))?$/);
	if (!match) return text;

	const compact_value = Number.parseFloat(match[1].replaceAll(",", ""));
	if (!Number.isFinite(compact_value)) return text;

	const amount = compact_value * (COMPACT_CNY_MULTIPLIERS[match[2]] || 1);
	if (amount >= 100_000_000) return `¥${format_decimal(amount / 100_000_000)}亿`;
	if (amount >= 10_000) return `¥${format_decimal(amount / 10_000)}万`;
	return `¥${format_decimal(amount)}`;
};

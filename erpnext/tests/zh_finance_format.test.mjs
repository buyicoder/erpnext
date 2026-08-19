import assert from "node:assert/strict";
import test from "node:test";

import { format_compact_cny_text } from "../public/js/zh_finance_format.mjs";

test("uses Chinese yuan, ten-thousand and hundred-million units", () => {
	assert.equal(format_compact_cny_text("CNY 1 K"), "¥1,000.00");
	assert.equal(format_compact_cny_text("CNY 363.00 K"), "¥36.30万");
	assert.equal(format_compact_cny_text("CNY 12.5 M"), "¥1,250.00万");
	assert.equal(format_compact_cny_text("CNY 1 B"), "¥10.00亿");
	assert.equal(format_compact_cny_text("CNY 229,000.00"), "¥22.90万");
	assert.equal(format_compact_cny_text("CNY 363.00"), "¥363.00");
});

test("preserves values outside the compact CNY contract", () => {
	assert.equal(format_compact_cny_text("USD 363.00 K"), "USD 363.00 K");
	assert.equal(format_compact_cny_text("¥363.00"), "¥363.00");
});

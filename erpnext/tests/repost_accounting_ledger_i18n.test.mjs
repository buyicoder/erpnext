import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import vm from "node:vm";


test("accounting ledger preview passes translated copy to render_grid", async () => {
	const sourceUrl = new URL(
		"../accounts/doctype/repost_accounting_ledger/repost_accounting_ledger.js",
		import.meta.url
	);
	const source = await readFile(sourceUrl, "utf8");
	let formEvents;
	let renderOptions;
	const escapedValues = [];
	const translations = {
		"Generating Preview": "正在生成预览…",
		"Accounting Ledger Repost Preview": "会计凭证重新过账预览",
		"Review the accounting entries before reposting.": "请在重新过账前核对会计凭证明细。",
	};
	const context = {
		__: (message) => translations[message] ?? message,
		frappe: {
			utils: {
				escape_html(value) {
					escapedValues.push(value);
					return `[escaped]${value}`;
				},
			},
			ui: {
				form: {
					on(_doctype, events) {
						formEvents = events;
					},
				},
			},
			render_grid(options) {
				renderOptions = options;
			},
		},
	};
	vm.runInNewContext(source, context);
	assert.ok(formEvents?.generate_preview);

	let callOptions;
	const frm = {
		doc: { name: "ACC-REPOST-0001" },
		call(options) {
			callOptions = options;
			options.callback({ message: "<table>预览内容</table>" });
		},
	};
	formEvents.generate_preview(frm);

	assert.equal(callOptions.freeze, true);
	assert.equal(callOptions.freeze_message, "正在生成预览…");
	assert.equal(renderOptions.title, "会计凭证重新过账预览");
	assert.deepEqual(escapedValues, ["请在重新过账前核对会计凭证明细。"]);
	assert.equal(
		renderOptions.content,
		'<p class="text-muted">[escaped]请在重新过账前核对会计凭证明细。</p><table>预览内容</table>'
	);
});

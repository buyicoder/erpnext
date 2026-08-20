import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const source = fs.readFileSync(
	path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../public/js/setup_wizard.js"),
	"utf8",
);

function loadSetupWizard() {
	const calls = [];
	const context = {
		__: (value) => ({ Standard: "标准", "Standard with Numbers": "标准（带编号）" })[value] || value,
		erpnext: { setup: {} },
		frappe: {
			provide() {},
			pages: { "setup-wizard": {} },
			sys_defaults: {},
			setup: { on() {}, add_slide() {} },
			wizard: { values: { country: "China" } },
			defaults: { get_default: () => "China" },
			call(options) {
				calls.push(options);
			},
		},
	};
	vm.runInNewContext(source, context);
	return { ...context, calls };
}

test("keeps stable Chinese chart options when the country template request fails", () => {
	const { erpnext, calls } = loadSetupWizard();
	const rendered = [];
	const input = {
		empty() {
			return this;
		},
		add_options(options) {
			rendered.push(options);
			return this;
		},
	};
	const slide = { get_input: () => input };
	const organization = erpnext.setup.slides_settings.find(({ name }) => name === "organization");

	organization.load_chart_of_accounts(slide);
	assert.deepEqual(JSON.parse(JSON.stringify(rendered[0])), [
		{ value: "Standard", label: "标准" },
		{ value: "Standard with Numbers", label: "标准（带编号）" },
	]);
	assert.equal(calls.length, 1);
	assert.equal(calls[0].silent, true);

	calls[0].error();
	assert.deepEqual(rendered[1], rendered[0]);
});

test("replaces fallback options with country-specific templates after a successful request", () => {
	const { erpnext, calls } = loadSetupWizard();
	const rendered = [];
	const input = {
		empty() {
			return this;
		},
		add_options(options) {
			rendered.push(options);
			return this;
		},
	};
	const organization = erpnext.setup.slides_settings.find(({ name }) => name === "organization");

	organization.load_chart_of_accounts({ get_input: () => input });
	calls[0].callback({ message: ["Standard", "China - Chart of Accounts"] });
	assert.deepEqual(JSON.parse(JSON.stringify(rendered.at(-1))), [
		{ value: "Standard", label: "标准" },
		{ value: "China - Chart of Accounts", label: "China - Chart of Accounts" },
	]);
});

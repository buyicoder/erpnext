#!/usr/bin/env python3
from pathlib import Path


SELECTOR_SETUP = '''\t\tthis.print_format_selector = this.add_sidebar_item({
\t\t\tfieldtype: "Link",
\t\t\tfieldname: "print_format",
\t\t\toptions: "Print Format",
\t\t\tlabel: __("Print Format"),
\t\t\tget_query: () => {
\t\t\t\treturn { filters: { doc_type: this.frm.doctype } };
\t\t\t},
\t\t\tchange: () => this.refresh_print_format(),
\t\t}).$input;'''

SELECTOR_SETUP_PATCHED = '''\t\tthis.print_format_control = this.add_sidebar_item({
\t\t\tfieldtype: "Link",
\t\t\tfieldname: "print_format",
\t\t\toptions: "Print Format",
\t\t\tlabel: __("Print Format"),
\t\t\tget_query: () => {
\t\t\t\treturn { filters: { doc_type: this.frm.doctype } };
\t\t\t},
\t\t\tchange: () => this.refresh_print_format(),
\t\t});
\t\tthis.print_format_selector = this.print_format_control.$input;'''

DEFAULT_FORMAT = '''\tset_default_print_format() {
\t\tif (
\t\t\tfrappe.meta
\t\t\t\t.get_print_formats(this.frm.doctype)
\t\t\t\t.includes(this.print_format_selector.val())
\t\t)
\t\t\treturn;

\t\tthis.print_format_selector.empty();
\t\tthis.print_format_selector.val(this.frm.meta.default_print_format || "");
\t}'''

DEFAULT_FORMAT_PATCHED = '''\tset_default_print_format() {
\t\tconst selected_format = this.print_format_selector.val();
\t\tif (frappe.meta.get_print_formats(this.frm.doctype).includes(selected_format)) {
\t\t\treturn this.print_format_control.set_value(selected_format);
\t\t}

\t\tthis.print_format_selector.empty();
\t\treturn this.print_format_control.set_value(this.frm.meta.default_print_format || "");
\t}'''

SELECTED_FORMAT = '''\tselected_format() {
\t\treturn this.print_format_selector.val() || "Standard";
\t}'''

SELECTED_FORMAT_PATCHED = '''\tselected_format() {
\t\treturn this.print_format_control.get_value() || "Standard";
\t}'''

LETTER_HEAD_SETUP = '''\t\tthis.letterhead_selector = this.add_sidebar_item({
\t\t\tfieldtype: "Link",
\t\t\tfieldname: "letterhead",
\t\t\toptions: "Letter Head",
\t\t\tlabel: __("Letter Head"),
\t\t\tdescription: description,
\t\t\tchange: function () {
\t\t\t\tthis.set_description(this.get_value() ? description : "");
\t\t\t\tprint_view.preview();
\t\t\t},
\t\t}).$input;'''

LETTER_HEAD_SETUP_PATCHED = '''\t\tthis.letterhead_control = this.add_sidebar_item({
\t\t\tfieldtype: "Link",
\t\t\tfieldname: "letterhead",
\t\t\toptions: "Letter Head",
\t\t\tlabel: __("Letter Head"),
\t\t\tdescription: description,
\t\t\tchange: function () {
\t\t\t\tthis.set_description(this.get_value() ? description : "");
\t\t\t\tprint_view.preview();
\t\t\t},
\t\t});
\t\tthis.letterhead_selector = this.letterhead_control.$input;'''

DEFAULT_LETTER_HEAD = '''\tset_default_letterhead() {
\t\tconst get_default = () =>
\t\t\tfrappe.db
\t\t\t\t.get_value("Letter Head", { disabled: 0, is_default: 1 }, "name")
\t\t\t\t.then(({ message }) => {
\t\t\t\t\tif (message?.name) this.letterhead_selector.val(message.name);
\t\t\t\t});

\t\tif (!this.frm.doc.letter_head) return get_default();

\t\treturn frappe.db
\t\t\t.get_value("Letter Head", { name: this.frm.doc.letter_head, disabled: 0 }, "name")
\t\t\t.then(({ message }) =>
\t\t\t\tmessage?.name ? this.letterhead_selector.val(message.name) : get_default()
\t\t\t);
\t}'''

DEFAULT_LETTER_HEAD_PATCHED = '''\tset_default_letterhead() {
\t\tconst get_default = () =>
\t\t\tfrappe.db
\t\t\t\t.get_value("Letter Head", { disabled: 0, is_default: 1 }, "name")
\t\t\t\t.then(({ message }) => {
\t\t\t\t\tif (message?.name) return this.letterhead_control.set_value(message.name);
\t\t\t\t});

\t\tif (!this.frm.doc.letter_head) return get_default();

\t\treturn frappe.db
\t\t\t.get_value("Letter Head", { name: this.frm.doc.letter_head, disabled: 0 }, "name")
\t\t\t.then(({ message }) =>
\t\t\t\tmessage?.name ? this.letterhead_control.set_value(message.name) : get_default()
\t\t\t);
\t}'''

GET_LETTER_HEAD = '''\tget_letterhead() {
\t\treturn this.letterhead_selector.val() || __("No Letterhead");
\t}'''

GET_LETTER_HEAD_PATCHED = '''\tget_letterhead() {
\t\treturn this.letterhead_control.get_value() || __("No Letterhead");
\t}'''


def patch_text(source: str) -> str:
	for original in (
		SELECTOR_SETUP,
		DEFAULT_FORMAT,
		SELECTED_FORMAT,
		LETTER_HEAD_SETUP,
		DEFAULT_LETTER_HEAD,
		GET_LETTER_HEAD,
	):
		if source.count(original) != 1:
			raise ValueError("Pinned Frappe print page no longer matches the expected source contract")
	return (
		source.replace(SELECTOR_SETUP, SELECTOR_SETUP_PATCHED)
		.replace(DEFAULT_FORMAT, DEFAULT_FORMAT_PATCHED)
		.replace(SELECTED_FORMAT, SELECTED_FORMAT_PATCHED)
		.replace(LETTER_HEAD_SETUP, LETTER_HEAD_SETUP_PATCHED)
		.replace(DEFAULT_LETTER_HEAD, DEFAULT_LETTER_HEAD_PATCHED)
		.replace(GET_LETTER_HEAD, GET_LETTER_HEAD_PATCHED)
	)


def main():
	path = Path(
		"/home/frappe/frappe-bench/apps/frappe/frappe/printing/page/print/print.js"
	)
	path.write_text(patch_text(path.read_text()))


if __name__ == "__main__":
	main()

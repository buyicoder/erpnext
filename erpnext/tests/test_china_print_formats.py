import json
from pathlib import Path
from unittest import TestCase


PRINT_FORMAT_ROOT = Path(__file__).parents[1] / "accounts" / "print_format"
LETTERHEAD_ROOT = Path(__file__).parents[1] / "accounts" / "letter_head"
LETTERHEAD_TEMPLATE_ROOT = Path(__file__).parents[1] / "accounts" / "letterhead"


class TestChinaPrintFormats(TestCase):
	def test_all_china_print_formats_default_to_chinese(self):
		for relative_path in (
			"pos_invoice_with_item_image/pos_invoice_with_item_image.json",
			"sales_invoice_with_item_image/sales_invoice_with_item_image.json",
			"cheque_printing_format/cheque_printing_format.json",
			"purchase_auditing_voucher/purchase_auditing_voucher.json",
			"sales_auditing_voucher/sales_auditing_voucher.json",
			"bank_and_cash_payment_voucher/bank_and_cash_payment_voucher.json",
			"journal_auditing_voucher/journal_auditing_voucher.json",
		):
			with self.subTest(print_format=relative_path):
				print_format = json.loads((PRINT_FORMAT_ROOT / relative_path).read_text())
				self.assertEqual(print_format["default_print_language"], "zh")

	def test_auditing_vouchers_translate_every_visible_label(self):
		for name in ("purchase_auditing_voucher", "sales_auditing_voucher"):
			html = (PRINT_FORMAT_ROOT / name / f"{name}.html").read_text()
			with self.subTest(print_format=name):
				self.assertNotIn("<th>SL</th>", html)
				self.assertNotIn("<strong>Total</strong>", html)
				self.assertIn('{{ _("Voucher No") }}', html)
				self.assertIn('{{ _("Total Taxes and Charges") }}', html)

	def test_ledger_vouchers_translate_debit_credit_and_remarks(self):
		for name in ("bank_and_cash_payment_voucher", "journal_auditing_voucher"):
			html = (PRINT_FORMAT_ROOT / name / f"{name}.html").read_text()
			with self.subTest(print_format=name):
				self.assertIn('{{ _("Debit") }}', html)
				self.assertIn('{{ _("Credit") }}', html)
				self.assertIn('{{ _("Total Debit") }}', html)
				self.assertIn('{{ _("Total Credit") }}', html)
				self.assertIn('{{ _("Remarks") }}', html)

	def test_finance_print_formats_do_not_hardcode_english_labels(self):
		formats = {
			"pos_invoice_with_item_image/pos_invoice_with_item_image.json": (
				"Customer Name:",
				"Bill to:",
				"Invoice Number:",
				"Invoice Date:",
				"Payment Due Date:",
			),
			"sales_invoice_with_item_image/sales_invoice_with_item_image.json": (
				"Customer Name:",
				"Bill to:",
				"Invoice Number:",
				"Invoice Date:",
				"Payment Due Date:",
			),
			"cheque_printing_format/cheque_printing_format.json": (
				"Prepared By",
				"Authorised Signatory",
				"Received Payment as Above",
				"A/C Payee",
			),
		}

		for relative_path, labels in formats.items():
			html = json.loads((PRINT_FORMAT_ROOT / relative_path).read_text())["html"]
			for label in labels:
				with self.subTest(print_format=relative_path, label=label):
					self.assertNotIn(f">{label}<", html)
					self.assertIn(f'{{{{ _("{label}") }}}}', html)

	def test_invoice_print_formats_use_chinese_specific_labels_and_exact_cny_money(self):
		for relative_path in (
			"pos_invoice_with_item_image/pos_invoice_with_item_image.json",
			"sales_invoice_with_item_image/sales_invoice_with_item_image.json",
		):
			print_format = json.loads((PRINT_FORMAT_ROOT / relative_path).read_text())
			html = print_format["html"]
			with self.subTest(print_format=relative_path):
				self.assertEqual(print_format["default_print_language"], "zh")
				self.assertIn('{{ _("Row No.") }}', html)
				self.assertIn("{{ _(item.uom) }}", html)
				self.assertNotIn("{{ item.uom }}", html)
				self.assertGreaterEqual(html.count("format_china_money("), 6)
				self.assertNotIn('{{ _("No") }}', html)
				self.assertIn("@media screen and (max-width: 600px)", html)
				self.assertIn(".info-table > tbody > tr > td", html)
				self.assertEqual(html.count("table.highlight-bg tr"), 1)

	def test_default_company_letterhead_localizes_document_type(self):
		letterhead = json.loads(
			(LETTERHEAD_ROOT / "company_letterhead___grey/company_letterhead___grey.json").read_text()
		)
		template = (LETTERHEAD_TEMPLATE_ROOT / "company_letterhead_grey.html").read_text()

		for content in (letterhead["content"], template):
			self.assertIn("{{ _(doc.doctype) }}", content)
			self.assertNotIn("{{ doc.doctype }}", content)

import ast
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from erpnext.stock import stock_ledger


class TestStockLedgerI18n(TestCase):
	def test_reposting_required_fields_use_translated_template_and_label(self):
		labels = {
			"Item Code": "物料号",
			"Warehouse": "仓库",
			"Posting Date": "记账日期",
			"Posting Time": "记账时间",
		}
		template = "The field {0} is required for the reposting"

		for missing_field, expected_label in labels.items():
			args = {
				"item_code": "ITEM-001",
				"warehouse": "Stores - TC",
				"posting_date": "2026-08-20",
				"posting_time": "09:30:00",
			}
			args[stock_ledger.frappe.scrub(missing_field)] = None

			def translate(message):
				if message == template:
					return "库存重算必须填写“{0}”"
				return labels.get(message, message)

			with (
				self.subTest(field=missing_field),
				patch.object(stock_ledger, "_", side_effect=translate),
				patch.object(stock_ledger.frappe, "throw", side_effect=RuntimeError) as throw,
				self.assertRaises(RuntimeError),
			):
				stock_ledger.validate_item_warehouse(args)

			throw.assert_called_once_with(f"库存重算必须填写“{expected_label}”")

	def test_empty_required_field_uses_the_same_translated_validation(self):
		args = {
			"item_code": "ITEM-001",
			"warehouse": "",
			"posting_date": "2026-08-20",
			"posting_time": "09:30:00",
		}
		template = "The field {0} is required for the reposting"

		def translate(message):
			return {
				template: "库存重算必须填写“{0}”",
				"Warehouse": "仓库",
			}.get(message, message)

		with (
			patch.object(stock_ledger, "_", side_effect=translate),
			patch.object(stock_ledger.frappe, "throw", side_effect=RuntimeError) as throw,
			self.assertRaises(RuntimeError),
		):
			stock_ledger.validate_item_warehouse(args)

		throw.assert_called_once_with("库存重算必须填写“仓库”")

	def test_source_never_translates_an_interpolated_reposting_error(self):
		text = Path(stock_ledger.__file__).read_text()
		self.assertNotIn("frappe.throw(_(validation_msg))", text)

		tree = ast.parse(text)
		function = next(
			node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "validate_item_warehouse"
		)
		throw_call = next(
			node
			for node in ast.walk(function)
			if isinstance(node, ast.Call)
			and isinstance(node.func, ast.Attribute)
			and node.func.attr == "throw"
		)
		formatted = throw_call.args[0]
		self.assertIsInstance(formatted, ast.Call)
		self.assertEqual(formatted.func.attr, "format")
		translated = formatted.func.value
		self.assertEqual(translated.func.id, "_")
		self.assertEqual(translated.args[0].value, "The field {0} is required for the reposting")

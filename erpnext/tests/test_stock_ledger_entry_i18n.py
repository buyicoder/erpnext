import ast
from pathlib import Path
from types import MethodType, SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch

from erpnext.stock.doctype.stock_ledger_entry import stock_ledger_entry


class TestStockLedgerEntryI18n(TestCase):
	def _assert_validation(self, *, item, bundle, template, translation, expected, exception):
		sle = SimpleNamespace(
			item_code="ITEM-001",
			is_cancelled=0,
			has_batch_no=item.has_batch_no if item else 0,
			has_serial_no=item.has_serial_no if item else 0,
			serial_and_batch_bundle=bundle,
			db_set=Mock(),
		)
		sle.throw_error_message = MethodType(stock_ledger_entry.StockLedgerEntry.throw_error_message, sle)

		with (
			patch.object(stock_ledger_entry.frappe, "get_cached_value", return_value=item),
			patch.object(
				stock_ledger_entry,
				"_",
				side_effect=lambda message: translation if message == template else message,
			),
			patch.object(stock_ledger_entry.frappe, "throw", side_effect=RuntimeError) as throw,
			self.assertRaises(RuntimeError),
		):
			stock_ledger_entry.StockLedgerEntry.validate_serial_batch_no_bundle(sle)

		throw.assert_called_once_with(expected, exception)
		return sle

	def test_template_item_error_translates_before_inserting_item_code(self):
		template = "Stock cannot exist for Item {0} since it has variants"
		translation = "物料 {0} 是模板物料，不能登记库存"
		sle = SimpleNamespace(
			item_code="ITEM-TEMPLATE",
			is_cancelled=0,
			has_batch_no=0,
			has_serial_no=0,
			serial_and_batch_bundle=None,
			db_set=Mock(),
		)
		item = SimpleNamespace(
			has_batch_no=0,
			has_serial_no=0,
			is_stock_item=1,
			has_variants=1,
		)
		sle.throw_error_message = MethodType(stock_ledger_entry.StockLedgerEntry.throw_error_message, sle)

		with (
			patch.object(stock_ledger_entry.frappe, "get_cached_value", return_value=item),
			patch.object(
				stock_ledger_entry,
				"_",
				side_effect=lambda message: translation if message == template else message,
			),
			patch.object(stock_ledger_entry.frappe, "throw") as throw,
		):
			stock_ledger_entry.StockLedgerEntry.validate_serial_batch_no_bundle(sle)

		throw.assert_called_once_with(
			"物料 ITEM-TEMPLATE 是模板物料，不能登记库存",
			stock_ledger_entry.ItemTemplateCannotHaveStock,
		)

	def test_missing_item_raises_translated_validation_instead_of_attribute_error(self):
		template = "Item {0} not found"
		translation = "未找到物料 {0}"
		sle = SimpleNamespace(
			item_code="ITEM-MISSING",
			is_cancelled=0,
			has_batch_no=0,
			has_serial_no=0,
			serial_and_batch_bundle=None,
			db_set=Mock(),
		)
		sle.throw_error_message = MethodType(stock_ledger_entry.StockLedgerEntry.throw_error_message, sle)

		with (
			patch.object(stock_ledger_entry.frappe, "get_cached_value", return_value=None),
			patch.object(
				stock_ledger_entry,
				"_",
				side_effect=lambda message: translation if message == template else message,
			),
			patch.object(stock_ledger_entry.frappe, "throw") as throw,
		):
			stock_ledger_entry.StockLedgerEntry.validate_serial_batch_no_bundle(sle)

		throw.assert_called_once_with("未找到物料 ITEM-MISSING", stock_ledger_entry.frappe.ValidationError)
		sle.db_set.assert_not_called()

	def test_all_stock_item_validation_branches_translate_fixed_templates(self):
		cases = [
			(
				SimpleNamespace(has_batch_no=0, has_serial_no=0, is_stock_item=0, has_variants=0),
				None,
				"Item {0} must be a stock item",
				"物料 {0} 必须启用库存管理",
				"物料 ITEM-001 必须启用库存管理",
			),
			(
				SimpleNamespace(has_batch_no=1, has_serial_no=0, is_stock_item=1, has_variants=0),
				None,
				"Serial No / Batch No are mandatory for Item {0}",
				"物料 {0} 必须填写序列号或批号",
				"物料 ITEM-001 必须填写序列号或批号",
			),
			(
				SimpleNamespace(has_batch_no=0, has_serial_no=0, is_stock_item=1, has_variants=0),
				"BUNDLE-001",
				"Serial No and Batch No are not allowed for Item {0}",
				"物料 {0} 未启用序列号或批号管理，不能填写这些信息",
				"物料 ITEM-001 未启用序列号或批号管理，不能填写这些信息",
			),
		]

		for item, bundle, template, translation, expected in cases:
			with self.subTest(template=template):
				self._assert_validation(
					item=item,
					bundle=bundle,
					template=template,
					translation=translation,
					expected=expected,
					exception=stock_ledger_entry.frappe.ValidationError,
				)

	def test_source_does_not_translate_interpolated_stock_errors(self):
		text = Path(stock_ledger_entry.__file__).read_text()

		self.assertNotIn("throw_error_message(f", text)
		self.assertNotIn("frappe.throw(_(message)", text)

		tree = ast.parse(text)
		method = next(
			node
			for node in ast.walk(tree)
			if isinstance(node, ast.FunctionDef) and node.name == "validate_serial_batch_no_bundle"
		)
		calls = [
			node
			for node in ast.walk(method)
			if isinstance(node, ast.Call)
			and isinstance(node.func, ast.Attribute)
			and node.func.attr == "throw_error_message"
		]
		self.assertEqual(len(calls), 5)
		for call in calls:
			formatted = call.args[0]
			self.assertIsInstance(formatted, ast.Call)
			self.assertIsInstance(formatted.func, ast.Attribute)
			self.assertEqual(formatted.func.attr, "format")
			translated = formatted.func.value
			self.assertIsInstance(translated, ast.Call)
			self.assertIsInstance(translated.func, ast.Name)
			self.assertEqual(translated.func.id, "_")
			self.assertIsInstance(translated.args[0], ast.Constant)

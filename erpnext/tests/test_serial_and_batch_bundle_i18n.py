from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from erpnext.stock.doctype.serial_and_batch_bundle import serial_and_batch_bundle


class TestSerialAndBatchBundleI18n(TestCase):
	def test_negative_batch_message_translates_before_inserting_business_values(self):
		template = "Batch {0} for item {1} has negative stock of {2} in warehouse {3}."
		translation = "批号 {0} 对应物料 {1}，负库存数量为 {2}，所在仓库为 {3}。"
		bundle = SimpleNamespace(
			item_code="ITEM-001",
			warehouse="原材料仓",
			is_stock_reco_for_valuation_adjustment=lambda _qty: False,
		)

		with (
			patch.object(
				serial_and_batch_bundle,
				"_",
				side_effect=lambda message: translation if message == template else message,
			),
			patch.object(serial_and_batch_bundle, "bold", side_effect=lambda value: str(value)),
			patch.object(serial_and_batch_bundle.frappe, "throw") as throw,
		):
			serial_and_batch_bundle.SerialandBatchBundle.validate_negative_batch(
				bundle, "BATCH-001", -3
			)

		throw.assert_called_once_with(
			"批号 BATCH-001 对应物料 ITEM-001，负库存数量为 -3，所在仓库为 原材料仓。",
			serial_and_batch_bundle.BatchNegativeStockError,
		)

	def test_source_does_not_translate_interpolated_stock_errors(self):
		text = Path(serial_and_batch_bundle.__file__).read_text()

		self.assertNotIn("frappe.throw(_(msg)", text)
		self.assertNotIn("frappe.throw(_(message)", text)
		self.assertNotIn("throw_error_message(f", text)

from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from erpnext.stock import serial_batch_bundle


TYPE_TEMPLATE = (
	"The transaction type of Serial and Batch Bundle {0} is {1}, but based on Actual Qty {2} for "
	"Item {3} in {4} {5}, it should be {6}."
)
QTY_TEMPLATE = "Total Qty {0} of Serial and Batch Bundle {1} does not equal Actual Qty {2} in {3} {4}."
SERIES_TEMPLATE = "Set Serial No Series for Item {0}, or create the Serial and Batch Bundle manually."


TRANSLATIONS = {
	TYPE_TEMPLATE: "序列号与批号组合 {0} 的交易类型为{1}，但根据单据 {4} {5} 中物料 {3} 的实际数量 {2}，交易类型应为{6}。",
	QTY_TEMPLATE: "序列号与批号组合 {1} 的总数量 {0} 与单据 {3} {4} 中的实际数量 {2} 不一致。",
	SERIES_TEMPLATE: "请为物料 {0} 设置序列号模板，或手工创建序列号与批号组合。",
	"Inward": "入库",
	"Outward": "出库",
	"Stock Entry": "物料移动",
	"Incorrect Type of Transaction": "交易类型错误",
}


class TestSerialBatchBundleI18n(TestCase):
	def _translate(self, message):
		return TRANSLATIONS.get(message, message)

	def _bundle(self, actual_qty):
		return SimpleNamespace(
			sle=SimpleNamespace(
				actual_qty=actual_qty,
				item_code="ITEM-001",
				voucher_type="Stock Entry",
				voucher_no="MAT-STE-0001",
			)
		)

	def test_transaction_direction_error_translates_dynamic_labels(self):
		bundle = self._bundle(-2)
		document = SimpleNamespace(
			name="SABB-0001",
			type_of_transaction="Inward",
			total_qty=-2,
			precision=lambda fieldname: 2,
		)
		with (
			patch.object(serial_batch_bundle, "_", side_effect=self._translate),
			patch.object(serial_batch_bundle, "bold", side_effect=lambda value: f"<b>{value}</b>"),
			patch.object(serial_batch_bundle, "get_link_to_form", return_value='<a href="/app/serial-and-batch-bundle/SABB-0001">SABB-0001</a>'),
			patch.object(serial_batch_bundle.frappe, "throw", side_effect=RuntimeError) as throw,
			self.assertRaises(RuntimeError),
		):
			serial_batch_bundle.SerialBatchBundle.validate_actual_qty(bundle, document)

		throw.assert_called_once_with(
			'序列号与批号组合 <a href="/app/serial-and-batch-bundle/SABB-0001">SABB-0001</a> 的交易类型为<b>入库</b>，但根据单据 物料移动 MAT-STE-0001 中物料 <b>ITEM-001</b> 的实际数量 -2，交易类型应为<b>出库</b>。',
			title="交易类型错误",
		)

	def test_quantity_mismatch_translates_voucher_type(self):
		bundle = self._bundle(2)
		document = SimpleNamespace(
			name="SABB-0002",
			type_of_transaction="Inward",
			total_qty=1,
			precision=lambda fieldname: 2,
		)
		with (
			patch.object(serial_batch_bundle, "_", side_effect=self._translate),
			patch.object(serial_batch_bundle, "get_link_to_form", return_value="SABB-0002"),
			patch.object(serial_batch_bundle, "flt", side_effect=lambda value, precision=None: float(value)),
			patch.object(serial_batch_bundle.frappe, "throw", side_effect=RuntimeError) as throw,
			self.assertRaises(RuntimeError),
		):
			serial_batch_bundle.SerialBatchBundle.validate_actual_qty(bundle, document)

		throw.assert_called_once_with(
			"序列号与批号组合 SABB-0002 的总数量 1.0 与单据 物料移动 MAT-STE-0001 中的实际数量 2.0 不一致。"
		)

	def test_missing_serial_number_series_uses_fixed_translated_template(self):
		bundle = SimpleNamespace(serial_no_series=None, item_code="ITEM-001")
		with (
			patch.object(serial_batch_bundle, "_", side_effect=self._translate),
			patch.object(serial_batch_bundle.frappe, "throw", side_effect=RuntimeError) as throw,
			self.assertRaises(RuntimeError),
		):
			serial_batch_bundle.SerialBatchCreation.get_auto_created_serial_nos(bundle)

		throw.assert_called_once_with("请为物料 ITEM-001 设置序列号模板，或手工创建序列号与批号组合。")

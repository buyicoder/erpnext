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
OWNERSHIP_TEMPLATE = (
	"Serial and Batch Bundle {0} does not match one or more of: Item {1}, Warehouse {2}, and {3} {4}."
)
BUNDLE_NOT_SET_TEMPLATE = "Serial and Batch Bundle is not set for Item {0} in Warehouse {1}. {2}"


TRANSLATIONS = {
	TYPE_TEMPLATE: "序列号与批号组合 {0} 的交易类型为{1}，但根据单据 {4} {5} 中物料 {3} 的实际数量 {2}，交易类型应为{6}。",
	QTY_TEMPLATE: "序列号与批号组合 {1} 的总数量 {0} 与单据 {3} {4} 中的实际数量 {2} 不一致。",
	SERIES_TEMPLATE: "请为物料 {0} 设置序列号模板，或手工创建序列号与批号组合。",
	OWNERSHIP_TEMPLATE: "序列号与批号组合 {0} 与以下一项或多项不匹配：物料 {1}、仓库 {2}、单据 {3} {4}。",
	BUNDLE_NOT_SET_TEMPLATE: "物料 {0} 在仓库 {1} 中未设置序列号与批号组合。{2}",
	"This Item does not use batch or serial numbers.": "此物料未启用批号或序列号管理。",
	"To select serial numbers automatically, set Serial No Series for this Item.": "如需自动选择序列号，请为此物料设置序列号模板。",
	"To select batches automatically, set Batch Number Series for this Item.": "如需自动选择批号，请为此物料设置批号模板。",
	"To select serial numbers or batches automatically for outbound stock, enable {0} in {1}.": "如需在出库时自动选择序列号或批号，请在{1}中启用“{0}”。",
	"Auto create Serial and Batch Bundle for outward": "出库时自动创建序列号与批号",
	"Stock Settings": "库存设置",
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

	def _assert_item_error(self, actual_qty, item_details, setting_values, expected):
		bundle = SimpleNamespace(
			sle=SimpleNamespace(actual_qty=actual_qty),
			item_details=SimpleNamespace(**item_details),
			item_code="ITEM-003",
			warehouse="Stores - TC",
		)
		with (
			patch.object(serial_batch_bundle, "_", side_effect=self._translate),
			patch.object(
				serial_batch_bundle.frappe,
				"get_single_value",
				side_effect=lambda doctype, fieldname: setting_values.get(fieldname),
			),
			patch.object(serial_batch_bundle.frappe, "throw", side_effect=RuntimeError) as throw,
			self.assertRaises(RuntimeError),
		):
			serial_batch_bundle.SerialBatchBundle.validate_item(bundle)

		throw.assert_called_once_with(expected)

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

	def test_bundle_ownership_error_translates_voucher_type(self):
		bundle = SimpleNamespace(
			sle=SimpleNamespace(
				serial_and_batch_bundle="SABB-0003",
				voucher_type="Stock Entry",
				voucher_no="MAT-STE-0002",
			),
			item_code="ITEM-002",
			warehouse="Stores - TC",
		)
		with (
			patch.object(
				serial_batch_bundle.frappe,
				"db",
				SimpleNamespace(exists=lambda *args, **kwargs: False),
			),
			patch.object(serial_batch_bundle, "_", side_effect=self._translate),
			patch.object(serial_batch_bundle, "bold", side_effect=lambda value: f"<b>{value}</b>"),
			patch.object(serial_batch_bundle.frappe, "throw", side_effect=RuntimeError) as throw,
			self.assertRaises(RuntimeError),
		):
			serial_batch_bundle.SerialBatchBundle.validate_item_and_warehouse(bundle)

		throw.assert_called_once_with(
			"序列号与批号组合 <b>SABB-0003</b> 与以下一项或多项不匹配：物料 <b>ITEM-002</b>、仓库 <b>Stores - TC</b>、单据 物料移动 <b>MAT-STE-0002</b>。"
		)

	def test_non_serialized_item_reason_is_translated(self):
		self._assert_item_error(
			1,
			{
				"has_batch_no": 0,
				"has_serial_no": 0,
				"serial_no_series": None,
				"batch_number_series": None,
			},
			{},
			"物料 ITEM-003 在仓库 Stores - TC 中未设置序列号与批号组合。此物料未启用批号或序列号管理。",
		)

	def test_missing_serial_and_batch_series_reasons_are_translated(self):
		self._assert_item_error(
			1,
			{
				"has_batch_no": 1,
				"has_serial_no": 1,
				"serial_no_series": None,
				"batch_number_series": None,
			},
			{"naming_series_prefix": None},
			"物料 ITEM-003 在仓库 Stores - TC 中未设置序列号与批号组合。如需自动选择序列号，请为此物料设置序列号模板。 如需自动选择批号，请为此物料设置批号模板。",
		)

	def test_outbound_auto_create_guidance_is_translated(self):
		self._assert_item_error(
			-1,
			{
				"has_batch_no": 1,
				"has_serial_no": 0,
				"serial_no_series": None,
				"batch_number_series": "BATCH-.#####",
			},
			{"auto_create_serial_and_batch_bundle_for_outward": 0},
			"物料 ITEM-003 在仓库 Stores - TC 中未设置序列号与批号组合。如需在出库时自动选择序列号或批号，请在库存设置中启用“出库时自动创建序列号与批号”。",
		)

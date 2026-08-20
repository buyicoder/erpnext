from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from erpnext.subcontracting.doctype.subcontracting_order import subcontracting_order


class TestSubcontractingOrderI18n(TestCase):
	def _assert_purchase_order_error(self, purchase_order, expected):
		order = SimpleNamespace(purchase_order=purchase_order.name)
		translations = {
			"Please submit Purchase Order {0} before proceeding.": "请先提交采购订单 {0}，再继续操作。",
			"Cannot create more Subcontracting Orders against the Purchase Order {0}.": "无法再基于采购订单 {0} 创建委外订单。",
		}

		with (
			patch.object(subcontracting_order.frappe, "get_doc", return_value=purchase_order),
			patch.object(
				subcontracting_order,
				"_",
				side_effect=lambda message: translations.get(message, message),
			),
			patch.object(subcontracting_order.frappe, "throw", side_effect=RuntimeError) as throw,
			self.assertRaises(RuntimeError),
		):
			subcontracting_order.SubcontractingOrder.validate_purchase_order_for_subcontracting(order)

		throw.assert_called_once_with(expected)

	def test_unsubmitted_purchase_order_uses_fixed_translated_template(self):
		self._assert_purchase_order_error(
			SimpleNamespace(
				name="PUR-ORD-0001",
				is_subcontracted=1,
				is_old_subcontracting_flow=0,
				docstatus=0,
				per_received=0,
			),
			"请先提交采购订单 PUR-ORD-0001，再继续操作。",
		)

	def test_fully_received_purchase_order_uses_fixed_translated_template(self):
		self._assert_purchase_order_error(
			SimpleNamespace(
				name="PUR-ORD-0002",
				is_subcontracted=1,
				is_old_subcontracting_flow=0,
				docstatus=1,
				per_received=100,
			),
			"无法再基于采购订单 PUR-ORD-0002 创建委外订单。",
		)

	def test_supplied_item_warehouse_error_uses_fixed_translated_template(self):
		order = SimpleNamespace(
			supplier_warehouse="Supplier - TC",
			supplied_items=[
				SimpleNamespace(
					reserve_warehouse="Supplier - TC",
					main_item_code="FG-ITEM-001",
				)
			],
		)
		template = "Reserve Warehouse must be different from Supplier Warehouse for Supplied Item {0}."

		with (
			patch.object(
				subcontracting_order,
				"_",
				side_effect=lambda message: (
					"委外原材料 {0} 的预留仓库必须与委外仓不同。" if message == template else message
				),
			),
			patch.object(subcontracting_order.frappe, "throw", side_effect=RuntimeError) as throw,
			self.assertRaises(RuntimeError),
		):
			subcontracting_order.SubcontractingOrder.validate_supplied_items(order)

		throw.assert_called_once_with("委外原材料 FG-ITEM-001 的预留仓库必须与委外仓不同。")

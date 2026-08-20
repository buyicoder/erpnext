from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from erpnext.controllers import selling_controller


class TestSellingControllerI18n(TestCase):
	def test_non_internal_customer_warning_uses_stock_transfer_terminology(self):
		item = SimpleNamespace(
			idx=1,
			get=lambda fieldname: {
				"target_warehouse": "客户寄售仓",
				"warehouse": "成品仓",
			}.get(fieldname),
		)
		values = {
			"items": [item],
			"packed_items": [],
			"is_internal_customer": 0,
		}
		translations = {
			("Target Warehouse is set for some items but the customer is not an internal customer.", None): "部分物料设置了目标仓库，但客户不是内部客户。",
			("This {0} will be treated as a material transfer.", None): "此{0}将按物料调拨处理。",
			("Sales Order", None): "销售订单",
			("Delivery Note", None): "销售出库",
			("Sales Invoice", None): "销售发票",
			("Internal Transfer", "Stock Transfer"): "内部调拨",
		}
		doctypes = {
			"Sales Order": "销售订单",
			"Delivery Note": "销售出库",
			"Sales Invoice": "销售发票",
		}

		def translate(message, context=None):
			return translations.get((message, context), message)

		with (
			patch.object(selling_controller, "_", side_effect=translate),
			patch.object(selling_controller.frappe, "msgprint") as msgprint,
		):
			for doctype, translated_doctype in doctypes.items():
				with self.subTest(doctype=doctype):
					document = SimpleNamespace(
						doctype=doctype,
						get=lambda fieldname: values.get(fieldname),
					)
					selling_controller.SellingController.validate_target_warehouse(document)
					msgprint.assert_called_once_with(
						"部分物料设置了目标仓库，但客户不是内部客户。 "
						f"此{translated_doctype}将按物料调拨处理。",
						title="内部调拨",
						alert=True,
					)
					msgprint.reset_mock()

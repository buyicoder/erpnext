from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from erpnext.controllers import buying_controller


class TestBuyingControllerI18n(TestCase):
	def test_asset_creation_message_uses_translated_success_title(self):
		controller = object.__new__(buying_controller.BuyingController)
		controller.items = [
			SimpleNamespace(is_fixed_asset=True, item_code="ITEM-001", idx=1),
		]
		translations = {
			"Assets not created for {item_code}. You will have to create asset manually.": "未自动创建物料 {item_code} 的资产，请手动创建。",
			"Success": "成功",
		}

		with (
			patch.object(
				buying_controller,
				"get_asset_item_details",
				return_value={"ITEM-001": {"auto_create_assets": False}},
			),
			patch.object(buying_controller, "get_dimensions", return_value=[]),
			patch.object(
				buying_controller, "_", side_effect=lambda message: translations.get(message, message)
			),
			patch.object(buying_controller.frappe, "bold", side_effect=lambda value: f"<b>{value}</b>"),
			patch.object(buying_controller.frappe, "msgprint") as msgprint,
		):
			controller.auto_make_assets(["ITEM-001"])

		msgprint.assert_called_once_with(
			"未自动创建物料 <b>ITEM-001</b> 的资产，请手动创建。",
			title="成功",
			indicator="green",
			alert=True,
		)

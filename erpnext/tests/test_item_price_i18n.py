from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from erpnext.stock.doctype.item_price import item_price


TRANSLATIONS = {
	"Price List {0} does not exist or is disabled.": "价格表 {0} 不存在或已停用。",
	"Item Price cannot be created for template Item {0}.": "不能为模板物料 {0} 创建物料价格。",
}


class TestItemPriceI18n(TestCase):
	def _translate(self, message):
		return TRANSLATIONS.get(message, message)

	def test_missing_or_disabled_price_list_uses_fixed_translated_template(self):
		price = SimpleNamespace(price_list="标准销售价")
		with (
			patch.object(
				item_price.frappe,
				"db",
				SimpleNamespace(get_value=lambda *args, **kwargs: None),
			),
			patch.object(
				item_price.frappe.utils,
				"get_link_to_form",
				return_value='<a href="/app/price-list/标准销售价">标准销售价</a>',
			),
			patch.object(item_price, "_", side_effect=self._translate),
			patch.object(item_price.frappe, "throw", side_effect=RuntimeError) as throw,
			self.assertRaises(RuntimeError),
		):
			item_price.ItemPrice.update_price_list_details(price)

		throw.assert_called_once_with(
			'价格表 <a href="/app/price-list/标准销售价">标准销售价</a> 不存在或已停用。'
		)

	def test_template_item_error_uses_fixed_translated_template(self):
		price = SimpleNamespace(item_code="ITEM-TEMPLATE-001")
		with (
			patch.object(item_price.frappe, "get_cached_value", return_value=1),
			patch.object(item_price, "_", side_effect=self._translate),
			patch.object(item_price, "bold", side_effect=lambda value: f"<b>{value}</b>"),
			patch.object(item_price.frappe, "throw", side_effect=RuntimeError) as throw,
			self.assertRaises(RuntimeError),
		):
			item_price.ItemPrice.validate_item_template(price)

		throw.assert_called_once_with("不能为模板物料 <b>ITEM-TEMPLATE-001</b> 创建物料价格。")

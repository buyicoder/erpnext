from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from erpnext.assets.doctype.asset import asset


class TestAssetPurchaseDocI18n(TestCase):
	def test_missing_item_uses_translated_document_type_and_fixed_template(self):
		template = "Selected {0} does not contain the Item Code {1}"
		translations = {
			template: "所选{0}中不包含物料号 {1}",
			"Purchase Receipt": "采购入库",
		}
		purchase_doc = SimpleNamespace(items=[])

		with (
			patch.object(asset.frappe, "get_doc", return_value=purchase_doc),
			patch.object(asset, "_", side_effect=lambda message: translations.get(message, message)),
			patch.object(asset.frappe, "throw", side_effect=RuntimeError) as throw,
			self.assertRaises(RuntimeError),
		):
			asset.get_values_from_purchase_doc("MAT-PRE-0001", "ITEM-404", "Purchase Receipt")

		throw.assert_called_once_with("所选采购入库中不包含物料号 ITEM-404")

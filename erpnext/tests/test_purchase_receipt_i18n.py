from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from erpnext.stock.doctype.purchase_receipt import purchase_receipt


REFERENCE_TEMPLATE = (
	"Row #{0}: Select a valid Quality Inspection with Reference Type {1} and Reference Name {2}."
)
ITEM_TEMPLATE = "Row #{0}: Select a valid Quality Inspection with Item Code {1}."


TRANSLATIONS = {
	REFERENCE_TEMPLATE: "第 {0} 行：请选择关联类型为 {1}、源单据为 {2} 的有效质量检验单。",
	ITEM_TEMPLATE: "第 {0} 行：请选择物料号为 {1} 的有效质量检验单。",
	"Purchase Receipt": "采购入库",
}


class TestPurchaseReceiptI18n(TestCase):
	def _translate(self, message):
		return TRANSLATIONS.get(message, message)

	def _receipt(self):
		item = SimpleNamespace(idx=2, quality_inspection="QI-0001", item_code="ITEM-001")
		return SimpleNamespace(
			doctype="Purchase Receipt",
			name="MAT-PRE-0001",
			get=lambda fieldname: [item] if fieldname == "items" else None,
		)

	def test_invalid_quality_inspection_reference_translates_doctype(self):
		receipt = self._receipt()
		inspection = SimpleNamespace(
			reference_type="Purchase Receipt",
			reference_name="MAT-PRE-OTHER",
			item_code="ITEM-001",
		)
		with (
			patch.object(
				purchase_receipt.frappe,
				"db",
				SimpleNamespace(get_value=lambda *args, **kwargs: inspection),
			),
			patch.object(purchase_receipt, "_", side_effect=self._translate),
			patch.object(purchase_receipt.frappe, "bold", side_effect=lambda value: f"<b>{value}</b>"),
			patch.object(purchase_receipt.frappe, "throw", side_effect=RuntimeError) as throw,
			self.assertRaises(RuntimeError),
		):
			purchase_receipt.PurchaseReceipt.validate_items_quality_inspection(receipt)

		throw.assert_called_once_with(
			"第 2 行：请选择关联类型为 <b>采购入库</b>、源单据为 <b>MAT-PRE-0001</b> 的有效质量检验单。"
		)

	def test_invalid_quality_inspection_item_uses_fixed_translated_template(self):
		receipt = self._receipt()
		inspection = SimpleNamespace(
			reference_type="Purchase Receipt",
			reference_name="MAT-PRE-0001",
			item_code="ITEM-OTHER",
		)
		with (
			patch.object(
				purchase_receipt.frappe,
				"db",
				SimpleNamespace(get_value=lambda *args, **kwargs: inspection),
			),
			patch.object(purchase_receipt, "_", side_effect=self._translate),
			patch.object(purchase_receipt.frappe, "bold", side_effect=lambda value: f"<b>{value}</b>"),
			patch.object(purchase_receipt.frappe, "throw", side_effect=RuntimeError) as throw,
			self.assertRaises(RuntimeError),
		):
			purchase_receipt.PurchaseReceipt.validate_items_quality_inspection(receipt)

		throw.assert_called_once_with("第 2 行：请选择物料号为 <b>ITEM-001</b> 的有效质量检验单。")

from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from erpnext.stock.doctype.inventory_dimension import inventory_dimension


TRANSLATIONS = {
	"The user cannot change the value of field {0} because stock transactions exist against dimension {1}.": "该库存辅助核算已有库存交易，不能修改字段 {0}（库存辅助核算：{1}）。",
	"Deleted custom fields related to dimension {0}": "已删除与库存辅助核算 {0} 相关的自定义字段",
	"Reference document {0} cannot be a child table.": "引用单据 {0} 不能是子表。",
	"Reference document {0} cannot be used as an Inventory Dimension.": "引用单据 {0} 不能用作库存辅助核算。",
	"Sales Invoice Item": "销售发票明细",
	"Warehouse": "仓库",
}


class TestInventoryDimensionI18n(TestCase):
	def _translate(self, message):
		return TRANSLATIONS.get(message, message)

	def test_delete_custom_fields_uses_fixed_translated_template(self):
		dimension = SimpleNamespace(
			name="品牌",
			source_fieldname="brand",
			document_type=None,
		)
		with (
			patch.object(inventory_dimension.frappe, "get_all", return_value=[]),
			patch.object(inventory_dimension, "_", side_effect=self._translate),
			patch.object(inventory_dimension.frappe, "msgprint") as msgprint,
		):
			inventory_dimension.InventoryDimension.delete_custom_fields(dimension)

		msgprint.assert_called_once_with("已删除与库存辅助核算 品牌 相关的自定义字段")

	def test_existing_stock_blocks_field_change_with_translated_label(self):
		old_doc = {"dimension_name": "旧品牌"}
		dimension = SimpleNamespace(
			name="品牌维度",
			_doc_before_save=old_doc,
			is_new=lambda: False,
			has_stock_ledger=lambda: True,
			get=lambda fieldname: {"dimension_name": "新品牌"}.get(fieldname),
		)
		field = SimpleNamespace(fieldname="dimension_name", label="Dimension Name")
		translations = {
			**TRANSLATIONS,
			"Dimension Name": "辅助核算名称",
		}
		with (
			patch.object(inventory_dimension.frappe, "get_meta", return_value=SimpleNamespace(fields=[field])),
			patch.object(inventory_dimension, "_", side_effect=lambda message: translations.get(message, message)),
			patch.object(inventory_dimension, "bold", side_effect=lambda value: f"<b>{value}</b>"),
			patch.object(inventory_dimension.frappe, "throw", side_effect=RuntimeError) as throw,
			self.assertRaises(RuntimeError),
		):
			inventory_dimension.InventoryDimension.do_not_update_document(dimension)

		throw.assert_called_once_with(
			"该库存辅助核算已有库存交易，不能修改字段 <b>辅助核算名称</b>（库存辅助核算：<b>品牌维度</b>）。",
			inventory_dimension.DoNotChangeError,
		)

	def test_child_table_error_translates_template_and_doctype(self):
		dimension = SimpleNamespace(reference_document="Sales Invoice Item")
		with (
			patch.object(inventory_dimension.frappe, "get_cached_value", return_value=1),
			patch.object(inventory_dimension, "_", side_effect=self._translate),
			patch.object(inventory_dimension.frappe, "throw", side_effect=RuntimeError) as throw,
			self.assertRaises(RuntimeError),
		):
			inventory_dimension.InventoryDimension.validate_reference_document(dimension)

		throw.assert_called_once_with("引用单据 销售发票明细 不能是子表。", inventory_dimension.CanNotBeChildDoc)

	def test_default_dimension_error_translates_template_and_doctype(self):
		dimension = SimpleNamespace(reference_document="Warehouse")
		with (
			patch.object(inventory_dimension.frappe, "get_cached_value", return_value=0),
			patch.object(inventory_dimension, "_", side_effect=self._translate),
			patch.object(inventory_dimension.frappe, "throw", side_effect=RuntimeError) as throw,
			self.assertRaises(RuntimeError),
		):
			inventory_dimension.InventoryDimension.validate_reference_document(dimension)

		throw.assert_called_once_with("引用单据 仓库 不能用作库存辅助核算。", inventory_dimension.CanNotBeDefaultDimension)

import json
from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock, patch

from erpnext.setup import china_defaults
from erpnext.setup.china_defaults import (
	CHINA_ADDRESS_TEMPLATE,
	CHINA_LETTER_HEAD_TRANSLATIONS,
	CHINA_PRINT_FORMAT_TRANSLATIONS,
	CHINA_SYSTEM_DEFAULTS,
)


class TestChinaDefaults(TestCase):
	def test_bundled_demo_data_uses_chinese_business_names(self):
		demo_root = Path(__file__).parents[1] / "setup" / "demo_data"
		payload = "\n".join(path.read_text() for path in demo_root.glob("*.json"))
		old_names = {
			old_name
			for names in china_defaults.CHINA_DEMO_RECORD_NAMES.values()
			for old_name in names
		}
		for old_name in old_names:
			self.assertNotIn(old_name, payload)

		items = json.loads((demo_root / "item.json").read_text())
		customers = json.loads((demo_root / "customer.json").read_text())
		suppliers = json.loads((demo_root / "supplier.json").read_text())
		item_groups = json.loads((demo_root / "item_group.json").read_text())
		customer_groups = json.loads((demo_root / "customer_group.json").read_text())
		supplier_groups = json.loads((demo_root / "supplier_group.json").read_text())
		sales_orders = json.loads((demo_root / "sales_order.json").read_text())
		purchase_orders = json.loads((demo_root / "purchase_order.json").read_text())

		self.assertEqual(
			[item["item_name"] for item in items],
			[name[1] for name in china_defaults.CHINA_DEMO_ITEM_NAMES.values()],
		)
		self.assertEqual(
			{customer["customer_name"] for customer in customers},
			set(china_defaults.CHINA_DEMO_RECORD_NAMES["Customer"].values()),
		)
		self.assertEqual(
			{supplier["supplier_name"] for supplier in suppliers},
			set(china_defaults.CHINA_DEMO_RECORD_NAMES["Supplier"].values()),
		)
		self.assertEqual(
			{group["item_group_name"] for group in item_groups},
			set(china_defaults.CHINA_DEMO_RECORD_NAMES["Item Group"].values()),
		)
		self.assertEqual(
			{group["customer_group_name"] for group in customer_groups},
			set(china_defaults.CHINA_DEMO_RECORD_NAMES["Customer Group"].values()),
		)
		self.assertEqual(
			{group["supplier_group_name"] for group in supplier_groups},
			set(china_defaults.CHINA_DEMO_RECORD_NAMES["Supplier Group"].values()),
		)

		item_codes = {item["item_code"] for item in items}
		customer_names = {customer["customer_name"] for customer in customers}
		supplier_names = {supplier["supplier_name"] for supplier in suppliers}
		self.assertTrue(
			all(item["item_group"] in {group["item_group_name"] for group in item_groups} for item in items)
		)
		self.assertTrue(
			all(
				customer["customer_group"]
				in {group["customer_group_name"] for group in customer_groups}
				for customer in customers
			)
		)
		self.assertTrue(
			all(
				supplier["supplier_group"]
				in {group["supplier_group_name"] for group in supplier_groups}
				for supplier in suppliers
			)
		)
		self.assertTrue(all(order["customer"] in customer_names for order in sales_orders))
		self.assertTrue(all(order["supplier"] in supplier_names for order in purchase_orders))
		self.assertTrue(
			all(row["item_code"] in item_codes for order in sales_orders for row in order["items"])
		)
		self.assertTrue(
			all(row["item_code"] in item_codes for order in purchase_orders for row in order["items"])
		)

	def test_china_business_display_defaults(self):
		self.assertEqual(CHINA_SYSTEM_DEFAULTS["language"], "zh")
		self.assertEqual(CHINA_SYSTEM_DEFAULTS["currency"], "CNY")
		self.assertEqual(CHINA_SYSTEM_DEFAULTS["time_zone"], "Asia/Shanghai")
		self.assertEqual(CHINA_SYSTEM_DEFAULTS["date_format"], "yyyy-mm-dd")
		self.assertEqual(CHINA_SYSTEM_DEFAULTS["time_format"], "HH:mm:ss")
		self.assertEqual(CHINA_SYSTEM_DEFAULTS["currency_precision"], "2")
		self.assertEqual(CHINA_SYSTEM_DEFAULTS["first_day_of_the_week"], "Monday")
		self.assertEqual(CHINA_SYSTEM_DEFAULTS["rounding_method"], "Commercial Rounding")

	def test_china_localization_status_reports_actual_values_and_customizations(self):
		system_settings = MagicMock(**CHINA_SYSTEM_DEFAULTS)
		global_defaults = MagicMock(country="China", default_currency="CNY")
		with patch.object(
			china_defaults.frappe,
			"get_single",
			side_effect=[system_settings, global_defaults],
		):
			status = china_defaults.get_china_localization_status()

		self.assertTrue(status["matches_china_defaults"])
		self.assertEqual(status["actual"]["System Settings"], CHINA_SYSTEM_DEFAULTS)
		self.assertEqual(status["customized"], {})

		system_settings.time_zone = "Asia/Urumqi"
		with patch.object(
			china_defaults.frappe,
			"get_single",
			side_effect=[system_settings, global_defaults],
		):
			status = china_defaults.get_china_localization_status()

		self.assertFalse(status["matches_china_defaults"])
		self.assertEqual(
			status["customized"]["System Settings"]["time_zone"],
			{"expected": "Asia/Shanghai", "actual": "Asia/Urumqi"},
		)

	def test_china_address_template_uses_domestic_order_and_labels(self):
		self.assertLess(CHINA_ADDRESS_TEMPLATE.index("{{ state }}"), CHINA_ADDRESS_TEMPLATE.index("{{ city }}"))
		self.assertLess(CHINA_ADDRESS_TEMPLATE.index("{{ city }}"), CHINA_ADDRESS_TEMPLATE.index("{{ county }}"))
		self.assertLess(CHINA_ADDRESS_TEMPLATE.index("{{ county }}"), CHINA_ADDRESS_TEMPLATE.index("{{ address_line1 }}"))
		self.assertIn("邮编：{{ pincode }}", CHINA_ADDRESS_TEMPLATE)
		self.assertIn("电话：{{ phone }}", CHINA_ADDRESS_TEMPLATE)
		self.assertNotIn("Phone", CHINA_ADDRESS_TEMPLATE)

	def test_custom_address_template_is_not_overwritten(self):
		custom_template = MagicMock(template="用户自定义模板")
		fake_db = MagicMock()
		fake_db.exists.return_value = True
		with (
			patch.object(china_defaults.frappe, "db", fake_db),
			patch.object(china_defaults.frappe, "get_doc", return_value=custom_template),
		):
			self.assertFalse(china_defaults.ensure_china_address_template())

		custom_template.save.assert_not_called()

	def test_existing_site_preferences_are_preserved_unless_forced(self):
		system_settings = MagicMock(
			language="zh",
			time_zone="Asia/Urumqi",
			date_format="dd/mm/yyyy",
			currency_precision="4",
		)
		global_defaults = MagicMock(country="China", default_currency="CNY")
		with (
			patch.object(
				china_defaults.frappe,
				"get_single",
				side_effect=[system_settings, global_defaults],
			),
			patch.object(china_defaults, "ensure_china_address_template"),
			patch.object(china_defaults, "ensure_china_print_format_labels"),
			patch.object(china_defaults, "ensure_china_letter_head_labels"),
			patch.object(china_defaults.frappe, "clear_cache"),
		):
			china_defaults.apply_china_defaults()

		system_settings.update.assert_not_called()
		system_settings.save.assert_not_called()
		global_defaults.update.assert_not_called()
		global_defaults.save.assert_not_called()

	def test_setup_can_force_china_defaults(self):
		system_settings = MagicMock(time_zone="Asia/Urumqi")
		global_defaults = MagicMock(country="Singapore", default_currency="SGD")
		with (
			patch.object(
				china_defaults.frappe,
				"get_single",
				side_effect=[system_settings, global_defaults],
			),
			patch.object(china_defaults, "ensure_china_address_template"),
			patch.object(china_defaults, "ensure_china_print_format_labels"),
			patch.object(china_defaults, "ensure_china_letter_head_labels"),
			patch.object(china_defaults.frappe, "clear_cache"),
		):
			china_defaults.apply_china_defaults(force=True)

		system_settings.update.assert_called_once_with(CHINA_SYSTEM_DEFAULTS)
		global_defaults.update.assert_called_once_with({"country": "China", "default_currency": "CNY"})

	def test_current_managed_address_template_is_a_noop(self):
		template = MagicMock(template=CHINA_ADDRESS_TEMPLATE, is_default=1)
		fake_db = MagicMock()
		fake_db.exists.return_value = True
		with (
			patch.object(china_defaults.frappe, "db", fake_db),
			patch.object(china_defaults.frappe, "get_doc", return_value=template),
		):
			self.assertFalse(china_defaults.ensure_china_address_template())

		template.save.assert_not_called()

	def test_print_format_labels_cover_core_transaction_formats(self):
		self.assertEqual(
			CHINA_PRINT_FORMAT_TRANSLATIONS["Sales Invoice with Item Image"],
			"销售发票（含物料图片）",
		)
		self.assertEqual(
			CHINA_PRINT_FORMAT_TRANSLATIONS["Purchase Order Standard"],
			"采购订单（标准）",
		)
		self.assertEqual(len(CHINA_PRINT_FORMAT_TRANSLATIONS), 15)
		self.assertEqual(CHINA_LETTER_HEAD_TRANSLATIONS["Company Letterhead - Grey"], "公司抬头（灰色）")

	def test_custom_print_format_translation_is_preserved(self):
		record = MagicMock(
			source_text="Sales Invoice with Item Image",
			translated_text="用户自定义名称",
			context=None,
		)
		fake_meta = MagicMock(translated_doctype=1)
		with (
			patch.object(
				china_defaults,
				"CHINA_PRINT_FORMAT_TRANSLATIONS",
				{"Sales Invoice with Item Image": "销售发票（含物料图片）"},
			),
			patch.object(china_defaults.frappe, "get_meta", return_value=fake_meta),
			patch.object(china_defaults.frappe, "db", MagicMock(get_value=MagicMock(return_value=None))),
			patch.object(china_defaults.frappe, "get_all", return_value=[record]),
			patch.object(china_defaults.frappe, "get_doc") as get_doc,
			patch.object(china_defaults.frappe, "new_doc") as new_doc,
		):
			self.assertFalse(china_defaults.ensure_china_print_format_labels())

		get_doc.assert_not_called()
		new_doc.assert_not_called()

	def test_force_preserves_custom_print_format_translation(self):
		record = MagicMock(
			source_text="Sales Invoice with Item Image",
			translated_text="用户自定义名称",
			context=None,
		)
		with (
			patch.object(
				china_defaults,
				"CHINA_PRINT_FORMAT_TRANSLATIONS",
				{"Sales Invoice with Item Image": "销售发票（含物料图片）"},
			),
			patch.object(china_defaults.frappe, "db", MagicMock(get_value=MagicMock(return_value=None))),
			patch.object(china_defaults.frappe, "get_meta", return_value=MagicMock(translated_doctype=1)),
			patch.object(china_defaults.frappe, "get_all", return_value=[record]),
			patch.object(china_defaults.frappe, "get_doc") as get_doc,
		):
			self.assertFalse(china_defaults.ensure_china_print_format_labels(force=True))

		get_doc.assert_not_called()

	def test_explicitly_disabled_print_format_translation_is_preserved(self):
		with (
			patch.object(china_defaults.frappe, "db", MagicMock(get_value=MagicMock(return_value="0"))),
			patch.object(china_defaults.frappe, "get_meta", return_value=MagicMock(translated_doctype=0)),
			patch.object(china_defaults.frappe, "get_all", return_value=[]),
			patch.object(china_defaults.frappe, "make_property_setter") as make_property_setter,
			patch.object(china_defaults.frappe, "new_doc") as new_doc,
		):
			new_doc.return_value = MagicMock()
			china_defaults.ensure_china_print_format_labels()

		make_property_setter.assert_not_called()

	def test_deferred_cache_clear_for_batched_deployment(self):
		with (
			patch.object(china_defaults.frappe, "get_single", side_effect=[MagicMock(), MagicMock()]),
			patch.object(china_defaults, "ensure_china_address_template", return_value=True),
			patch.object(china_defaults, "ensure_china_print_format_labels", return_value=True),
			patch.object(china_defaults, "ensure_china_letter_head_labels", return_value=True),
			patch.object(china_defaults.frappe, "clear_cache") as clear_cache,
		):
			china_defaults.apply_china_defaults(clear_cache=False)

		clear_cache.assert_not_called()

	def test_only_exact_bundled_demo_records_are_localized(self):
		existing = {
			("Item Group", "Demo Item Group"),
			("Customer", "Grant Plastics Ltd."),
		}
		fake_db = MagicMock()
		fake_db.get_single_value.return_value = "占永杰企业数字化服务 (Demo)"
		fake_db.exists.side_effect = lambda doctype, name: (doctype, name) in existing
		def get_value(doctype, name, field, as_dict=False):
			if doctype == "Customer":
				return "演示客户组"
			if as_dict and name == "SKU001":
				return MagicMock(item_name="T-shirt", item_group="演示物料组")
			if as_dict and name == "SKU002":
				return MagicMock(item_name="用户自定义名称", item_group="演示物料组")
			return None

		fake_db.get_value.side_effect = get_value

		with (
			patch.object(china_defaults.frappe, "db", fake_db),
			patch.object(china_defaults.frappe, "get_all", return_value=[]),
			patch.object(china_defaults.frappe, "rename_doc") as rename_doc,
			patch.object(china_defaults, "rebuild_for_doctype") as rebuild_for_doctype,
		):
			self.assertTrue(china_defaults.localize_bundled_demo_data())

		rename_doc.assert_any_call(
			"Item Group",
			"Demo Item Group",
			"演示物料组",
			show_alert=False,
		)
		rename_doc.assert_any_call(
			"Customer",
			"Grant Plastics Ltd.",
			"格兰特塑料有限公司",
			show_alert=False,
		)
		fake_db.set_value.assert_called_once_with(
			"Item", "SKU001", "item_name", "T恤", update_modified=False
		)
		rebuild_for_doctype.assert_called_once_with("Item")

	def test_non_demo_site_never_renames_matching_business_data(self):
		fake_db = MagicMock()
		fake_db.get_single_value.return_value = None
		with (
			patch.object(china_defaults.frappe, "db", fake_db),
			patch.object(china_defaults.frappe, "rename_doc") as rename_doc,
		):
			self.assertFalse(china_defaults.localize_bundled_demo_data())

		fake_db.exists.assert_not_called()
		fake_db.set_value.assert_not_called()
		rename_doc.assert_not_called()

	def test_demo_migration_refreshes_cached_party_and_item_names(self):
		fake_db = MagicMock()
		fake_db.get_single_value.return_value = "占永杰企业数字化服务 (Demo)"
		fake_db.exists.return_value = False
		cached_records = {
			"Sales Order": {
				"SAL-ORD-2026-00001": {
					"customer": "格兰特塑料有限公司",
					"customer_name": "Grant Plastics Ltd.",
				}
			},
			"Sales Invoice": {
				"ACC-SINV-2026-00001": {
					"customer": "格兰特塑料有限公司",
					"customer_name": "Grant Plastics Ltd.",
				}
			},
			"Purchase Order": {
				"PUR-ORD-2026-00001": {
					"supplier": "MA实业有限公司",
					"supplier_name": "MA Inc.",
				}
			},
			"Purchase Invoice": {
				"ACC-PINV-2026-00001": {
					"supplier": "MA实业有限公司",
					"supplier_name": "MA Inc.",
				}
			},
			"Payment Entry": {
				"ACC-PAY-2026-00001": {
					"party_type": "Customer",
					"party": "格兰特塑料有限公司",
					"party_name": "Grant Plastics Ltd.",
				},
				"ACC-PAY-2026-00002": {
					"party_type": "Supplier",
					"party": "MA实业有限公司",
					"party_name": "MA Inc.",
				},
			},
			"Sales Order Item": {"soi-1": {"item_code": "SKU001", "item_name": "T-shirt"}},
			"Sales Invoice Item": {"sii-1": {"item_code": "SKU001", "item_name": "T-shirt"}},
			"Purchase Order Item": {"poi-1": {"item_code": "SKU001", "item_name": "T-shirt"}},
			"Purchase Invoice Item": {"pii-1": {"item_code": "SKU001", "item_name": "T-shirt"}},
		}

		def get_all(doctype, filters, fields, limit_page_length):
			self.assertIn("name", fields)
			self.assertEqual(limit_page_length, 500)
			return [
				china_defaults.frappe._dict(name=name, **values)
				for name, values in cached_records.get(doctype, {}).items()
				if all(
					values.get(field) in value[1] if isinstance(value, list) else values.get(field) == value
					for field, value in filters.items()
				)
			]

		def bulk_update(doctype, doc_updates, **kwargs):
			self.assertFalse(kwargs["update_modified"])
			for name, updates in doc_updates.items():
				cached_records[doctype][name].update(updates)

		fake_db.bulk_update.side_effect = bulk_update

		with (
			patch.object(china_defaults.frappe, "db", fake_db),
			patch.object(china_defaults.frappe, "get_all", side_effect=get_all),
			patch.object(
				china_defaults,
				"CHINA_DEMO_RECORD_NAMES",
				{
					"Customer": {"Grant Plastics Ltd.": "格兰特塑料有限公司"},
					"Supplier": {"MA Inc.": "MA实业有限公司"},
				},
			),
			patch.object(china_defaults, "CHINA_DEMO_ITEM_NAMES", {"SKU001": ("T-shirt", "T恤")}),
		):
			self.assertTrue(china_defaults.localize_bundled_demo_cached_values())
			self.assertFalse(china_defaults.localize_bundled_demo_cached_values())

		expected_updates = {
			("Sales Order", "SAL-ORD-2026-00001", "customer_name", "格兰特塑料有限公司"),
			("Sales Invoice", "ACC-SINV-2026-00001", "customer_name", "格兰特塑料有限公司"),
			("Purchase Order", "PUR-ORD-2026-00001", "supplier_name", "MA实业有限公司"),
			("Purchase Invoice", "ACC-PINV-2026-00001", "supplier_name", "MA实业有限公司"),
			("Payment Entry", "ACC-PAY-2026-00001", "party_name", "格兰特塑料有限公司"),
			("Payment Entry", "ACC-PAY-2026-00002", "party_name", "MA实业有限公司"),
			("Sales Order Item", "soi-1", "item_name", "T恤"),
			("Sales Invoice Item", "sii-1", "item_name", "T恤"),
			("Purchase Order Item", "poi-1", "item_name", "T恤"),
			("Purchase Invoice Item", "pii-1", "item_name", "T恤"),
		}
		actual_updates = {
			(doctype, name, field, value)
			for call in fake_db.bulk_update.call_args_list
			for doctype, doc_updates in [call.args[:2]]
			for name, updates in doc_updates.items()
			for field, value in updates.items()
		}
		self.assertEqual(actual_updates, expected_updates)

	def test_demo_cached_value_patch_runs_master_migration_before_backfill(self):
		from erpnext.patches.v16_0 import localize_china_demo_cached_values as patch_module

		call_order = []
		with (
			patch.object(
				patch_module,
				"localize_bundled_demo_data",
				side_effect=lambda: call_order.append("masters"),
			) as migrate_masters,
			patch.object(
				patch_module,
				"localize_bundled_demo_cached_values",
				side_effect=lambda: call_order.append("cached_values"),
			) as backfill_cached_values,
		):
			patch_module.execute()

		migrate_masters.assert_called_once_with()
		backfill_cached_values.assert_called_once_with()
		self.assertEqual(call_order, ["masters", "cached_values"])

	def test_successful_demo_data_migration_is_idempotent(self):
		state = {
			("Item Group", "Demo Item Group"): {},
			("Customer Group", "Demo Customer Group"): {},
			("Customer", "Grant Plastics Ltd."): {"customer_group": "Demo Customer Group"},
			("Item", "SKU001"): {"item_name": "T-shirt", "item_group": "Demo Item Group"},
		}
		fake_db = MagicMock()
		fake_db.get_single_value.return_value = "占永杰企业数字化服务 (Demo)"
		fake_db.exists.side_effect = lambda doctype, name: (doctype, name) in state

		def get_value(doctype, name, field, as_dict=False):
			record = state.get((doctype, name))
			if not record:
				return None
			if as_dict:
				return MagicMock(**record)
			return record.get(field)

		def rename_doc(doctype, old_name, new_name, **kwargs):
			state[(doctype, new_name)] = state.pop((doctype, old_name))
			if doctype == "Item Group":
				state[("Item", "SKU001")]["item_group"] = new_name
			if doctype == "Customer Group":
				state[("Customer", "Grant Plastics Ltd.")]["customer_group"] = new_name

		def set_value(doctype, name, field, value, **kwargs):
			state[(doctype, name)][field] = value

		fake_db.get_value.side_effect = get_value
		fake_db.set_value.side_effect = set_value
		with (
			patch.object(china_defaults.frappe, "db", fake_db),
			patch.object(china_defaults.frappe, "get_all", return_value=[]),
			patch.object(china_defaults.frappe, "rename_doc", side_effect=rename_doc) as rename,
			patch.object(china_defaults, "rebuild_for_doctype") as rebuild_for_doctype,
			patch.object(
				china_defaults,
				"CHINA_DEMO_RECORD_NAMES",
				{
					"Item Group": {"Demo Item Group": "演示物料组"},
					"Customer Group": {"Demo Customer Group": "演示客户组"},
					"Customer": {"Grant Plastics Ltd.": "格兰特塑料有限公司"},
				},
			),
			patch.object(china_defaults, "CHINA_DEMO_ITEM_NAMES", {"SKU001": ("T-shirt", "T恤")}),
		):
			self.assertTrue(china_defaults.localize_bundled_demo_data())
			self.assertFalse(china_defaults.localize_bundled_demo_data())

		self.assertEqual(rename.call_count, 3)
		self.assertEqual(fake_db.set_value.call_count, 1)
		rebuild_for_doctype.assert_called_once_with("Item")

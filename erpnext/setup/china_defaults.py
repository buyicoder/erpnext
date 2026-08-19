import frappe
from frappe.utils.global_search import rebuild_for_doctype


CHINA_SYSTEM_DEFAULTS = {
	"country": "China",
	"language": "zh",
	"time_zone": "Asia/Shanghai",
	"currency": "CNY",
	"date_format": "yyyy-mm-dd",
	"time_format": "HH:mm:ss",
	"number_format": "#,###.##",
	"currency_precision": "2",
	"first_day_of_the_week": "Monday",
	"rounding_method": "Commercial Rounding",
}

CHINA_PRINT_FORMAT_TRANSLATIONS = {
	"Sales Order Standard": "销售订单（标准）",
	"Sales Order with Item Image": "销售订单（含物料图片）",
	"Sales Invoice Standard": "销售发票（标准）",
	"Sales Invoice with Item Image": "销售发票（含物料图片）",
	"Delivery Note Standard": "销售出库单（标准）",
	"Delivery Note with Item Image": "销售出库单（含物料图片）",
	"Purchase Order Standard": "采购订单（标准）",
	"Purchase Order with Item Image": "采购订单（含物料图片）",
	"Purchase Invoice Standard": "采购发票（标准）",
	"Purchase Invoice with Item Image": "采购发票（含物料图片）",
	"POS Invoice Standard": "POS 发票（标准）",
	"POS Invoice with Item Image": "POS 发票（含物料图片）",
	"Quotation Standard": "报价单（标准）",
	"Quotation with Item Image": "报价单（含物料图片）",
	"Request for Quotation with Item Image": "询价单（含物料图片）",
}

CHINA_LETTER_HEAD_TRANSLATIONS = {
	"Company Letterhead - Grey": "公司抬头（灰色）",
}

CHINA_DEMO_RECORD_NAMES = {
	"Item Group": {"Demo Item Group": "演示物料组"},
	"Customer Group": {"Demo Customer Group": "演示客户组"},
	"Supplier Group": {"Demo Supplier Group": "演示供应商组"},
	"Customer": {
		"Grant Plastics Ltd.": "格兰特塑料有限公司",
		"West View Software Ltd.": "西景软件有限公司",
		"Palmer Productions Ltd.": "帕尔默制造有限公司",
	},
	"Supplier": {
		"Zuckerman Security Ltd.": "祖克曼安防有限公司",
		"MA Inc.": "MA实业有限公司",
		"Summit Traders Ltd.": "山峰贸易有限公司",
	},
}

CHINA_DEMO_ITEM_NAMES = {
	"SKU001": ("T-shirt", "T恤"),
	"SKU002": ("Laptop", "笔记本电脑"),
	"SKU003": ("Book", "图书"),
	"SKU004": ("Smartphone", "智能手机"),
	"SKU005": ("Sneakers", "运动鞋"),
	"SKU006": ("Coffee Mug", "咖啡杯"),
	"SKU007": ("Television", "电视机"),
	"SKU008": ("Backpack", "双肩包"),
	"SKU009": ("Headphones", "耳机"),
	"SKU010": ("Camera", "相机"),
}

UPSTREAM_CHINA_ADDRESS_TEMPLATE = """{{ address_line1 }}<br>
{% if address_line2 %}{{ address_line2 }}<br>{% endif -%}
{{ city }}<br>
{% if state %}{{ state }}<br>{% endif -%}
{% if pincode %}{{ pincode }}<br>{% endif -%}
{{ country }}<br>
<br>
{% if phone %}{{ _(\"Phone\") }}: {{ phone }}<br>{% endif -%}
{% if fax %}{{ _(\"Fax\") }}: {{ fax }}<br>{% endif -%}
{% if email_id %}{{ _(\"Email\") }}: {{ email_id }}<br>{% endif -%}
"""

CHINA_ADDRESS_TEMPLATE = """中国{% if state %}{{ state }}{% endif -%}{% if city %}{{ city }}{% endif -%}{% if county %}{{ county }}{% endif -%}<br>
{% if address_line1 %}{{ address_line1 }}{% endif -%}{% if address_line2 %}{{ address_line2 }}{% endif -%}<br>
{% if pincode %}邮编：{{ pincode }}<br>{% endif -%}
{% if phone %}电话：{{ phone }}<br>{% endif -%}
{% if fax %}传真：{{ fax }}<br>{% endif -%}
{% if email_id %}邮箱：{{ email_id }}<br>{% endif -%}
"""


def apply_china_defaults(force=False, clear_cache=True):
	"""Apply mainland-China defaults without overwriting existing preferences."""
	system_settings = frappe.get_single("System Settings")
	changed = _apply_defaults(system_settings, CHINA_SYSTEM_DEFAULTS, force=force)
	if changed:
		system_settings.save(ignore_permissions=True)

	global_defaults = frappe.get_single("Global Defaults")
	global_defaults_changed = _apply_defaults(
		global_defaults,
		{"country": "China", "default_currency": "CNY"},
		force=force,
	)
	if global_defaults_changed:
		global_defaults.save(ignore_permissions=True)
	address_template_changed = ensure_china_address_template()
	print_format_labels_changed = ensure_china_print_format_labels(force=force)
	letter_head_labels_changed = ensure_china_letter_head_labels(force=force)

	if clear_cache and (
		changed
		or global_defaults_changed
		or address_template_changed
		or print_format_labels_changed
		or letter_head_labels_changed
	):
		frappe.clear_cache()
	return CHINA_SYSTEM_DEFAULTS


def localize_bundled_demo_data():
	"""Localize the records created by ERPNext's demo-data loader."""
	if not frappe.db.get_single_value("Global Defaults", "demo_company"):
		return False

	changed = False
	item_names_changed = False
	for doctype, names in CHINA_DEMO_RECORD_NAMES.items():
		for old_name, new_name in names.items():
			if not frappe.db.exists(doctype, old_name) or frappe.db.exists(doctype, new_name):
				continue
			if doctype == "Customer" and frappe.db.get_value(doctype, old_name, "customer_group") not in {
				"Demo Customer Group",
				"演示客户组",
			}:
				continue
			if doctype == "Supplier" and frappe.db.get_value(doctype, old_name, "supplier_group") not in {
				"Demo Supplier Group",
				"演示供应商组",
			}:
				continue
			frappe.rename_doc(doctype, old_name, new_name, show_alert=False)
			changed = True

	for item_code, (old_name, new_name) in CHINA_DEMO_ITEM_NAMES.items():
		item = frappe.db.get_value("Item", item_code, ["item_name", "item_group"], as_dict=True)
		if not item or item.item_name != old_name or item.item_group not in {
			"Demo Item Group",
			"演示物料组",
		}:
			continue
		frappe.db.set_value("Item", item_code, "item_name", new_name, update_modified=False)
		changed = True
		item_names_changed = True

	if item_names_changed:
		rebuild_for_doctype("Item")

	return changed


def _apply_defaults(doc, defaults, force=False):
	updates = {
		field: value
		for field, value in defaults.items()
		if force or getattr(doc, field, None) in (None, "")
	}
	if not updates:
		return False
	doc.update(updates)
	return True


def ensure_china_address_template(force=False):
	"""Install the Chinese address order without overwriting a custom template."""
	if frappe.db.exists("Address Template", "China"):
		template = frappe.get_doc("Address Template", "China")
		if not force and template.template not in {
			UPSTREAM_CHINA_ADDRESS_TEMPLATE,
			CHINA_ADDRESS_TEMPLATE,
		}:
			return False
	else:
		template = frappe.new_doc("Address Template")
		template.country = "China"

	if template.template == CHINA_ADDRESS_TEMPLATE and template.is_default == 1:
		return False

	template.is_default = 1
	template.template = CHINA_ADDRESS_TEMPLATE
	template.save(ignore_permissions=True)
	return True


def ensure_china_print_format_labels(force=False):
	"""Translate print-format display labels while preserving their stable record names."""
	return _ensure_translated_doctype_labels("Print Format", CHINA_PRINT_FORMAT_TRANSLATIONS, force)


def ensure_china_letter_head_labels(force=False):
	"""Translate letter-head display labels while preserving their stable record names."""
	return _ensure_translated_doctype_labels("Letter Head", CHINA_LETTER_HEAD_TRANSLATIONS, force)


def _ensure_translated_doctype_labels(doctype, translations, force=False):
	changed = False
	explicit_setting = frappe.db.get_value(
		"Property Setter",
		{
			"doc_type": doctype,
			"doctype_or_field": "DocType",
			"property": "translated_doctype",
		},
		"value",
	)
	should_enable_translation = explicit_setting != "0" or force
	if should_enable_translation and not frappe.get_meta(doctype).translated_doctype:
		frappe.make_property_setter(
			{
				"doctype": doctype,
				"doctype_or_field": "DocType",
				"property": "translated_doctype",
				"value": "1",
				"property_type": "Check",
			}
		)
		changed = True

	records = frappe.get_all(
		"Translation",
		filters={"language": "zh", "source_text": ["in", list(translations)]},
		fields=["name", "source_text", "context", "translated_text"],
		limit_page_length=0,
	)
	existing = {record.source_text: record for record in records if not record.context}

	for source, translated in translations.items():
		record = existing.get(source)
		if record:
			if record.translated_text == translated:
				continue
			if record.translated_text:
				continue
			translation = frappe.get_doc("Translation", record.name)
		else:
			translation = frappe.new_doc("Translation")
			translation.language = "zh"
			translation.source_text = source

		translation.translated_text = translated
		translation.save(ignore_permissions=True)
		changed = True

	return changed

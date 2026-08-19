import frappe


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

	if clear_cache and (changed or global_defaults_changed or address_template_changed or print_format_labels_changed):
		frappe.clear_cache()
	return CHINA_SYSTEM_DEFAULTS


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
	changed = False
	explicit_setting = frappe.db.get_value(
		"Property Setter",
		{
			"doc_type": "Print Format",
			"doctype_or_field": "DocType",
			"property": "translated_doctype",
		},
		"value",
	)
	should_enable_translation = explicit_setting != "0" or force
	if should_enable_translation and not frappe.get_meta("Print Format").translated_doctype:
		frappe.make_property_setter(
			{
				"doctype": "Print Format",
				"doctype_or_field": "DocType",
				"property": "translated_doctype",
				"value": "1",
				"property_type": "Check",
			}
		)
		changed = True

	records = frappe.get_all(
		"Translation",
		filters={"language": "zh", "source_text": ["in", list(CHINA_PRINT_FORMAT_TRANSLATIONS)]},
		fields=["name", "source_text", "context", "translated_text"],
		limit_page_length=0,
	)
	existing = {record.source_text: record for record in records if not record.context}

	for source, translated in CHINA_PRINT_FORMAT_TRANSLATIONS.items():
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

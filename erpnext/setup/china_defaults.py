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


def apply_china_defaults(force=False):
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

	if changed or global_defaults_changed or address_template_changed:
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

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


def apply_china_defaults():
	"""Apply idempotent defaults expected by a mainland-China deployment."""
	system_settings = frappe.get_single("System Settings")
	system_settings.update(CHINA_SYSTEM_DEFAULTS)
	system_settings.save(ignore_permissions=True)

	global_defaults = frappe.get_single("Global Defaults")
	global_defaults.country = "China"
	global_defaults.default_currency = "CNY"
	global_defaults.save(ignore_permissions=True)

	frappe.clear_cache()
	return CHINA_SYSTEM_DEFAULTS

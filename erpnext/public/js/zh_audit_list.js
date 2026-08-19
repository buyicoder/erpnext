if (frappe.boot.lang === "zh") {
	const zh_finance = frappe.utils.zh_finance;
	const activity_log_settings = frappe.listview_settings["Activity Log"];
	const access_log_settings = frappe.listview_settings["Access Log"];
	const user_settings = frappe.listview_settings.User;

	if (activity_log_settings) {
		activity_log_settings.formatters = {
			...activity_log_settings.formatters,
			subject: (value) => zh_finance.localize_login_activity_text(value, __),
		};
	}

	if (access_log_settings) {
		access_log_settings.formatters = {
			...access_log_settings.formatters,
			export_from: (value) => zh_finance.localize_audit_doctype_text(value, __),
		};
	}

	if (user_settings) {
		user_settings.formatters = {
			...user_settings.formatters,
			user_type: (value) => zh_finance.localize_audit_doctype_text(value, __),
		};
	}
}

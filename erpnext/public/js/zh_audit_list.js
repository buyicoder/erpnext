if (frappe.boot.lang === "zh") {
	const localize_audit_text = (value) =>
		frappe.utils.zh_finance?.localize_audit_doctype_text?.(value, __) ?? value;
	const localize_login_text = (value) =>
		frappe.utils.zh_finance?.localize_login_activity_text?.(value, __) ?? value;
	const activity_log_settings = frappe.listview_settings["Activity Log"];
	const access_log_settings = frappe.listview_settings["Access Log"];
	const user_settings = frappe.listview_settings.User;

	if (activity_log_settings) {
		activity_log_settings.formatters = {
			...activity_log_settings.formatters,
			subject: localize_login_text,
		};
	}

	if (access_log_settings) {
		access_log_settings.formatters = {
			...access_log_settings.formatters,
			export_from: localize_audit_text,
		};
	}

	if (user_settings) {
		user_settings.formatters = {
			...user_settings.formatters,
			user_type: localize_audit_text,
		};
	}
}

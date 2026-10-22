import json

import frappe


def execute():
	chart_filters = {
		"Budget Variance": {
			"company": 'frappe.defaults.get_user_default("Company")',
			"from_fiscal_year": "frappe.sys_defaults.fiscal_year",
			"to_fiscal_year": "frappe.sys_defaults.fiscal_year",
		},
		"Profit and Loss": {
			"company": 'frappe.defaults.get_user_default("Company")',
			"from_fiscal_year": "frappe.sys_defaults.fiscal_year",
			"to_fiscal_year": "frappe.sys_defaults.fiscal_year",
		},
		"Purchase Order Trends": {
			"company": 'frappe.defaults.get_user_default("Company")',
			"fiscal_year": "frappe.sys_defaults.fiscal_year",
		},
		"Sales Order Trends": {
			"company": 'frappe.defaults.get_user_default("Company")',
			"fiscal_year": "frappe.sys_defaults.fiscal_year",
		},
		"Top Customers": {
			"company": 'frappe.defaults.get_user_default("Company")',
			"fiscal_year": "frappe.sys_defaults.fiscal_year",
		},
		"Top Suppliers": {
			"company": 'frappe.defaults.get_user_default("Company")',
			"fiscal_year": "frappe.sys_defaults.fiscal_year",
		},
	}

	for chart_name, filters in chart_filters.items():
		if frappe.db.exists("Dashboard Chart", chart_name):
			frappe.db.set_value(
				"Dashboard Chart",
				chart_name,
				"dynamic_filters_json",
				json.dumps(filters, separators=(",", ":")),
				update_modified=False,
			)

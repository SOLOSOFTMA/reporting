// Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.require("assets/reporting/js/financial_statements.js", function() {
	frappe.query_reports["Draft Cash Flow"] = $.extend({},
		erpnext.financial_statements);

	frappe.query_reports["Draft Cash Flow"]["filters"].push({
		"fieldname": "accumulated_values",
		"label": __("Accumulated Values"),
		"fieldtype": "Check"
	}
	,
		{
			"fieldname": "show_draft",
			"label": __("Show Draft"),
			"fieldtype": "Check",
			"default": 1
		},
		{
			"fieldname": "show_submitted",
			"label": __("Show Submitted"),
			"fieldtype": "Check",
			"default": 0
		}
	
	);
});

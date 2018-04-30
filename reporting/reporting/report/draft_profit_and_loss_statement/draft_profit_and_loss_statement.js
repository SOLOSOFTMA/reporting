// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.require("assets/reporting/js/financial_statements.js", function() {
	frappe.query_reports["Draft Profit and Loss Statement"] = $.extend({},
		erpnext.financial_statements);

	frappe.query_reports["Draft Profit and Loss Statement"]["filters"].push(
		//~ {
			//~ "fieldname":"cost_center",
			//~ "label": __("Cost Center"),
			//~ "fieldtype": "Link",
			//~ "options": "Cost Center"
		//~ },
		//~ {
			//~ "fieldname":"project",
			//~ "label": __("Project"),
			//~ "fieldtype": "Link",
			//~ "options": "Project"
		//~ },
		{
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
			"default": 1
		}
	);
});

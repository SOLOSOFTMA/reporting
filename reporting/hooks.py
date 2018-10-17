# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "reporting"
app_title = "Reporting"
app_publisher = "ahmad18"
app_description = "Reporting"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "a@a.a"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/reporting/css/reporting.css"
# app_include_js = "/assets/reporting/js/reporting.js"

# include js, css files in header of web template
# web_include_css = "/assets/reporting/css/reporting.css"
# web_include_js = "/assets/reporting/js/reporting.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "reporting.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "reporting.install.before_install"
# after_install = "reporting.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "reporting.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

	# target_docs_list = [
	# "Payment Entry", 		Done
	# "Purchase Invoice", 	Done
	# "Expense Claim",  	Done
	# "Journal Entry", 		Done
	# "Sales Invoice", 		Done
	# "Purchase Receipt", 
	# "Delivery Note"]


doc_events = {
	"Payment Entry": {
		"after_insert": "reporting.reporting.doctype.gl_entry2.gl_entry2.make_gl_entries_payment_entry",
		"on_trash": "reporting.reporting.doctype.gl_entry2.gl_entry2.make_gl_entries_cancel_payment_entry",
		"on_submit": "reporting.reporting.doctype.gl_entry2.gl_entry2.make_gl_entries_cancel_payment_entry"
	},
	"Expense Claim": {
		"after_insert": "reporting.reporting.doctype.gl_entry2.gl_entry2.make_gl_entries_expense",
		"on_trash": "reporting.reporting.doctype.gl_entry2.gl_entry2.make_gl_entries_expense_cancel",
		"on_submit": "reporting.reporting.doctype.gl_entry2.gl_entry2.make_gl_entries_expense_cancel"
	},
	# "Purchase Receipt": {
	# 	"after_insert": "reporting.reporting.doctype.gl_entry2.gl_entry2.make_gl_entries_purchase_receipt_and_Delivery_note",
	# 	"on_trash": "reporting.reporting.doctype.gl_entry2.gl_entry2.make_gl_entries_stock_cancel",
	# 	"on_submit": "reporting.reporting.doctype.gl_entry2.gl_entry2.make_gl_entries_stock_cancel"
	# },
	"Purchase Invoice": {
		"after_insert": "reporting.reporting.doctype.gl_entry2.gl_entry2.make_gl_entries_purchase",
		"on_trash": "reporting.reporting.doctype.gl_entry2.gl_entry2.make_gl_entries_stock_cancel",
		"on_submit": "reporting.reporting.doctype.gl_entry2.gl_entry2.make_gl_entries_stock_cancel"
	},
	"Sales Invoice": {
		"after_insert": "reporting.reporting.doctype.gl_entry2.gl_entry2.make_gl_entries_sales_invoice",
		"on_trash": "reporting.reporting.doctype.gl_entry2.gl_entry2.make_gl_entries_stock_cancel",
		"on_submit": "reporting.reporting.doctype.gl_entry2.gl_entry2.make_gl_entries_stock_cancel"
	},
	"Journal Entry": {
		"after_insert": "reporting.reporting.doctype.gl_entry2.gl_entry2.make_gl_entries",
		"on_trash": "reporting.reporting.doctype.gl_entry2.gl_entry2.make_gl_entries_cancel",
		"on_submit": "reporting.reporting.doctype.gl_entry2.gl_entry2.make_gl_entries_cancel",
		"on_update": "reporting.reporting.doctype.gl_entry2.gl_entry2.make_gl_entries_on_update"
	}
	# ,
	# "Delivery Note": {
	# 	"after_insert": "reporting.reporting.doctype.gl_entry2.gl_entry2.make_gl_entries_purchase_receipt_and_Delivery_note",
	# 	"on_trash": "reporting.reporting.doctype.gl_entry2.gl_entry2.make_gl_entries_stock_cancel",
	# 	"on_submit": "reporting.reporting.doctype.gl_entry2.gl_entry2.make_gl_entries_stock_cancel"
	# }
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"reporting.tasks.all"
# 	],
# 	"daily": [
# 		"reporting.tasks.daily"
# 	],
# 	"hourly": [
# 		"reporting.tasks.hourly"
# 	],
# 	"weekly": [
# 		"reporting.tasks.weekly"
# 	]
# 	"monthly": [
# 		"reporting.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "reporting.install.before_tests"

# Overriding Whitelisted Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "reporting.event.get_events"
# }


# -*- coding: utf-8 -*-
# Copyright (c) 2018, ahmad18 and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, erpnext
from frappe.model.document import Document

from frappe.model.meta import get_field_precision
from erpnext.accounts.doctype.budget.budget import validate_expense_against_budget

import frappe, erpnext, json
from frappe.utils import cstr, flt, fmt_money, formatdate, getdate, nowdate, cint
from frappe import msgprint, _
from erpnext.stock import get_warehouse_account_map

from erpnext.controllers.stock_controller import update_gl_entries_after

class GLEntry2(Document):
	pass



#update for new server create gl2 for journal entry onely 
list_of_error = []

def new_server():
	jv = frappe.get_all('Journal Entry', filters={'docstatus': 0 }, fields=['name', 'posting_date'], order_by='posting_date')
	for jv_object in jv:
		jv_name = jv_object.get('name')
		doc = frappe.get_doc("Journal Entry", jv_name)
		make_gl_entries(doc,"create")
	print "list_of_error" 
	print "list_of_error" 
	print "list_of_error" 
	print "list_of_error" 
	print list_of_error 

	return list_of_error 

#expense claim
def make_gl_entries_expense(doc, method):
	self = doc 
	cancel = False 
	if flt(self.total_sanctioned_amount) > 0:
		gl_entries = self.get_gl_entries()
		make_gl2_entries(gl_entries, cancel)

def make_gl_entries_expense_cancel(doc, method):
	self=doc
	if self.payable_account:
		cancel = True
		if flt(self.total_sanctioned_amount) > 0:
			gl_entries = self.get_gl_entries()
			make_gl2_entries(gl_entries, cancel)

#purchase invoice 
def make_gl_entries_purchase(doc, method):
	self = doc
	gl_entries=None
	repost_future_gle=True
	from_repost=False

	if not self.grand_total:
		return
	if not gl_entries:
		gl_entries = self.get_gl_entries()

	if gl_entries:
		update_outstanding = "No" if (cint(self.is_paid) or self.write_off_account) else "Yes"

		make_gl2_entries(gl_entries,  cancel=(self.docstatus == 2),
			update_outstanding=update_outstanding, merge_entries=False)

		if update_outstanding == "No":
			update_outstanding_amt(self.credit_to, "Supplier", self.supplier,
				self.doctype, self.return_against if cint(self.is_return and self.return_against) else self.name)

		if repost_future_gle and cint(self.update_stock) and self.auto_accounting_for_stock:
			items, warehouses = self.get_items_and_warehouses()
			update_gl_entries_after(self.posting_date, self.posting_time, warehouses, items)

	elif self.docstatus == 2 and cint(self.update_stock) and self.auto_accounting_for_stock:
		delete_gl_entries(voucher_type=self.doctype, voucher_no=self.name)



#sales invoice 

def make_gl_entries_sales_invoice(doc, method):
	self=doc
	gl_entries=None
	repost_future_gle=True
	from_repost=False
	
	auto_accounting_for_stock = erpnext.is_perpetual_inventory_enabled(self.company)

	if not self.grand_total:
		return

	if not gl_entries:
		gl_entries = self.get_gl_entries()

	if gl_entries:

		# if POS and amount is written off, updating outstanding amt after posting all gl entries
		update_outstanding = "No" if (cint(self.is_pos) or self.write_off_account) else "Yes"

		make_gl2_entries(gl_entries, cancel=(self.docstatus == 2),
			update_outstanding=update_outstanding, merge_entries=False)

		if update_outstanding == "No":
			from erpnext.accounts.doctype.gl_entry.gl_entry import update_outstanding_amt
			update_outstanding_amt(self.debit_to, "Customer", self.customer,
				self.doctype, self.return_against if cint(self.is_return) and self.return_against else self.name)

		if repost_future_gle and cint(self.update_stock) \
			and cint(auto_accounting_for_stock):
				items, warehouses = self.get_items_and_warehouses()
				update_gl_entries_after(self.posting_date, self.posting_time, warehouses, items)
	elif self.docstatus == 2 and cint(self.update_stock) \
		and cint(auto_accounting_for_stock):
			delete_gl_entries(voucher_type=self.doctype, voucher_no=self.name)

#payment entry
def make_gl_entries_payment_entry(doc, method):

	self=doc
	cancel=0
	adv_adj=0,

	if self.payment_type in ("Receive", "Pay") and not self.get("party_account_field"):
		self.setup_party_account_field()

	gl_entries = []
	self.add_party_gl_entries(gl_entries)
	self.add_bank_gl_entries(gl_entries)
	self.add_deductions_gl_entries(gl_entries)

	make_gl2_entries(gl_entries, cancel=cancel, adv_adj=adv_adj)

def make_gl_entries_cancel_payment_entry(doc, method):
	self=doc
	cancel=1
	adv_adj=0,

	if self.payment_type in ("Receive", "Pay") and not self.get("party_account_field"):
		self.setup_party_account_field()

	gl_entries = []
	self.add_party_gl_entries(gl_entries)
	self.add_bank_gl_entries(gl_entries)
	self.add_deductions_gl_entries(gl_entries)

	make_gl2_entries(gl_entries, cancel=cancel, adv_adj=adv_adj)


#purchase receipt
#stock delivery note 
# cancillation works for sales invoice an purchase invoice and payment entry
def make_gl_entries_purchase_receipt_and_Delivery_note(doc,method):
	update_stock_ledger(doc)
	make_gl_entries_stock(doc)
def make_gl_entries_stock_cancel(doc,method):
	make_gl_entries_on_cancel(doc)



def make_gl_entries_on_cancel(doc, repost_future_gle=True):
	self=doc
	if frappe.db.sql("""select name from `tabGL Entry2` where voucher_type=%s
		and voucher_no=%s""", (self.doctype, self.name)):
			make_gl_entries_stock_cancel_draft(self,repost_future_gle=repost_future_gle)

def make_gl_entries_stock_cancel_draft(self, gl_entries=None, repost_future_gle=True, from_repost=False):
	if self.docstatus == 0:
		delete_gl_entries(voucher_type=self.doctype, voucher_no=self.name)

def make_gl_entries_stock(self, gl_entries=None, repost_future_gle=True, from_repost=False):
	if self.docstatus == 2:
		delete_gl_entries(voucher_type=self.doctype, voucher_no=self.name)

	if cint(erpnext.is_perpetual_inventory_enabled(self.company)):
		warehouse_account = get_warehouse_account_map()

		if self.docstatus==0:
			if not gl_entries:
				gl_entries = get_gl_entries_receipt(self,warehouse_account)
				frappe.throw(str(gl_entries))			
			make_gl2_entries(gl_entries, from_repost=from_repost)

		if repost_future_gle:
			items, warehouses = self.get_items_and_warehouses()
			update_gl_entries_after(self.posting_date, self.posting_time, warehouses, items,
				warehouse_account)
	elif self.doctype in ['Purchase Receipt', 'Purchase Invoice'] and self.docstatus == 0:
		gl_entries = []
		gl_entries = self.get_asset_gl_entry(gl_entries)
		frappe.msgprint(str(gl_entries))			
		make_gl2_entries(gl_entries, from_repost=from_repost)


def make_gl_entries_cancel(doc, method):
	# from erpnext.accounts.general_ledger import make_gl_entries
	self=doc
	cancel=1
	adv_adj=0,
	gl_map = []
	
	for d in self.get("accounts"):
		if d.debit or d.credit:
			gl_map.append(
				self.get_gl_dict({
					"account": d.account,
					"party_type": d.party_type,
					"party": d.party,
					"against": d.against_account,
					"debit": flt(d.debit, d.precision("debit")),
					"credit": flt(d.credit, d.precision("credit")),
					"account_currency": d.account_currency,
					"debit_in_account_currency": flt(d.debit_in_account_currency, d.precision("debit_in_account_currency")),
					"credit_in_account_currency": flt(d.credit_in_account_currency, d.precision("credit_in_account_currency")),
					"against_voucher_type": d.reference_type,
					"against_voucher": d.reference_name,
					"remarks": self.remark,
					"cost_center": d.cost_center,
					"project": d.project
					# "finance_book": self.finance_book
				})
			)

	if gl_map:
		make_gl2_entries(gl_map, cancel=cancel, adv_adj=adv_adj)

@frappe.whitelist()
def make_gl_entries_on_update(doc, method):
	make_gl_entries_cancel(doc, method)
	make_gl_entries(doc, method)

@frappe.whitelist()
def make_gl_entries(doc, method):
	# from erpnext.accounts.general_ledger import make_gl_entries
	self=doc
	cancel=0
	adv_adj=0,
	gl_map = []
	for d in self.get("accounts"):
		if d.debit or d.credit:
			gl_map.append(
				self.get_gl_dict({
					"account": d.account,
					"party_type": d.party_type,
					"party": d.party,
					"against": d.against_account,
					"debit": flt(d.debit, d.precision("debit")),
					"credit": flt(d.credit, d.precision("credit")),
					"account_currency": d.account_currency,
					"debit_in_account_currency": flt(d.debit_in_account_currency, d.precision("debit_in_account_currency")),
					"credit_in_account_currency": flt(d.credit_in_account_currency, d.precision("credit_in_account_currency")),
					"against_voucher_type": d.reference_type,
					"against_voucher": d.reference_name,
					"remarks": self.remark,
					"cost_center": d.cost_center,
					"project": d.project
					# "finance_book": self.finance_book
				})
			)

	if gl_map:
		#print(checkerrr(gl_map, cancel=cancel, adv_adj=adv_adj))
		if checkerrr(gl_map, cancel=cancel, adv_adj=adv_adj):

			make_gl2_entries(gl_map, cancel=cancel, adv_adj=adv_adj)
		else:

			list_of_error.append(str(doc.name))


def make_gl2_entries(gl_map, cancel=False, adv_adj=False, merge_entries=True, update_outstanding='Yes', from_repost=False):
	if gl_map:
		if not cancel:
			gl_map = process_gl_map(gl_map, merge_entries)
			if gl_map and len(gl_map) > 1:
				save_entries(gl_map, adv_adj, update_outstanding, from_repost)
			else:
				frappe.throw(_("Incorrect number of General Ledger Entries found. You might have selected a wrong Account in the transaction."))
		else:
			delete_gl_entries(gl_map, adv_adj=adv_adj, update_outstanding=update_outstanding)

def checkerrr(gl_map, cancel=False, adv_adj=False, merge_entries=True, update_outstanding='Yes', from_repost=False):
	if gl_map:
		if not cancel:
			gl_map = process_gl_map(gl_map, merge_entries)
			if gl_map and len(gl_map) > 1:
				if save_entries_chker(gl_map, adv_adj, update_outstanding, from_repost):
					return True 
			else:
				return False 
	
		# else:
		# 	delete_gl_entries(gl_map, adv_adj=adv_adj, update_outstanding=update_outstanding)


def process_gl_map(gl_map, merge_entries=True):
	if merge_entries:
		gl_map = merge_similar_entries(gl_map)
	for entry in gl_map:
		# toggle debit, credit if negative entry
		if flt(entry.debit) < 0:
			entry.credit = flt(entry.credit) - flt(entry.debit)
			entry.debit = 0.0

		if flt(entry.debit_in_account_currency) < 0:
			entry.credit_in_account_currency = \
				flt(entry.credit_in_account_currency) - flt(entry.debit_in_account_currency)
			entry.debit_in_account_currency = 0.0

		if flt(entry.credit) < 0:
			entry.debit = flt(entry.debit) - flt(entry.credit)
			entry.credit = 0.0

		if flt(entry.credit_in_account_currency) < 0:
			entry.debit_in_account_currency = \
				flt(entry.debit_in_account_currency) - flt(entry.credit_in_account_currency)
			entry.credit_in_account_currency = 0.0

	return gl_map

def merge_similar_entries(gl_map):
	merged_gl_map = []
	for entry in gl_map:
		# if there is already an entry in this account then just add it
		# to that entry
		same_head = check_if_in_list(entry, merged_gl_map)
		if same_head:
			same_head.debit	= flt(same_head.debit) + flt(entry.debit)
			same_head.debit_in_account_currency	= \
				flt(same_head.debit_in_account_currency) + flt(entry.debit_in_account_currency)
			same_head.credit = flt(same_head.credit) + flt(entry.credit)
			same_head.credit_in_account_currency = \
				flt(same_head.credit_in_account_currency) + flt(entry.credit_in_account_currency)
		else:
			merged_gl_map.append(entry)

	# filter zero debit and credit entries
	merged_gl_map = filter(lambda x: flt(x.debit, 9)!=0 or flt(x.credit, 9)!=0, merged_gl_map)
	merged_gl_map = list(merged_gl_map)
		
	return merged_gl_map

	
def check_if_in_list(gle, gl_map):
	for e in gl_map:
		if e.account == gle.account \
			and cstr(e.get('party_type'))==cstr(gle.get('party_type')) \
			and cstr(e.get('party'))==cstr(gle.get('party')) \
			and cstr(e.get('against_voucher'))==cstr(gle.get('against_voucher')) \
			and cstr(e.get('against_voucher_type')) == cstr(gle.get('against_voucher_type')) \
			and cstr(e.get('cost_center')) == cstr(gle.get('cost_center')) \
			and cstr(e.get('project')) == cstr(gle.get('project')):
				return e

def save_entries_chker(gl_map, adv_adj, update_outstanding, from_repost=False):
	if not from_repost:
		validate_account_for_perpetual_inventory(gl_map)

	if  round_off_debit_credit_chker(gl_map):
		return True
	else:
		return False
	# for entry in gl_map:
	# 	make_entry(entry, adv_adj, update_outstanding, from_repost)
		
	# 	# check against budget
	# 	if not from_repost:
	# 		validate_expense_against_budget(entry)

def save_entries(gl_map, adv_adj, update_outstanding, from_repost=False):
	if not from_repost:
		validate_account_for_perpetual_inventory(gl_map)

	#round_off_debit_credit(gl_map)
	for entry in gl_map:
		make_entry(entry, adv_adj, update_outstanding, from_repost)
		
		# check against budget
		if not from_repost:
			validate_expense_against_budget(entry)

def make_entry(args, adv_adj, update_outstanding, from_repost=False):
	args.update({"doctype": "GL Entry2"})
	gle = frappe.get_doc(args)
	gle.flags.ignore_permissions = 1
	gle.flags.from_repost = from_repost
	gle.insert()
	gle.run_method("on_update_with_args", adv_adj, update_outstanding, from_repost)
	gle.submit()

def validate_account_for_perpetual_inventory(gl_map):
	if cint(erpnext.is_perpetual_inventory_enabled(gl_map[0].company)) \
		and gl_map[0].voucher_type=="Journal Entry":
			aii_accounts = [d[0] for d in frappe.db.sql("""select name from tabAccount
				where account_type = 'Stock' and is_group=0""")]

			for entry in gl_map:
				if entry.account in aii_accounts:
					frappe.throw(_("Account: {0} can only be updated via Stock Transactions")
						.format(entry.account), StockAccountInvalidTransaction)



def round_off_debit_credit_chker(gl_map):
	precision = get_field_precision(frappe.get_meta("GL Entry2").get_field("debit"),
		currency=frappe.db.get_value("Company", gl_map[0].company, "default_currency", cache=True))

	debit_credit_diff = 0.0
	for entry in gl_map:
		entry.debit = flt(entry.debit, precision)
		entry.credit = flt(entry.credit, precision)
		debit_credit_diff += entry.debit - entry.credit

	debit_credit_diff = flt(debit_credit_diff, precision)
	
	if gl_map[0]["voucher_type"] in ("Journal Entry", "Payment Entry"):
		allowance = 5.0 / (10**precision)
	else:
		allowance = .5
	
	if abs(debit_credit_diff) >= allowance:
		return False
		# frappe.throw(_("Debit and Credit not equal for {0} #{1}. Difference is {2}.")
		# 	.format(gl_map[0].voucher_type, gl_map[0].voucher_no, debit_credit_diff))
	else:
		return True

def round_off_debit_credit(gl_map):
	precision = get_field_precision(frappe.get_meta("GL Entry2").get_field("debit"),
		currency=frappe.db.get_value("Company", gl_map[0].company, "default_currency", cache=True))

	debit_credit_diff = 0.0
	for entry in gl_map:
		entry.debit = flt(entry.debit, precision)
		entry.credit = flt(entry.credit, precision)
		debit_credit_diff += entry.debit - entry.credit

	debit_credit_diff = flt(debit_credit_diff, precision)
	
	if gl_map[0]["voucher_type"] in ("Journal Entry", "Payment Entry"):
		allowance = 5.0 / (10**precision)
	else:
		allowance = .5
	
	if abs(debit_credit_diff) >= allowance:
		frappe.throw(_("Debit and Credit not equal for {0} #{1}. Difference is {2}.")
			.format(gl_map[0].voucher_type, gl_map[0].voucher_no, debit_credit_diff))

	elif abs(debit_credit_diff) >= (1.0 / (10**precision)):
		make_round_off_gle(gl_map, debit_credit_diff)

def make_round_off_gle(gl_map, debit_credit_diff):
	round_off_account, round_off_cost_center = get_round_off_account_and_cost_center(gl_map[0].company)

	round_off_gle = frappe._dict()
	for k in ["voucher_type", "voucher_no", "company",
		"posting_date", "remarks", "is_opening"]:
			round_off_gle[k] = gl_map[0][k]

	round_off_gle.update({
		"account": round_off_account,
		"debit_in_account_currency": abs(debit_credit_diff) if debit_credit_diff < 0 else 0,
		"credit_in_account_currency": debit_credit_diff if debit_credit_diff > 0 else 0,
		"debit": abs(debit_credit_diff) if debit_credit_diff < 0 else 0,
		"credit": debit_credit_diff if debit_credit_diff > 0 else 0,
		"cost_center": round_off_cost_center,
		"party_type": None,
		"party": None,
		"against_voucher_type": None,
		"against_voucher": None
	})

	gl_map.append(round_off_gle)

def get_round_off_account_and_cost_center(company):
	round_off_account, round_off_cost_center = frappe.db.get_value("Company", company,
		["round_off_account", "round_off_cost_center"]) or [None, None]
	if not round_off_account:
		frappe.throw(_("Please mention Round Off Account in Company"))

	if not round_off_cost_center:
		frappe.throw(_("Please mention Round Off Cost Center in Company"))

	return round_off_account, round_off_cost_center

def delete_gl_entries(gl_entries=None, voucher_type=None, voucher_no=None,
		adv_adj=False, update_outstanding="Yes"):

	from erpnext.accounts.doctype.gl_entry.gl_entry import validate_balance_type, \
		check_freezing_date, update_outstanding_amt, validate_frozen_account

	if not gl_entries:
		gl_entries = frappe.db.sql("""
			select account, posting_date, party_type, party, cost_center, fiscal_year,voucher_type,
			voucher_no, against_voucher_type, against_voucher, cost_center, company
			from `tabGL Entry2`
			where voucher_type=%s and voucher_no=%s""", (voucher_type, voucher_no), as_dict=True)

	if gl_entries:
		check_freezing_date(gl_entries[0]["posting_date"], adv_adj)
	frappe.db.sql("""delete from `tabGL Entry2` where voucher_type=%s and voucher_no=%s""",
		(voucher_type or gl_entries[0]["voucher_type"], voucher_no or gl_entries[0]["voucher_no"]))

	for entry in gl_entries:
		validate_frozen_account(entry["account"], adv_adj)
		validate_balance_type(entry["account"], adv_adj)
		if not adv_adj:
			validate_expense_against_budget(entry)
		
		if entry.get("against_voucher") and update_outstanding == 'Yes' and not adv_adj:
			update_outstanding_amt(entry["account"], entry.get("party_type"), entry.get("party"), entry.get("against_voucher_type"),
				entry.get("against_voucher"), on_cancel=True)


def get_gl_entries_receipt(self, warehouse_account=None):

		stock_rbnb = self.get_company_default("stock_received_but_not_billed")
		expenses_included_in_valuation = self.get_company_default("expenses_included_in_valuation")

		gl_entries = []
		warehouse_with_no_account = []
		negative_expense_to_be_booked = 0.0
		stock_items = self.get_stock_items()
		for d in self.get("items"):
			if d.item_code in stock_items and flt(d.valuation_rate) and flt(d.qty):
				if warehouse_account.get(d.warehouse):
					stock_value_diff = frappe.db.get_value("Stock Ledger Entry2",
						{"voucher_type": "Purchase Receipt", "voucher_no": self.name,
						"voucher_detail_no": d.name}, "stock_value_difference")
					if not stock_value_diff:
						continue
					gl_entries.append(self.get_gl_dict({
						"account": warehouse_account[d.warehouse]["account"],
						"against": stock_rbnb,
						"cost_center": d.cost_center,
						"remarks": self.get("remarks") or _("Accounting Entry for Stock"),
						"debit": stock_value_diff
					}, warehouse_account[d.warehouse]["account_currency"]))

					# stock received but not billed
					stock_rbnb_currency = get_account_currency(stock_rbnb)
					gl_entries.append(self.get_gl_dict({
						"account": stock_rbnb,
						"against": warehouse_account[d.warehouse]["account"],
						"cost_center": d.cost_center,
						"remarks": self.get("remarks") or _("Accounting Entry for Stock"),
						"credit": flt(d.base_net_amount, d.precision("base_net_amount")),
						"credit_in_account_currency": flt(d.base_net_amount, d.precision("base_net_amount")) \
							if stock_rbnb_currency==self.company_currency else flt(d.net_amount, d.precision("net_amount"))
					}, stock_rbnb_currency))

					negative_expense_to_be_booked += flt(d.item_tax_amount)

					# Amount added through landed-cost-voucher
					if flt(d.landed_cost_voucher_amount):
						gl_entries.append(self.get_gl_dict({
							"account": expenses_included_in_valuation,
							"against": warehouse_account[d.warehouse]["account"],
							"cost_center": d.cost_center,
							"remarks": self.get("remarks") or _("Accounting Entry for Stock"),
							"credit": flt(d.landed_cost_voucher_amount),
							"project": d.project
						}))

					# sub-contracting warehouse
					if flt(d.rm_supp_cost) and warehouse_account.get(self.supplier_warehouse):
						gl_entries.append(self.get_gl_dict({
							"account": warehouse_account[self.supplier_warehouse]["account"],
							"against": warehouse_account[d.warehouse]["account"],
							"cost_center": d.cost_center,
							"remarks": self.get("remarks") or _("Accounting Entry for Stock"),
							"credit": flt(d.rm_supp_cost)
						}, warehouse_account[self.supplier_warehouse]["account_currency"]))

					# divisional loss adjustment
					valuation_amount_as_per_doc = flt(d.base_net_amount, d.precision("base_net_amount")) + \
						flt(d.landed_cost_voucher_amount) + flt(d.rm_supp_cost) + flt(d.item_tax_amount)

					divisional_loss = flt(valuation_amount_as_per_doc - stock_value_diff,
						d.precision("base_net_amount"))

					if divisional_loss:
						if self.is_return or flt(d.item_tax_amount):
							loss_account = expenses_included_in_valuation
						else:
							loss_account = stock_rbnb

						gl_entries.append(self.get_gl_dict({
							"account": loss_account,
							"against": warehouse_account[d.warehouse]["account"],
							"cost_center": d.cost_center,
							"remarks": self.get("remarks") or _("Accounting Entry for Stock"),
							"debit": divisional_loss,
							"project": d.project
						}, stock_rbnb_currency))

				elif d.warehouse not in warehouse_with_no_account or \
					d.rejected_warehouse not in warehouse_with_no_account:
						warehouse_with_no_account.append(d.warehouse)

		self.get_asset_gl_entry(gl_entries)
		# Cost center-wise amount breakup for other charges included for valuation
		valuation_tax = {}
		for tax in self.get("taxes"):
			if tax.category in ("Valuation", "Valuation and Total") and flt(tax.base_tax_amount_after_discount_amount):
				if not tax.cost_center:
					frappe.throw(_("Cost Center is required in row {0} in Taxes table for type {1}").format(tax.idx, _(tax.category)))
				valuation_tax.setdefault(tax.cost_center, 0)
				valuation_tax[tax.cost_center] += \
					(tax.add_deduct_tax == "Add" and 1 or -1) * flt(tax.base_tax_amount_after_discount_amount)

		if negative_expense_to_be_booked and valuation_tax:
			# Backward compatibility:
			# If expenses_included_in_valuation account has been credited in against PI
			# and charges added via Landed Cost Voucher,
			# post valuation related charges on "Stock Received But Not Billed"

			negative_expense_booked_in_pi = frappe.db.sql("""select name from `tabPurchase Invoice Item` pi
				where docstatus = 0 and purchase_receipt=%s
				and exists(select name from `tabGL Entry2` where voucher_type='Purchase Invoice'
					and voucher_no=pi.parent and account=%s)""", (self.name, expenses_included_in_valuation))

			if negative_expense_booked_in_pi:
				expenses_included_in_valuation = stock_rbnb

			against_account = ", ".join([d.account for d in gl_entries if flt(d.debit) > 0])
			total_valuation_amount = sum(valuation_tax.values())
			amount_including_divisional_loss = negative_expense_to_be_booked
			i = 1
			for cost_center, amount in iteritems(valuation_tax):
				if i == len(valuation_tax):
					applicable_amount = amount_including_divisional_loss
				else:
					applicable_amount = negative_expense_to_be_booked * (amount / total_valuation_amount)
					amount_including_divisional_loss -= applicable_amount

				gl_entries.append(
					self.get_gl_dict({
						"account": expenses_included_in_valuation,
						"cost_center": cost_center,
						"credit": applicable_amount,
						"remarks": self.remarks or _("Accounting Entry for Stock"),
						"against": against_account
					})
				)

				i += 1

		if warehouse_with_no_account:
			frappe.msgprint(_("No accounting entries for the following warehouses") + ": \n" +
				"\n".join(warehouse_with_no_account))

		return process_gl_map(gl_entries)


def update_stock_ledger(self):
	sl_entries = []
	import json
	# print(json.dumps())
	print dir(self)
	frappe.throw(str(json.dumps(dir(self))))

	# make sl entries for source warehouse first, then do for target warehouse
	for d in self.get('items'):
		if cstr(d.s_warehouse):
			sl_entries.append(self.get_sl_entries(d, {
				"warehouse": cstr(d.s_warehouse),
				"actual_qty": -flt(d.transfer_qty),
				"incoming_rate": 0
			}))

	for d in self.get('items'):
		if cstr(d.t_warehouse):
			sl_entries.append(self.get_sl_entries(d, {
				"warehouse": cstr(d.t_warehouse),
				"actual_qty": flt(d.transfer_qty),
				"incoming_rate": flt(d.valuation_rate)
			}))

	# On cancellation, make stock ledger entry for
	# target warehouse first, to update serial no values properly

		# if cstr(d.s_warehouse) and self.docstatus == 2:
		# 	sl_entries.append(self.get_sl_entries(d, {
		# 		"warehouse": cstr(d.s_warehouse),
		# 		"actual_qty": -flt(d.transfer_qty),
		# 		"incoming_rate": 0
		# 	}))

	if self.docstatus == 2:
		sl_entries.reverse()

	make_sl_entries_stock(sl_entries, self.amended_from and 'Yes' or 'No')

def make_sl_entries_stock(self, sl_entries, is_amended=None, allow_negative_stock=False,
		via_landed_cost_voucher=False):
	make_sl_entries(sl_entries, is_amended, allow_negative_stock, via_landed_cost_voucher)



def make_sl_entries(sl_entries, is_amended=None, allow_negative_stock=False, via_landed_cost_voucher=False):
	if sl_entries:
		from erpnext.stock.utils import update_bin

		cancel = True if sl_entries[0].get("is_cancelled") == "Yes" else False
		if cancel:
			set_as_cancel(sl_entries[0].get('voucher_no'), sl_entries[0].get('voucher_type'))

		for sle in sl_entries:
			sle_id = None
			if sle.get('is_cancelled') == 'Yes':
				sle['actual_qty'] = -flt(sle['actual_qty'])

			if sle.get("actual_qty") or sle.get("voucher_type")=="Stock Reconciliation":
				sle_id = make_entry(sle, allow_negative_stock, via_landed_cost_voucher)

			args = sle.copy()
			args.update({
				"sle_id": sle_id,
				"is_amended": is_amended
			})
			# update_bin(args, allow_negative_stock, via_landed_cost_voucher)

		if cancel:
			delete_cancelled_entry(sl_entries[0].get('voucher_type'), sl_entries[0].get('voucher_no'))

def set_as_cancel(voucher_type, voucher_no):
	frappe.db.sql("""update `tabStock Ledger Entry2` set is_cancelled='Yes',
		modified=%s, modified_by=%s
		where voucher_no=%s and voucher_type=%s""",
		(now(), frappe.session.user, voucher_type, voucher_no))

# def make_entry(args, allow_negative_stock=False, via_landed_cost_voucher=False):
# 	args.update({"doctype": "Stock Ledger Entry2"})
# 	sle = frappe.get_doc(args)
# 	sle.flags.ignore_permissions = 1
# 	sle.allow_negative_stock=allow_negative_stock
# 	sle.via_landed_cost_voucher = via_landed_cost_voucher
# 	sle.insert()
# 	sle.submit()
# 	return sle.name

def delete_cancelled_entry(voucher_type, voucher_no):
	frappe.db.sql("""delete from `tabStock Ledger Entry2`
		where voucher_type=%s and voucher_no=%s""", (voucher_type, voucher_no))

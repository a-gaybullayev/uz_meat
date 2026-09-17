import frappe
from frappe import _
from frappe.model.document import Document

from group_core.group_core.permissions import cancel_linked_documents
from uz_meat.uz_meat.store_managers import STORE_MANAGERS


class PurchaseProposal(Document):
	def validate(self):
		if not self.requested_by:
			self.requested_by = frappe.session.user

		if self.requesting_company == self.supplying_company:
			frappe.throw(_("Requesting Company и Supplying Company не могут совпадать"))

		if not self.items:
			frappe.throw(_("Добавьте хотя бы одну позицию"))

		for row in self.items:
			if row.qty <= 0:
				frappe.throw(_("Row {0}: количество должно быть больше нуля.").format(row.idx))

		self._validate_store_manager_scope()

	def _validate_store_manager_scope(self):
		"""A store's own manager (Denov / Boysun / Termiz Store Manager) may
		only request purchases for their own store -- not on behalf of a
		different one. Generic UZ MEAT Store Staff, System Manager, and the
		MEAT GOLD-side Warehouse Manager (who only edits during "На
		согласовании") are not store-scoped and are left alone."""
		user_roles = set(frappe.get_roles(frappe.session.user))
		if "System Manager" in user_roles:
			return

		allowed_warehouses = {wh for wh, role in STORE_MANAGERS.items() if role in user_roles}
		if allowed_warehouses and self.requesting_warehouse not in allowed_warehouses:
			frappe.throw(
				_("Вы отвечаете только за {0} и не можете создавать заявки для другого магазина").format(
					", ".join(allowed_warehouses)
				)
			)

	def on_submit(self):
		# Rate is optional while the store is still just proposing what it
		# wants -- MEAT GOLD fills/confirms it during "На согласовании" --
		# but it must be set by the time this is actually confirmed. Checked
		# here rather than in validate(), because docstatus only flips to 1
		# *after* validate() runs, right before this hook fires.
		for row in self.items:
			if not row.rate:
				frappe.throw(_("Row {0}: укажите цену перед подтверждением").format(row.idx))

		si = self._make_sales_invoice()
		self.db_set("sales_invoice", si.name)

		pi = self._make_purchase_invoice()
		self.db_set("purchase_invoice", pi.name)

	def on_cancel(self):
		cancel_linked_documents(
			self, {"sales_invoice": "Sales Invoice", "purchase_invoice": "Purchase Invoice"}
		)

	def _make_sales_invoice(self):
		"""MEAT GOLD's side of the deal: sells from its own warehouse to the
		internal Customer record representing the requesting company."""
		si = frappe.get_doc(
			{
				"doctype": "Sales Invoice",
				"company": self.supplying_company,
				"customer": self.requesting_company,
				"update_stock": 1,
				"posting_date": self.proposal_date,
				"set_posting_time": 1,
				"items": [
					{
						"item_code": row.item_code,
						"qty": row.qty,
						"rate": row.rate,
						"warehouse": self.supplying_warehouse,
					}
					for row in self.items
				],
			}
		)
		si.insert(ignore_permissions=True)
		si.submit()
		return si

	def _make_purchase_invoice(self):
		"""UZ MEAT's side of the same deal: buys into the requesting store's
		own warehouse from the internal Supplier record representing MEAT GOLD.
		Uses the same rate as the Sales Invoice so both companies' books
		agree on the transfer price."""
		pi = frappe.get_doc(
			{
				"doctype": "Purchase Invoice",
				"company": self.requesting_company,
				"supplier": self.supplying_company,
				"update_stock": 1,
				"posting_date": self.proposal_date,
				"set_posting_time": 1,
				"items": [
					{
						"item_code": row.item_code,
						"qty": row.qty,
						"rate": row.rate,
						"warehouse": self.requesting_warehouse,
					}
					for row in self.items
				],
			}
		)
		pi.insert(ignore_permissions=True)
		pi.submit()
		return pi

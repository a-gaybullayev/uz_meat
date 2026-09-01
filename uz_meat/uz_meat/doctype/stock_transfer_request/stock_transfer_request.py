import frappe
from frappe import _
from frappe.model.document import Document


class StockTransferRequest(Document):
	def validate(self):
		if not self.requested_by:
			self.requested_by = frappe.session.user

		if self.from_warehouse == self.to_warehouse:
			frappe.throw(_("From Warehouse и To Warehouse не могут совпадать"))

		if not self.items:
			frappe.throw(_("Добавьте хотя бы одну позицию для перемещения"))

		for row in self.items:
			if row.qty <= 0:
				frappe.throw(_("Row {0}: количество должно быть больше нуля.").format(row.idx))

	def on_submit(self):
		"""Runs when the workflow transitions this request to its terminal
		"approved" state (that transition performs a normal Frappe submit
		under the hood) -- creates and submits the real Stock Entry that
		actually moves the goods."""
		se = self._make_stock_entry()
		se.insert(ignore_permissions=True)
		se.submit()
		self.db_set("stock_entry", se.name)

	def on_cancel(self):
		if self.stock_entry:
			se_docstatus = frappe.db.get_value("Stock Entry", self.stock_entry, "docstatus")
			if se_docstatus == 1:
				se = frappe.get_doc("Stock Entry", self.stock_entry)
				se.cancel()

	def _make_stock_entry(self):
		return frappe.get_doc(
			{
				"doctype": "Stock Entry",
				"stock_entry_type": "Material Transfer",
				"company": self.company,
				"posting_date": self.transfer_date,
				"items": [
					{
						"item_code": row.item_code,
						"qty": row.qty,
						"uom": row.uom,
						"s_warehouse": self.from_warehouse,
						"t_warehouse": self.to_warehouse,
					}
					for row in self.items
				],
			}
		)

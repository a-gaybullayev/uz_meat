import frappe
from frappe.model.workflow import apply_workflow
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today


class TestPurchaseProposal(FrappeTestCase):
	def setUp(self):
		self.item = self._get_or_create_item("TEST-PP-ITEM-001")
		self._ensure_stock(self.item, "Asosiy Ombor - MG", "MEAT GOLD", 100)

	def _get_or_create_item(self, item_code):
		if not frappe.db.exists("Item", item_code):
			frappe.get_doc(
				{
					"doctype": "Item",
					"item_code": item_code,
					"item_name": "Test Purchase Proposal Item",
					"item_group": "All Item Groups",
					"stock_uom": "Nos",
					"is_stock_item": 1,
				}
			).insert(ignore_permissions=True)
		return item_code

	def _ensure_stock(self, item_code, warehouse, company, qty):
		se = frappe.get_doc(
			{
				"doctype": "Stock Entry",
				"stock_entry_type": "Material Receipt",
				"company": company,
				"items": [
					{"item_code": item_code, "qty": qty, "uom": "Nos", "t_warehouse": warehouse, "basic_rate": 1}
				],
			}
		)
		se.insert(ignore_permissions=True)
		se.submit()

	def _make_proposal(self, rate=50000):
		pp = frappe.get_doc(
			{
				"doctype": "Purchase Proposal",
				"proposal_date": today(),
				"requesting_company": "UZ MEAT",
				"requesting_warehouse": "Denov - UM",
				"supplying_company": "MEAT GOLD",
				"supplying_warehouse": "Asosiy Ombor - MG",
				"items": [{"item_code": self.item, "qty": 10, "rate": rate}],
			}
		)
		pp.insert(ignore_permissions=True)
		return pp

	def test_submit_creates_matching_sales_and_purchase_invoice(self):
		pp = self._make_proposal()
		pp.submit()

		self.assertTrue(pp.sales_invoice)
		self.assertTrue(pp.purchase_invoice)

		si = frappe.get_doc("Sales Invoice", pp.sales_invoice)
		self.assertEqual(si.docstatus, 1)
		self.assertEqual(si.company, "MEAT GOLD")
		self.assertEqual(si.customer, "UZ MEAT")
		self.assertEqual(si.items[0].item_code, self.item)
		self.assertEqual(si.items[0].qty, 10)
		self.assertEqual(si.items[0].warehouse, "Asosiy Ombor - MG")

		pi = frappe.get_doc("Purchase Invoice", pp.purchase_invoice)
		self.assertEqual(pi.docstatus, 1)
		self.assertEqual(pi.company, "UZ MEAT")
		self.assertEqual(pi.supplier, "MEAT GOLD")
		self.assertEqual(pi.items[0].item_code, self.item)
		self.assertEqual(pi.items[0].qty, 10)
		self.assertEqual(pi.items[0].warehouse, "Denov - UM")

		# Both sides must agree on the transfer price.
		self.assertEqual(si.items[0].rate, pi.items[0].rate)

		pp.cancel()
		si.reload()
		pi.reload()
		self.assertEqual(si.docstatus, 2)
		self.assertEqual(pi.docstatus, 2)

	def test_cannot_confirm_without_rate(self):
		pp = self._make_proposal(rate=0)
		self.assertRaises(frappe.ValidationError, pp.submit)

	def test_same_company_on_both_sides_rejected(self):
		pp = frappe.get_doc(
			{
				"doctype": "Purchase Proposal",
				"proposal_date": today(),
				"requesting_company": "UZ MEAT",
				"requesting_warehouse": "Denov - UM",
				"supplying_company": "UZ MEAT",
				"supplying_warehouse": "Boysun - UM",
				"items": [{"item_code": self.item, "qty": 1, "rate": 100}],
			}
		)
		self.assertRaises(frappe.ValidationError, pp.insert, ignore_permissions=True)


class TestPurchaseProposalWorkflow(FrappeTestCase):
	def setUp(self):
		self.item = self._get_or_create_item("TEST-PP-WF-ITEM-001")
		self._ensure_stock(self.item, "Asosiy Ombor - MG", "MEAT GOLD", 100)

		self.store_staff = self._get_or_create_user(
			"store.staff.pp.test@uzmeat.local", "UZ MEAT Store Staff"
		)
		self.warehouse_manager = self._get_or_create_user(
			"warehouse.manager.pp.test@meatgold.local", "Warehouse Manager"
		)

	def tearDown(self):
		frappe.set_user("Administrator")

	def _get_or_create_item(self, item_code):
		if not frappe.db.exists("Item", item_code):
			frappe.get_doc(
				{
					"doctype": "Item",
					"item_code": item_code,
					"item_name": "Test PP Workflow Item",
					"item_group": "All Item Groups",
					"stock_uom": "Nos",
					"is_stock_item": 1,
				}
			).insert(ignore_permissions=True)
		return item_code

	def _ensure_stock(self, item_code, warehouse, company, qty):
		se = frappe.get_doc(
			{
				"doctype": "Stock Entry",
				"stock_entry_type": "Material Receipt",
				"company": company,
				"items": [
					{"item_code": item_code, "qty": qty, "uom": "Nos", "t_warehouse": warehouse, "basic_rate": 1}
				],
			}
		)
		se.insert(ignore_permissions=True)
		se.submit()

	def _get_or_create_user(self, email, role):
		if not frappe.db.exists("User", email):
			frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": email.split(".")[0].title(),
					"send_welcome_email": 0,
					"user_type": "System User",
					"roles": [{"role": role}],
				}
			).insert(ignore_permissions=True)
		return email

	def test_store_staff_cannot_confirm_own_proposal(self):
		frappe.set_user(self.store_staff)
		pp = frappe.get_doc(
			{
				"doctype": "Purchase Proposal",
				"proposal_date": today(),
				"requesting_company": "UZ MEAT",
				"requesting_warehouse": "Denov - UM",
				"supplying_company": "MEAT GOLD",
				"supplying_warehouse": "Asosiy Ombor - MG",
				"items": [{"item_code": self.item, "qty": 5, "rate": 1000}],
			}
		)
		pp.insert(ignore_permissions=True)
		apply_workflow(pp, "Отправить на согласование")

		# Store staff has no "Подтвердить" transition available at all.
		from frappe.model.workflow import WorkflowTransitionError

		with self.assertRaises(WorkflowTransitionError):
			apply_workflow(pp, "Подтвердить")

	def test_warehouse_manager_can_set_rate_and_confirm(self):
		frappe.set_user(self.store_staff)
		pp = frappe.get_doc(
			{
				"doctype": "Purchase Proposal",
				"proposal_date": today(),
				"requesting_company": "UZ MEAT",
				"requesting_warehouse": "Denov - UM",
				"supplying_company": "MEAT GOLD",
				"supplying_warehouse": "Asosiy Ombor - MG",
				"items": [{"item_code": self.item, "qty": 5}],
			}
		)
		pp.insert(ignore_permissions=True)
		apply_workflow(pp, "Отправить на согласование")

		frappe.set_user(self.warehouse_manager)
		pp = frappe.get_doc("Purchase Proposal", pp.name)
		pp.items[0].rate = 45000
		pp.save(ignore_permissions=True)
		apply_workflow(pp, "Подтвердить")

		pp.reload()
		self.assertEqual(pp.docstatus, 1)
		self.assertEqual(pp.workflow_state, "Подтверждено")
		self.assertTrue(pp.sales_invoice)
		self.assertTrue(pp.purchase_invoice)

	def test_store_manager_can_request_for_own_store(self):
		denau_manager = self._get_or_create_user(
			"denau.manager.pp.test@uzmeat.local", "Denov Store Manager"
		)
		frappe.set_user(denau_manager)
		pp = frappe.get_doc(
			{
				"doctype": "Purchase Proposal",
				"proposal_date": today(),
				"requesting_company": "UZ MEAT",
				"requesting_warehouse": "Denov - UM",
				"supplying_company": "MEAT GOLD",
				"supplying_warehouse": "Asosiy Ombor - MG",
				"items": [{"item_code": self.item, "qty": 5, "rate": 1000}],
			}
		)
		pp.insert(ignore_permissions=True)
		self.assertEqual(pp.requesting_warehouse, "Denov - UM")

	def test_store_manager_cannot_request_for_another_store(self):
		denau_manager = self._get_or_create_user(
			"denau.manager.pp.test@uzmeat.local", "Denov Store Manager"
		)
		frappe.set_user(denau_manager)
		pp = frappe.get_doc(
			{
				"doctype": "Purchase Proposal",
				"proposal_date": today(),
				"requesting_company": "UZ MEAT",
				"requesting_warehouse": "Boysun - UM",
				"supplying_company": "MEAT GOLD",
				"supplying_warehouse": "Asosiy Ombor - MG",
				"items": [{"item_code": self.item, "qty": 5, "rate": 1000}],
			}
		)
		self.assertRaises(frappe.ValidationError, pp.insert, ignore_permissions=True)

import frappe
from frappe.model.workflow import WorkflowTransitionError, apply_workflow
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today


class TestStockTransferRequest(FrappeTestCase):
	def setUp(self):
		self.company = "UZ MEAT"
		self.from_wh = "Boysun - UM"
		self.to_wh = "Denov - UM"
		self.item = self._get_or_create_item("TEST-UZM-ITEM-001")
		self._ensure_stock(self.item, self.from_wh, 100)

	def tearDown(self):
		frappe.set_user("Administrator")

	def _get_or_create_item(self, item_code):
		if not frappe.db.exists("Item", item_code):
			frappe.get_doc(
				{
					"doctype": "Item",
					"item_code": item_code,
					"item_name": "Test UZ MEAT Item",
					"item_group": "All Item Groups",
					"stock_uom": "Nos",
					"is_stock_item": 1,
				}
			).insert(ignore_permissions=True)
		return item_code

	def _ensure_stock(self, item_code, warehouse, qty):
		se = frappe.get_doc(
			{
				"doctype": "Stock Entry",
				"stock_entry_type": "Material Receipt",
				"company": self.company,
				"items": [
					{"item_code": item_code, "qty": qty, "uom": "Nos", "t_warehouse": warehouse, "basic_rate": 1}
				],
			}
		)
		se.insert(ignore_permissions=True)
		se.submit()

	def _make_request(self, from_wh, to_wh, qty=5):
		req = frappe.get_doc(
			{
				"doctype": "Stock Transfer Request",
				"transfer_date": today(),
				"company": self.company,
				"from_warehouse": from_wh,
				"to_warehouse": to_wh,
				"items": [{"item_code": self.item, "qty": qty}],
			}
		)
		req.insert(ignore_permissions=True)
		return req

	def test_submit_creates_material_transfer_stock_entry(self):
		req = self._make_request(self.from_wh, self.to_wh)
		req.submit()

		self.assertTrue(req.stock_entry)
		se = frappe.get_doc("Stock Entry", req.stock_entry)
		self.assertEqual(se.docstatus, 1)
		self.assertEqual(se.stock_entry_type, "Material Transfer")
		self.assertEqual(len(se.items), 1)
		self.assertEqual(se.items[0].s_warehouse, self.from_wh)
		self.assertEqual(se.items[0].t_warehouse, self.to_wh)

		req.cancel()
		se.reload()
		self.assertEqual(se.docstatus, 2)

	def test_cannot_transfer_to_same_warehouse(self):
		req = frappe.get_doc(
			{
				"doctype": "Stock Transfer Request",
				"transfer_date": today(),
				"company": self.company,
				"from_warehouse": self.from_wh,
				"to_warehouse": self.from_wh,
				"items": [{"item_code": self.item, "qty": 1}],
			}
		)
		self.assertRaises(frappe.ValidationError, req.insert, ignore_permissions=True)

	def test_store_to_store_transfer_allowed(self):
		# Direct transfer between two store warehouses -- the only kind of
		# transfer left now that there is no shared UZ MEAT hub warehouse.
		req = self._make_request("Denov - UM", "Termiz - UM")
		self._ensure_stock(self.item, "Denov - UM", 10)
		req.submit()
		se = frappe.get_doc("Stock Entry", req.stock_entry)
		self.assertEqual(se.items[0].s_warehouse, "Denov - UM")
		self.assertEqual(se.items[0].t_warehouse, "Termiz - UM")


class TestStockTransferRequestWorkflowApproval(FrappeTestCase):
	"""Confirms the core business requirement: only the manager of the
	*receiving* warehouse can approve a transfer into it -- another
	warehouse's manager must not be able to."""

	def setUp(self):
		self.company = "UZ MEAT"
		self.item = self._get_or_create_item("TEST-UZM-WF-ITEM-001")
		self._ensure_stock(self.item, "Boysun - UM", 100)

		self.denau_manager = self._get_or_create_user(
			"denau.manager.test@uzmeat.local", "Denov Store Manager"
		)
		self.termez_manager = self._get_or_create_user(
			"termez.manager.test@uzmeat.local", "Termiz Store Manager"
		)
		self.store_staff = self._get_or_create_user(
			"store.staff.test@uzmeat.local", "UZ MEAT Store Staff"
		)

	def tearDown(self):
		frappe.set_user("Administrator")

	def _get_or_create_item(self, item_code):
		if not frappe.db.exists("Item", item_code):
			frappe.get_doc(
				{
					"doctype": "Item",
					"item_code": item_code,
					"item_name": "Test UZ MEAT Workflow Item",
					"item_group": "All Item Groups",
					"stock_uom": "Nos",
					"is_stock_item": 1,
				}
			).insert(ignore_permissions=True)
		return item_code

	def _ensure_stock(self, item_code, warehouse, qty):
		se = frappe.get_doc(
			{
				"doctype": "Stock Entry",
				"stock_entry_type": "Material Receipt",
				"company": self.company,
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

	def _make_request(self, to_wh):
		frappe.set_user(self.store_staff)
		req = frappe.get_doc(
			{
				"doctype": "Stock Transfer Request",
				"transfer_date": today(),
				"company": self.company,
				"from_warehouse": "Boysun - UM",
				"to_warehouse": to_wh,
				"items": [{"item_code": self.item, "qty": 1}],
			}
		)
		req.insert(ignore_permissions=True)
		apply_workflow(req, "Отправить на согласование")
		return req.name

	def test_wrong_warehouse_manager_cannot_approve(self):
		req_name = self._make_request("Denov - UM")

		frappe.set_user(self.termez_manager)
		req = frappe.get_doc("Stock Transfer Request", req_name)
		# The Termez manager's own "Утвердить" transition row exists but its
		# condition (to_warehouse == "Termiz - UM") doesn't match this
		# request's to_warehouse ("Denov - UM"), so Frappe reports no valid
		# transition at all for this user rather than a bare permission
		# error -- that's the actual, correct behavior to guard against.
		with self.assertRaises(WorkflowTransitionError):
			apply_workflow(req, "Утвердить")

	def test_correct_warehouse_manager_can_approve(self):
		req_name = self._make_request("Denov - UM")

		frappe.set_user(self.denau_manager)
		req = frappe.get_doc("Stock Transfer Request", req_name)
		apply_workflow(req, "Утвердить")

		req.reload()
		self.assertEqual(req.docstatus, 1)
		self.assertEqual(req.workflow_state, "Утверждено")
		self.assertTrue(req.stock_entry)

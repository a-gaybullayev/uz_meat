import frappe


def execute():
	"""UOM read access on this site is intentionally locked down (via
	property_manager's Custom DocPerm hardening) to a handful of stock/
	accounting roles. Cashiers need it too -- POS Awesome reads UOM records
	while building the item list -- so grant it narrowly to our own
	UZ MEAT Store Staff role instead of widening a broad, cross-company role
	like Sales User."""
	role = "UZ MEAT Store Staff"
	if frappe.db.exists("Custom DocPerm", {"parent": "UOM", "role": role}):
		return

	frappe.get_doc(
		{
			"doctype": "Custom DocPerm",
			"parent": "UOM",
			"parenttype": "DocType",
			"parentfield": "permissions",
			"role": role,
			"read": 1,
		}
	).insert(ignore_permissions=True)

import frappe

from uz_meat.uz_meat.store_managers import STORE_MANAGERS

# Purchase Proposal has TWO Link-to-Warehouse fields (requesting_warehouse,
# supplying_warehouse) with opposite scoping needs -- a store manager's own
# warehouse for one, MEAT GOLD's warehouse for the other. A declarative
# User Permission on Warehouse can't express "restrict only this one field":
# Frappe's own permission-query builder generates one match condition per
# Link-to-Warehouse field on the doctype and ANDs them together, so
# restricting a store manager to their own warehouse that way made
# `supplying_warehouse` (always MEAT GOLD's) fail the same condition and
# hid every proposal, including their own -- confirmed by testing a real
# User Permission before writing this. Hence a purpose-built query
# condition on requesting_warehouse specifically, same shape as
# property_manager/property_management/permissions.py's own
# get_permission_query_conditions().


def _allowed_warehouses(user):
	roles = frappe.get_roles(user)
	if "System Manager" in roles:
		return None
	return {wh for wh, role in STORE_MANAGERS.items() if role in roles}


def get_permission_query_conditions(user, doctype=None):
	"""Restricts the Purchase Proposal list to a store manager's own
	requesting_warehouse. Returns "" (no restriction) for System Manager,
	and for anyone NOT holding one of the three store-manager roles (UZ
	MEAT Store Staff, Warehouse Manager) -- matches
	PurchaseProposal._validate_store_manager_scope()'s own docstring: those
	roles are deliberately not store-scoped."""
	allowed = _allowed_warehouses(user)
	if not allowed:
		return ""
	values = ", ".join(frappe.db.escape(wh) for wh in allowed)
	return f"`tabPurchase Proposal`.requesting_warehouse in ({values})"


def has_permission(doc, user):
	allowed = _allowed_warehouses(user)
	if not allowed:
		return True
	return doc.get("requesting_warehouse") in allowed

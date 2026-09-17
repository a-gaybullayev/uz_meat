import json

import frappe

# Stock Transfer Request has zero real records in the live database
# (confirmed directly against tabStock Transfer Request before writing
# this patch) -- Purchase Proposal is the only inter-company movement
# path that has ever actually been used, and it's the only one that
# produces a real Sales Invoice + Purchase Invoice (debt/books trail).
# Stock Transfer Request only ever produced a bare Stock Entry with no
# invoice on either side. With no data to migrate, now is the cheapest
# point to retire it -- so create is revoked for every store-facing role.
#
# Stock Transfer Request currently has ZERO Custom DocPerm rows. Adding
# a Custom DocPerm row for even one role triggers Frappe's exclusivity
# trap (frappe/permissions.py: get_valid_perms() drops ALL standard
# DocPerm roles for a doctype the instant it has ANY Custom DocPerm row).
# So every role that currently has a standard DocPerm row here needs an
# explicit Custom DocPerm row too, cloning its exact existing flags --
# not just the roles being narrowed.
#
# read/report are kept 1 everywhere: if a Stock Transfer Request is ever
# created another way (API, future data import), it must stay visible
# rather than becoming an orphaned, invisible record.
#
# submit is dropped alongside create for the three store-manager roles,
# same reasoning as narrow_warehouse_manager_sales_invoice_access.py in
# property_manager: unreachable anyway once create=0, since there will
# never again be a draft for those roles to submit.

DOCTYPE = "Stock Transfer Request"

ROLES = {
	"System Manager": dict(
		read=1, write=1, create=1, submit=1, cancel=1, amend=1, delete=1,
		email=1, export=1, print=1, report=1, share=1,
	),
	"UZ MEAT Store Staff": dict(
		read=1, write=1, create=0,
		email=1, export=1, print=1, report=1, share=1,
	),
	"Менеджер Денау": dict(
		read=1, write=1, create=0, submit=0, cancel=1, amend=1, delete=1,
		email=1, export=1, print=1, report=1, share=1,
	),
	"Менеджер Байсуна": dict(
		read=1, write=1, create=0, submit=0, cancel=1, amend=1, delete=1,
		email=1, export=1, print=1, report=1, share=1,
	),
	"Менеджер Термеза": dict(
		read=1, write=1, create=0, submit=0, cancel=1, amend=1, delete=1,
		email=1, export=1, print=1, report=1, share=1,
	),
}

# Workspaces that currently show a "Stock Transfer Request" shortcut +
# list link -- confirmed by grepping the JSON fixtures for the store-role
# workspaces before writing this patch.
WORKSPACES = ["Менеджер Денау", "Менеджер Байсуна", "Менеджер Термеза", "Кассир"]


def execute():
	for role, flags in ROLES.items():
		if not frappe.db.exists("Role", role):
			continue
		_ensure_custom_docperm(role, flags)

	for workspace in WORKSPACES:
		_remove_stock_transfer_shortcut(workspace)

	frappe.clear_cache()


def _ensure_custom_docperm(role, flags):
	existing = frappe.db.exists("Custom DocPerm", {"parent": DOCTYPE, "role": role})
	if existing:
		doc = frappe.get_doc("Custom DocPerm", existing)
		for field, value in flags.items():
			doc.set(field, value)
		doc.save(ignore_permissions=True)
		return

	doc = frappe.get_doc(
		{
			"doctype": "Custom DocPerm",
			"parent": DOCTYPE,
			"parenttype": "DocType",
			"parentfield": "permissions",
			"role": role,
			"permlevel": 0,
			**flags,
		}
	)
	doc.insert(ignore_permissions=True)


def _remove_stock_transfer_shortcut(workspace_name):
	"""Drop the Stock Transfer Request shortcut/list-link/layout-block from
	a store workspace. Edits the live Workspace doc directly (like
	property_manager's v1_20 fix_workspace_file_sync) rather than relying
	on JSON-fixture auto-sync -- Workspace.on_update() only exports
	DB -> file, not the other way round, so a patch is the only thing that
	reliably fixes an already-migrated site."""
	if not frappe.db.exists("Workspace", workspace_name):
		return

	doc = frappe.get_doc("Workspace", workspace_name)
	changed = False

	shortcuts_before = len(doc.shortcuts)
	doc.shortcuts = [s for s in doc.shortcuts if s.label != "Stock Transfer Request"]
	changed = changed or len(doc.shortcuts) != shortcuts_before

	links_before = len(doc.links)
	doc.links = [l for l in doc.links if l.label != "Stock Transfer Request"]
	changed = changed or len(doc.links) != links_before

	if doc.content:
		blocks = json.loads(doc.content)
		filtered_blocks = [
			b
			for b in blocks
			if not (
				b.get("type") == "shortcut"
				and b.get("data", {}).get("shortcut_name") == "Stock Transfer Request"
			)
		]
		if len(filtered_blocks) != len(blocks):
			doc.content = json.dumps(filtered_blocks)
			changed = True

	if not changed:
		return

	doc.save(ignore_permissions=True)

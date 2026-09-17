import frappe

# Purchase Proposal is our own doctype -- no other consumer claims
# in_standard_filter on it the way POS Awesome does on Sales Invoice, so
# the separate "Purchase Proposals" Query Report is no longer needed: the
# doctype's own List View now carries in_list_view/in_standard_filter
# directly (requesting_warehouse, proposal_date, workflow_state), with a
# default "На согласовании" filter via purchase_proposal_list.js. The
# report's files have been removed from uz_meat/report/purchase_proposals/;
# this patch removes the already-migrated DB record.

REPORT_NAME = "Purchase Proposals"


def execute():
	if frappe.db.exists("Report", REPORT_NAME):
		frappe.delete_doc("Report", REPORT_NAME, ignore_permissions=True, force=True)

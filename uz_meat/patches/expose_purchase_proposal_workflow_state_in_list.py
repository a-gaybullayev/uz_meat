import frappe

# workflow_state is auto-created as a HIDDEN Custom Field by the Workflow
# framework the first time a Workflow targeting this doctype is created
# (see patches/create_purchase_proposal_workflow.py, workflow_state_field=
# "workflow_state") -- it's meant to drive the workflow machinery, not to
# be seen. We now want it as a real List View column + sidebar filter (the
# "На согласовании" queue), which just means un-hiding that same field and
# flagging it -- Purchase Proposal is our own doctype, no other consumer
# relies on its Custom Field staying hidden.

DOCTYPE = "Purchase Proposal"
FIELDNAME = "workflow_state"


def execute():
	name = frappe.db.exists("Custom Field", {"dt": DOCTYPE, "fieldname": FIELDNAME})
	if not name:
		return

	doc = frappe.get_doc("Custom Field", name)
	doc.hidden = 0
	doc.in_list_view = 1
	doc.in_standard_filter = 1
	doc.save(ignore_permissions=True)

	frappe.clear_cache(doctype=DOCTYPE)

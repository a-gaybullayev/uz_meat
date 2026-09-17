import frappe

from uz_meat.uz_meat.store_managers import STORE_MANAGERS as WAREHOUSE_APPROVERS

STATES = [
	# (state, doc_status, allow_edit_role) -- allow_edit is mandatory on
	# Workflow Document State, so states other than the draft are locked to
	# System Manager (no direct field edits once a request is in play; only
	# the workflow actions -- approve/reject -- can move it forward).
	("Черновик", "0", "UZ MEAT Store Staff"),
	("На согласовании", "0", "System Manager"),
	("Утверждено", "1", "System Manager"),
	("Отклонено", "0", "System Manager"),
]

ACTIONS = ["Отправить на согласование", "Утвердить", "Отклонить"]


def execute():
	_ensure_workflow_states()
	_ensure_workflow_actions()
	_ensure_workflow()


def _ensure_workflow_states():
	for state, *_rest in STATES:
		if not frappe.db.exists("Workflow State", state):
			frappe.get_doc({"doctype": "Workflow State", "workflow_state_name": state}).insert(
				ignore_permissions=True
			)


def _ensure_workflow_actions():
	for action in ACTIONS:
		if not frappe.db.exists("Workflow Action Master", action):
			frappe.get_doc({"doctype": "Workflow Action Master", "workflow_action_name": action}).insert(
				ignore_permissions=True
			)


def _ensure_workflow():
	workflow_name = "Stock Transfer Approval"
	if frappe.db.exists("Workflow", workflow_name):
		return

	states = [
		{
			"state": state,
			"doc_status": doc_status,
			"allow_edit": allow_edit_role,
		}
		for state, doc_status, allow_edit_role in STATES
	]

	transitions = [
		# Draft -> Pending: any store staff, or System Manager
		{
			"state": "Черновик",
			"action": "Отправить на согласование",
			"next_state": "На согласовании",
			"allowed": "UZ MEAT Store Staff",
		},
		{
			"state": "Черновик",
			"action": "Отправить на согласование",
			"next_state": "На согласовании",
			"allowed": "System Manager",
		},
	]

	for warehouse, role in WAREHOUSE_APPROVERS.items():
		# Approve / Reject are only allowed if this transition's role matches
		# the manager of the request's OWN to_warehouse -- this is what makes
		# "the receiving warehouse's manager approves" actually enforced,
		# not just a naming convention.
		condition = f'doc.to_warehouse == "{warehouse}"'
		transitions.append(
			{
				"state": "На согласовании",
				"action": "Утвердить",
				"next_state": "Утверждено",
				"allowed": role,
				"condition": condition,
			}
		)
		transitions.append(
			{
				"state": "На согласовании",
				"action": "Отклонить",
				"next_state": "Отклонено",
				"allowed": role,
				"condition": condition,
			}
		)

	# System Manager can always override, regardless of warehouse.
	transitions.append(
		{
			"state": "На согласовании",
			"action": "Утвердить",
			"next_state": "Утверждено",
			"allowed": "System Manager",
		}
	)
	transitions.append(
		{
			"state": "На согласовании",
			"action": "Отклонить",
			"next_state": "Отклонено",
			"allowed": "System Manager",
		}
	)

	frappe.get_doc(
		{
			"doctype": "Workflow",
			"workflow_name": workflow_name,
			"document_type": "Stock Transfer Request",
			"is_active": 1,
			"override_status": 1,
			"workflow_state_field": "workflow_state",
			"states": states,
			"transitions": transitions,
		}
	).insert(ignore_permissions=True)

import frappe

# States reuse the same "Черновик" state created by
# create_stock_transfer_workflow.py where possible; only the states unique
# to this workflow are created here.
STATES = [
	# (state, doc_status, allow_edit_role)
	("Черновик", "0", "UZ MEAT Store Staff"),
	("На согласовании", "0", "Warehouse Manager"),
	("Подтверждено", "1", "System Manager"),
	("Отклонено", "0", "System Manager"),
]

ACTIONS = ["Отправить на согласование", "Подтвердить", "Отклонить"]


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
	workflow_name = "Purchase Proposal Approval"
	if frappe.db.exists("Workflow", workflow_name):
		return

	states = [
		{"state": state, "doc_status": doc_status, "allow_edit": allow_edit_role}
		for state, doc_status, allow_edit_role in STATES
	]

	transitions = [
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
		{
			# The MEAT GOLD side confirms availability and price (editable
			# while in "На согласовании", see allow_edit above) before
			# committing to the deal.
			"state": "На согласовании",
			"action": "Подтвердить",
			"next_state": "Подтверждено",
			"allowed": "Warehouse Manager",
		},
		{
			"state": "На согласовании",
			"action": "Подтвердить",
			"next_state": "Подтверждено",
			"allowed": "System Manager",
		},
		{
			"state": "На согласовании",
			"action": "Отклонить",
			"next_state": "Отклонено",
			"allowed": "Warehouse Manager",
		},
		{
			"state": "На согласовании",
			"action": "Отклонить",
			"next_state": "Отклонено",
			"allowed": "System Manager",
		},
	]

	frappe.get_doc(
		{
			"doctype": "Workflow",
			"workflow_name": workflow_name,
			"document_type": "Purchase Proposal",
			"is_active": 1,
			"override_status": 1,
			"workflow_state_field": "workflow_state",
			"states": states,
			"transitions": transitions,
		}
	).insert(ignore_permissions=True)

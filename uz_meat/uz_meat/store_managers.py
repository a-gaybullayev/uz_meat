"""Single source of truth for "which role is responsible for which UZ MEAT
store warehouse". Used by:
  - patches/create_stock_transfer_workflow.py (who can approve a transfer
    INTO that store)
  - doctype/purchase_proposal/purchase_proposal.py (a store manager may only
    request purchases FOR their own store, not on behalf of another one)
"""

STORE_MANAGERS = {
	"Denov - UM": "Denov Store Manager",
	"Boysun - UM": "Boysun Store Manager",
	"Termiz - UM": "Termiz Store Manager",
}

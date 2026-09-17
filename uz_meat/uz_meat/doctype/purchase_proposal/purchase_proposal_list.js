frappe.listview_settings["Purchase Proposal"] = {
	// Default queue on first open, matching the old "Purchase Proposals"
	// Query Report's default filter -- adjustable by the user afterwards,
	// same as any other List View default filter (e.g. core Production
	// Plan's `filters: [["status", "!=", "Closed"]]`).
	filters: [["workflow_state", "=", "На согласовании"]],

	get_indicator: function (doc) {
		const colors = {
			"Черновик": "gray",
			"На согласовании": "orange",
			"Подтверждено": "green",
			"Отклонено": "red",
		};
		const color = colors[doc.workflow_state] || "gray";
		return [__(doc.workflow_state), color, "workflow_state,=," + doc.workflow_state];
	},
};

frappe.ui.form.on("Purchase Proposal", {
    onload: function (frm) {
        frm.set_query("requesting_warehouse", function () {
            return {
                filters: {
                    company: frm.doc.requesting_company,
                    is_group: 0
                }
            };
        });
        frm.set_query("supplying_warehouse", function () {
            return {
                filters: {
                    company: frm.doc.supplying_company,
                    is_group: 0
                }
            };
        });
    }
});

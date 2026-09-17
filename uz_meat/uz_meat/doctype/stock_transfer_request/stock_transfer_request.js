frappe.ui.form.on("Stock Transfer Request", {
    onload: function (frm) {
        ["from_warehouse", "to_warehouse"].forEach(function (fieldname) {
            frm.set_query(fieldname, function () {
                return {
                    filters: {
                        company: frm.doc.company,
                        is_group: 0
                    }
                };
            });
        });
    }
});

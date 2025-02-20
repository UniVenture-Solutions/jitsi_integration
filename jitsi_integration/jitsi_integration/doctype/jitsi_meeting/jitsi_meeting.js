// Copyright (c) 2025, Khizer Saeed and contributors
// For license information, please see license.txt

frappe.ui.form.on("JitSi Meeting", {
	refresh(frm) {
        if(!frm.doc.__islocal) {
            frm.add_custom_button(__("Go to Meet"), function() {
                frappe.call({
                    method: "go_to_meeting",
                    doc: frm.doc,
                    callback(r) {
                        if(r.message[0] && r.message[1]) {
                            window.location.href = r.message[1];
                        } else {
                            frappe.throw(r.message[1]);
                        }
                    }
                })
            });
        }
	}
});

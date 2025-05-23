// Copyright (c) 2025, Khizer Saeed and contributors
// For license information, please see license.txt

frappe.ui.form.on("JitSi Settings", {
	generate_key(frm) {
        frappe.call({
            method: "jitsi_integration.utils.jitsi_utils.generate_encryption_key",
            callback(r) {
                if (r.message) {
                    frm.set_value("encryption_key", r.message);
                    frm.save();
                }
            }
        });
	},
});

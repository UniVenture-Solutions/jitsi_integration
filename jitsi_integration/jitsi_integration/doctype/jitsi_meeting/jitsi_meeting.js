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

            frm.add_custom_button(__("Invite"), function() {
                let d = new frappe.ui.Dialog({
                    title: 'How would you like to invite users?',
                    fields: [
                        {
                            label: 'Mode',
                            fieldname: 'mode',
                            fieldtype: 'Select',
                            options: ["Email", "Mattermost"],
                            default: "Email",
                            reqd: 1
                        },
                    ],
                    size: 'small',
                    primary_action_label: 'Confirm',
                    primary_action(values) {
                        frappe.call({
                            method: "send_invitation",
                            doc: frm.doc,
                            freeze: true,
                            freeze_message: "Sending invitation...",
                            args: {
                                domain: window.location.origin,
                                user_invitation_mode: values.mode.toLowerCase()
                            },
                            callback(r) {
                                if(r.message) {
                                    frappe.msgprint("Invitation sent successfully");
                                    setTimeout(() => {
                                        frm.set_value("status", "Invited");
                                        frm.save();
                                    }, 1000);
                                }
                            }
                        })
                        d.hide();
                    }
                });
                
                d.show();
            });
            
        }
	},
    from_datetime(frm) {
        if(frm.doc.from_datetime && frm.doc.to_datetime) {
            let from = new Date(frm.doc.from_datetime);
            let to = new Date(frm.doc.to_datetime);
            if(from > to) {
                frappe.msgprint("From datetime should be less than to datetime");
                frm.set_value("from_datetime", "");
            }
        }
    },
    to_datetime(frm) {
        if(frm.doc.from_datetime && frm.doc.to_datetime) {
            let from = new Date(frm.doc.from_datetime);
            let to = new Date(frm.doc.to_datetime);
            if(from > to) {
                frappe.msgprint("From datetime should be less than to datetime");
                frm.set_value("to_datetime", "");
            }
        }
    },
});

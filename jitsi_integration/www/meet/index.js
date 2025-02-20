window.addEventListener("DOMContentLoaded", function() {
    let redirectLink = document.querySelector(".redirect-link");
    if (redirectLink) {
        let currentPath = encodeURIComponent(window.location.pathname + window.location.search);
        redirectLink.href = `/login?redirect-to=${currentPath}#login`;
    }

    frappe.ready(function() {
        if (frappe.session.user && frappe.session.user !== "Guest") {
            const urlParams = new URLSearchParams(window.location.search);
            const roomName = urlParams.get('room');
            const message = document.querySelector(".primary-heading");
            if (!roomName) {
                message.textContent = "No room name provided";
                return;
            }
            
            frappe.call({
                method: "jitsi_integration.www.meet.index.get_jitsi_meeting_url",
                args: {
                    room: roomName
                },
                callback(r) {
                    if(r.message[0] && r.message[1]) {
                        window.location.href = r.message[1];
                    } else {
                        message.textContent = r.message[1];
                    }
                }
            })
        }
    })
})

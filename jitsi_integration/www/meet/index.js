window.addEventListener("DOMContentLoaded", function() {
    let redirectLink = document.querySelector(".redirect-link");
    const mainBody = document.querySelector(".title-body");
    const unauthorized = document.querySelector(".unauthorized");

    if (redirectLink) {
        let currentPath = encodeURIComponent(window.location.pathname + window.location.search);
        redirectLink.href = `/login?redirect-to=${currentPath}#login`;
    }

    frappe.ready(function() {
        const urlParams = new URLSearchParams(window.location.search);
        const roomName = urlParams.get('room');
        const guest = urlParams.get('guest');

        if(!guest && frappe.session.user === "Guest") {
            mainBody.classList.add("hidden");
            unauthorized.classList.remove("hidden");
        }

        const message = document.querySelector(".primary-heading");
        if (!roomName) {
            message.textContent = "No room name provided";
            return;
        }
        
        frappe.call({
            method: "jitsi_integration.www.meet.index.get_jitsi_meeting_url",
            args: {
                room: roomName,
                guest: guest || ""
            },
            callback(r) {
                if(r.message[0] && r.message[1]) {
                    window.location.href = r.message[1];
                } else {
                    message.textContent = r.message[1];
                }
            }
        })
    })
})

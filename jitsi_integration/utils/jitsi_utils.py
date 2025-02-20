import jwt
import frappe

@frappe.whitelist()
def generate_jitsi_meeting_token(full_name=None, email=None):
    jitsi_settings = frappe.get_single("JitSi Settings")
    # configureable in JitSi Integration Settings
    App_Secret = jitsi_settings.get_password("secret_token")
    Issuers=jitsi_settings.issuers
    Audiences=jitsi_settings.audiences
    Domain=jitsi_settings.domain
    if full_name and email:
        payload =  {
            "context": {
                "user": {
                    "name": full_name,
                    "email": email
                }
            },
            "aud": Issuers,
            "iss": Audiences,
            "sub": Domain,
            "room": "*"
        }
        
        encoded_jwt = jwt.encode(payload, App_Secret, algorithm="HS256")
        return encoded_jwt
    else:
        frappe.throw("Invalid Credentials")

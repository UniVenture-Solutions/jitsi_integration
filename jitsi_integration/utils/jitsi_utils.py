import jwt
import frappe
from cryptography.fernet import Fernet
import base64
from urllib.parse import quote

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
        
@frappe.whitelist()
def generate_encryption_key():
    try:
        key = Fernet.generate_key()
        return key.decode("utf-8")
    except Exception as e:
        frappe.log_error(f"Error generating encryption key: {str(e)}")
        frappe.throw("Error generating encryption key")
        
@frappe.whitelist()
def encrypt_info(data):
    try:
        jitsi_settings = frappe.get_single("JitSi Settings")
        encryption_key = jitsi_settings.get_password("encryption_key")
        if not encryption_key:
            frappe.throw("Encryption key is not set in JitSi Settings.")
        key = base64.urlsafe_b64encode(encryption_key.encode("utf-8")[:32])
        f = Fernet(key)
        encrypted_data = f.encrypt(data.encode("utf-8"))
        encrypted_str = encrypted_data.decode("utf-8")
        safe_info = quote(encrypted_str)
        return safe_info
    except Exception as e:
        frappe.log_error(f"Error encrypting data: {str(e)}")
        return None

@frappe.whitelist()
def decrypt_info(data):
    try:
        jitsi_settings = frappe.get_single("JitSi Settings")
        encryption_key = jitsi_settings.get_password("encryption_key")
        key = base64.urlsafe_b64encode(encryption_key.encode("utf-8")[:32])
        f = Fernet(key)

        decrypted_data = f.decrypt(data.encode("utf-8"))
        decrypted_info = decrypted_data.decode("utf-8")
        return decrypted_info
    except Exception as e:
        frappe.log_error(f"Error decrypting data: {str(e)}")
        return None

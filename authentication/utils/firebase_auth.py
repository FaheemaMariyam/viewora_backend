from firebase_admin import auth as firebase_auth
from rest_framework.exceptions import ValidationError


def verify_firebase_token(id_token: str):
    try:
        decoded_token = firebase_auth.verify_id_token(id_token)
        return decoded_token
    except Exception:
        raise ValidationError("Invalid or expired phone verification token")

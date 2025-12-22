# import firebase_admin
# from firebase_admin import credentials
# from django.conf import settings
# import os

# if not firebase_admin._apps:
#     cred = credentials.Certificate(
#         os.path.join(settings.BASE_DIR, "viewora_project", "firebase_service_account.json")
#     )
#     firebase_admin.initialize_app(cred)
import firebase_admin
from firebase_admin import credentials
import os

if not firebase_admin._apps:
    cred = credentials.Certificate(
        os.getenv("FIREBASE_CREDENTIALS")
    )
    firebase_admin.initialize_app(cred)

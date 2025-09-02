import os, json
from pywebpush import webpush, WebPushException

VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY")
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY")
VAPID_EMAIL = os.getenv("VAPID_EMAIL", "mailto:admin@example.com")

def send_webpush(endpoint: str, p256dh: str, auth: str, payload: dict):
    if not VAPID_PRIVATE_KEY:
        return
    try:
        webpush(
            subscription={"endpoint": endpoint, "keys": {"p256dh": p256dh, "auth": auth}},
            data=json.dumps(payload),
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims={"sub": VAPID_EMAIL},
        )
    except WebPushException:
        pass

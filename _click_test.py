import hashlib
import os
import time
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cinema.settings.local")
django.setup()

from django.conf import settings
from django.test import Client
from users.models import CustomUser
from payments.models import PaymentTransaction
from payments.services import create_payment, build_click_checkout_url

out = []
SECRET = settings.CLICK_SECRET_KEY or "test_secret"
# Sozlamada secret bo'lmasa, test uchun o'rnatamiz
if not settings.CLICK_SECRET_KEY:
    settings.CLICK_SECRET_KEY = SECRET
if not settings.CLICK_SERVICE_ID:
    settings.CLICK_SERVICE_ID = "12345"

EMAIL = "click_test@example.com"
CustomUser.objects.filter(email=EMAIL).delete()
PaymentTransaction.objects.filter(user__email=EMAIL).delete()

u = CustomUser.objects.create_user(
    email=EMAIL, password="Str0ngPass!", full_name="Click User", is_verified=True
)

# 1) Tranzaksiya yaratish
payment = create_payment(user=u, provider="click", plan="premium")
out.append(
    "payment created: %s | amount=%s | status=%s"
    % (payment.id, payment.amount, payment.status)
)

# 2) Checkout URL
url = build_click_checkout_url(payment)
out.append("checkout_url: %s" % url[:90])

service_id = settings.CLICK_SERVICE_ID
client = Client(SERVER_NAME="localhost")

# 3) PREPARE (action=0)
sign_time = str(time.time())
amount = str(payment.amount)
click_trans_id = "777001"
raw = f"{click_trans_id}{service_id}{SECRET}{payment.id}{amount}0{sign_time}"
sign = hashlib.md5(raw.encode()).hexdigest()

prepare_data = {
    "click_trans_id": click_trans_id,
    "service_id": service_id,
    "merchant_trans_id": str(payment.id),
    "amount": amount,
    "action": "0",
    "sign_time": sign_time,
    "sign_string": sign,
    "click_paydoc_id": "998877",
    "error": "0",
    "error_note": "Success",
}
r = client.post("/api/payments/click/prepare/", prepare_data)
out.append("PREPARE -> %s | %s" % (r.status_code, r.json()))

prepare_id = r.json().get("merchant_prepare_id", "")

# 4) COMPLETE (action=1)
sign_time2 = str(time.time())
raw2 = (
    f"{click_trans_id}{service_id}{SECRET}{payment.id}{prepare_id}{amount}1{sign_time2}"
)
sign2 = hashlib.md5(raw2.encode()).hexdigest()
complete_data = dict(prepare_data)
complete_data.update(
    {
        "action": "1",
        "sign_time": sign_time2,
        "sign_string": sign2,
        "merchant_prepare_id": prepare_id,
    }
)
r = client.post("/api/payments/click/complete/", complete_data)
out.append("COMPLETE -> %s | %s" % (r.status_code, r.json()))

# 5) Tekshirish: premium berildimi?
u.refresh_from_db()
payment.refresh_from_db()
out.append("payment status: %s" % payment.status)
out.append("user is_premium: %s" % u.is_premium)
out.append("user tier: %s" % u.subscription_tier)
out.append("expires: %s" % u.subscription_expires_at)

# 6) Noto'g'ri imzo
bad = dict(prepare_data)
bad["sign_string"] = "0" * 32
bad["action"] = "0"
r = client.post("/api/payments/click/prepare/", bad)
out.append("BAD SIGN prepare -> %s | error=%s" % (r.status_code, r.json().get("error")))

# 7) Idempotentlik: yana COMPLETE
exp_before = u.subscription_expires_at
r = client.post("/api/payments/click/complete/", complete_data)
u.refresh_from_db()
out.append(
    "RE-COMPLETE -> %s | error=%s | expires o'zgarmadi: %s"
    % (r.status_code, r.json().get("error"), u.subscription_expires_at == exp_before)
)

PaymentTransaction.objects.filter(user__email=EMAIL).delete()
CustomUser.objects.filter(email=EMAIL).delete()

with open("_click_out.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("done")

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cinema.settings.local")
django.setup()

from django.test import Client
from users.models import CustomUser

out = []
EMAIL = "flow_test@example.com"

# Tozalash
CustomUser.objects.filter(email=EMAIL).delete()

c = Client(SERVER_NAME="localhost")

# 1) GET register (form step)
r = c.get("/auth/register/")
h = r.content.decode()
out.append("GET /auth/register/ -> %s" % r.status_code)
out.append("  step=form (forma ko'rinadi): %s" % ("Hisob yarating" in h))
out.append("  kod bosqichi yo'q: %s" % ("Emailni tasdiqlang" not in h))

# 2) POST register form
r = c.post(
    "/auth/register/",
    {
        "full_name": "Flow Test",
        "email": EMAIL,
        "password": "Str0ngPass!",
        "password_confirm": "Str0ngPass!",
        "agree": "on",
    },
)
h = r.content.decode()
out.append("POST register -> %s" % r.status_code)
out.append("  kod bosqichi ko'rindi: %s" % ("Emailni tasdiqlang" in h))
out.append("  1 hafta premium badge: %s" % ("1 HAFTA BEPUL PREMIUM" in h))

u = CustomUser.objects.filter(email=EMAIL).first()
out.append("  user yaratildi: %s" % (u is not None))
out.append("  is_verified=False: %s" % (u and u.is_verified is False))
code = u.verification_token if u else ""
out.append("  kod 6 xonali: %s (code=%s)" % (bool(code) and len(code) == 6, code))
out.append("  premium hali yo'q: %s" % (u and u.is_premium is False))

# 3) POST wrong code
r = c.post("/auth/register/", {"code": "000" if code != "000" else "111"})
h = r.content.decode()
out.append(
    "POST wrong code -> %s | xato ko'rindi: %s"
    % (r.status_code, "noto'g'ri" in h.lower())
)

# 4) POST correct code
r = c.post("/auth/register/", {"code": code})
out.append(
    "POST correct code -> %s | redirect: %s" % (r.status_code, r.get("Location"))
)

u.refresh_from_db()
out.append("  is_verified=True: %s" % u.is_verified)
out.append("  premium faol: %s" % u.is_premium)
out.append("  tier=%s" % u.subscription_tier)
out.append("  expires=%s" % u.subscription_expires_at)

# 5) Home with welcome
r = c.get("/")
out.append("GET / -> %s" % r.status_code)

# Cleanup
CustomUser.objects.filter(email=EMAIL).delete()
out.append("cleanup done")

with open("_flow_out.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("done")

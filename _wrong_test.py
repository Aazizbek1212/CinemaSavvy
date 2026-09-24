import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cinema.settings.local")
django.setup()

from django.test import Client
from users.models import CustomUser

out = []
EMAIL = "wrong_code_test@example.com"
CustomUser.objects.filter(email=EMAIL).delete()

c = Client(SERVER_NAME="localhost")
c.post(
    "/auth/register/",
    {
        "full_name": "T",
        "email": EMAIL,
        "password": "Str0ngPass!",
        "password_confirm": "Str0ngPass!",
        "agree": "on",
    },
)

u = CustomUser.objects.get(email=EMAIL)
real_code = u.verification_token

# 6 xonali xato kod
wrong = "000" if real_code != "000" else "111"
r = c.post("/auth/register/", {"code": wrong})
h = r.content.decode()
out.append("6-xonali xato kod -> %s" % r.status_code)
out.append("  'noto\\'g\\'ri' ko'rindi: %s" % ("noto'g'ri" in h))
out.append(
    "  hali verify=False: %s"
    % (CustomUser.objects.get(email=EMAIL).is_verified is False)
)

# 3 xonali kod
r = c.post("/auth/register/", {"code": "123"})
h = r.content.decode()
out.append(
    "3-xonali kod -> %s | 'to\\'liq kiriting': %s"
    % (r.status_code, "to'liq kiriting" in h)
)

# to'g'ri kod
r = c.post("/auth/register/", {"code": real_code})
out.append("to'g'ri kod -> %s | %s" % (r.status_code, r.get("Location")))

CustomUser.objects.filter(email=EMAIL).delete()
with open("_wrong_out.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("done")

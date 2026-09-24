import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cinema.settings.local")
django.setup()

from django.test import Client
from users.models import CustomUser

EMAIL = "ctx_test@example.com"
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
wrong = "000" if u.verification_token != "000" else "111"
r = c.post("/auth/register/", {"code": wrong})
h = r.content.decode()

with open("_ctx_out.txt", "w", encoding="utf-8") as f:
    f.write("has 'Kod noto'g'ri': %s\n" % ("Kod noto" in h))
    # print the auth-error block if present
    idx = h.find("auth-error")
    f.write("auth-error idx: %s\n" % idx)
    if idx > 0:
        f.write(h[idx - 50 : idx + 300])
    else:
        f.write("NO auth-error block in HTML\n")
CustomUser.objects.filter(email=EMAIL).delete()
print("done")

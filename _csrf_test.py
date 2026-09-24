import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cinema.settings.local")
django.setup()

from django.test import Client
from users.models import CustomUser
from movies.models import Movie

out = []
movie = Movie.objects.first()

c = Client(SERVER_NAME="localhost")
r = c.get("/movies/%s/" % movie.slug)
out.append("GET movie_detail -> %s" % r.status_code)
out.append("  csrftoken cookie o'rnatildi: %s" % ("csrftoken" in r.cookies))

if "csrftoken" in r.cookies:
    csrf = r.cookies["csrftoken"].value
    out.append("  csrf token: %s..." % csrf[:12])

# Endi login qilib review yozamiz (cookie bilan)
EMAIL = "rev2@example.com"
CustomUser.objects.filter(email=EMAIL).delete()
u = CustomUser.objects.create_user(
    email=EMAIL, password="Str0ngPass!", full_name="R", is_verified=True
)
c2 = Client(SERVER_NAME="localhost", enforce_csrf_checks=True)
c2.force_login(u)
# csrf cookie olish
r2 = c2.get("/movies/%s/" % movie.slug)
csrf = c2.cookies.get("csrftoken")
out.append("after force_login + GET, csrftoken: %s" % (csrf is not None))

if csrf:
    import json

    resp = c2.post(
        "/api/reviews/movies/%s/reviews/create/" % movie.slug,
        data=json.dumps({"rating": 7, "text": "Test"}),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=csrf.value,
    )
    out.append("review POST with csrf -> %s" % resp.status_code)
    out.append("  body: %s" % resp.content.decode()[:150])

CustomUser.objects.filter(email=EMAIL).delete()
with open("_csrf_out.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("done")

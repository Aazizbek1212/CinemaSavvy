import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cinema.settings.local")
django.setup()

from django.test import Client
from movies.models import Movie

out = []
c = Client(SERVER_NAME="localhost")
movie = Movie.objects.first()

urls = [
    "/",
    "/movies/",
    "/search/",
    "/auth/login/",
    "/auth/register/",
    "/movies/%s/" % movie.slug,
    "/auth/register/success/",
    "/auth/password-reset/",
    "/auth/password-reset/done/",
]
for u in urls:
    try:
        r = c.get(u)
        out.append("%-40s -> %s" % (u, r.status_code))
    except Exception as e:
        out.append("%-40s -> ERROR %s" % (u, e))

with open("_smoke2.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("done")

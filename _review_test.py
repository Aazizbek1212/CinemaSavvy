import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cinema.settings.local")
django.setup()

from django.test import Client
from users.models import CustomUser
from movies.models import Movie
from reviews.models import Review

out = []
EMAIL = "review_test@example.com"
CustomUser.objects.filter(email=EMAIL).delete()

movie = Movie.objects.first()
out.append("movie: %s" % (movie.slug if movie else "YO'Q"))

if movie:
    # Verified user yaratamiz
    u = CustomUser.objects.create_user(
        email=EMAIL,
        password="Str0ngPass!",
        full_name="Reviewer",
        is_verified=True,
    )
    c = Client(SERVER_NAME="localhost", enforce_csrf_checks=True)
    c.force_login(u)

    url = "/api/reviews/movies/%s/reviews/create/" % movie.slug
    r = c.post(
        url, data={"rating": 8, "text": "Zo'r film!"}, content_type="application/json"
    )
    out.append("review POST (JSON, CSRF on) -> %s" % r.status_code)
    out.append("  body: %s" % r.content.decode()[:200])

    # Review yaratildimi?
    exists = Review.objects.filter(user=u, movie=movie).exists()
    out.append("  review yaratildi: %s" % exists)

    # Dublikat
    r2 = c.post(
        url, data={"rating": 9, "text": "Yana"}, content_type="application/json"
    )
    out.append("duplicate POST -> %s" % r2.status_code)
    out.append("  dublikat rad etildi: %s" % (r2.status_code == 400))

    Review.objects.filter(user=u, movie=movie).delete()
    CustomUser.objects.filter(email=EMAIL).delete()

with open("_review_out.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("done")

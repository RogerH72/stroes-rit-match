"""URLs of the screens outside the Django admin (roadmap phases 5-6)."""

from django.urls import path

from matching import views

urlpatterns = [
    path("uitzonderingen/", views.uitzonderingen, name="uitzonderingen"),
    # The precision is a path segment rather than a query parameter, so both
    # kinds of group have their own stable, bookmarkable address. `str` also
    # covers a street name with spaces in it: reverse() percent-encodes the
    # value, so the template never has to escape it by hand.
    path(
        "uitzonderingen/koppelen/<str:precisie>/<str:waarde>/",
        views.uitzonderingen_koppelen,
        name="uitzonderingen_koppelen",
    ),
]

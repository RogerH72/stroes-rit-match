"""URLs of the screens outside the Django admin (roadmap phases 5-6)."""

from django.contrib.auth.views import LogoutView
from django.urls import path

from matching import views

urlpatterns = [
    # One logout route for the whole application: both the navigation bar and
    # the admin header post here, so "uitloggen" cannot come to mean two things
    # depending on which screen you are on. Where it lands is
    # LOGOUT_REDIRECT_URL. LogoutView refuses GET, which is why both headers
    # hold a small POST form and not a link — a link would be followed by every
    # link-prefetcher and mail scanner.
    path("uitloggen/", LogoutView.as_view(), name="uitloggen"),
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
    # Monteur and week are query parameters rather than path segments: they are
    # what the two controls at the top of the page set, and a form GET writes
    # its fields into the query string by itself. The Excel export takes exactly
    # the same parameters, so "download deze week" is the page's own URL with
    # /excel/ in it.
    path("weekoverzicht/", views.weekoverzicht, name="weekoverzicht"),
    path(
        "weekoverzicht/excel/",
        views.weekoverzicht_excel,
        name="weekoverzicht_excel",
    ),
]

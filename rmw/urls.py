"""URL configuration for the RMW project."""

from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from matching import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", views.health, name="health"),
    # The application's own screens, outside the admin (phase 5: uitzonderingen,
    # phase 6: weekoverzicht).
    path("", include("matching.urls")),
    # The root is the front door of the application, not of the admin: the
    # weekoverzicht is what SBTT staff open all day, while the beheerschermen
    # are occasional. Anonymous visitors are not sent to the login page from
    # here — /weekoverzicht/ does that itself, and via that detour the login
    # carries ?next=/weekoverzicht/ so they land on the overview afterwards
    # rather than in the admin.
    path("", RedirectView.as_view(pattern_name="weekoverzicht", permanent=False)),
]

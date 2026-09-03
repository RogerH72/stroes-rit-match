"""URL configuration for the RMW project."""

from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from matching import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", views.health, name="health"),
    # The application's own screens, outside the admin (phase 5: uitzonderingen;
    # phase 6 adds the weekoverzicht here).
    path("", include("matching.urls")),
    # The admin remains the entry point: it holds the beheerschermen and the
    # only login page.
    path("", RedirectView.as_view(pattern_name="admin:index", permanent=False)),
]

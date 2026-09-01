"""URL configuration for the RMW project."""

from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView

from matching import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", views.health, name="health"),
    # No front-end yet (roadmap phases 5-6); the admin is the only entry point.
    path("", RedirectView.as_view(pattern_name="admin:index", permanent=False)),
]

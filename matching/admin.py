from django.contrib import admin

# Admin UI text is Dutch (project convention: UI in Dutch, code in English).
admin.site.site_header = "RMW — Ritten Match Werkbon"
admin.site.site_title = "RMW"
admin.site.index_title = "Beheer"

# No models registered yet; the koppeltabellen and the tolerantietabel are
# roadmap phase 4.

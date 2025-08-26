import environ
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

env = environ.Env()
environ.Env.read_env()

admin.site.site_header = env("SITE_NAME")
admin.site.site_title = env("SITE_NAME")
admin.site.index_title = "Admin Panel"

urlpatterns = [
    path("illiad/", admin.site.urls),
    # Django Ninja API
    path("api/v1/", include("api.urls")),
    path("", include("srl.urls")),
    path("docs/", include("guides.urls")),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    from debug_toolbar.toolbar import debug_toolbar_urls

    urlpatterns = urlpatterns + debug_toolbar_urls()

handler404 = "srl.static_views.page_not_found"

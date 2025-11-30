#!/usr/bin/env python
# config/urls.py

"""
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
   openapi.Info(
      title="Kauro API",
      default_version='v1',
      description="Kauro consent and chatbot API",
      terms_of_service="https://raw.githubusercontent.com/UCI-ICTS/kauro/refs/heads/dev/LICENSE.txt",
      contact=openapi.Contact(email="kingch2@hs.cui.edu"),
   ),
   public=True,
   permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('kbi/swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('kbi/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path("kbi/django-admin/", admin.site.urls),
    path('kbi/auth/', include('authentication.urls')),
    path('kbi/consentbot/', include('consentbot.urls')),
    path('kbi/archive/', include('archive.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

#!/usr/bin/env python
# config/urls.py

"""
"""
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.urls import path, include
from django.contrib import admin

schema_view = get_schema_view(
   openapi.Info(
      title="MIA API",
      default_version='v1',
      description="MIA consent and chatbot API",
      terms_of_service="https://yourdomain.com/terms/",
      contact=openapi.Contact(email="contact@yourdomain.com"),
   ),
   public=True,
   permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('mia/swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('mia/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path("mia/django-admin/", admin.site.urls),
    path('mia/auth/', include('authentication.urls')),
    path('mia/consentbot/', include('consentbot.urls')),
    # path('api/admin/', include('administration.urls')),
]

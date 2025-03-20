#!/usr/bin/env python
# config/urls.py

"""

"""

from django.urls import path, include
from django.contrib import admin

urlpatterns = [
    path("admin/", admin.site.urls),
    # path('api/auth/', include('authentication.urls')),
    # path('api/chatbot/', include('chatbot.urls')),
    # path('api/admin/', include('administration.urls')),
]

#!/usr/bin/env python
# archive/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from archive.apis import DocumentViewSet

router = DefaultRouter()
router.register(r'documents', DocumentViewSet, basename='documents')

urlpatterns = [
    path('', include(router.urls))
] 


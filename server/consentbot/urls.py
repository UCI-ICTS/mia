# consentbot/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from consentbot.apis import ConsentScriptViewSet

router = DefaultRouter()
router.register(r'scripts', ConsentScriptViewSet, basename='consent-scripts')

urlpatterns = [
    path('', include(router.urls)),
]

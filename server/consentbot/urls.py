# consentbot/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from consentbot.apis import (
    ConsentScriptViewSet,
    ConsentViewSet,
    ConsentUrlViewSet,
    ConsentResponseViewSet
)

router = DefaultRouter()
router.register(r'scripts', ConsentScriptViewSet, basename='consent-scripts')
router.register(r'consent', ConsentViewSet, basename='consent')
router.register(r'consent-url', ConsentUrlViewSet, basename='consent-url')
router.register(r'consent-response', ConsentResponseViewSet, basename='consent-response')


urlpatterns = [
    path('', include(router.urls)),
    path(
        'consent-url/<str:username>/invite-link/',
        ConsentUrlViewSet.as_view({'get': 'invite_link_by_username'}),
        name='invite-link-by-username'
    ),
]

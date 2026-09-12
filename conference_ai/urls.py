from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from auth.views import CurrentUserView, RegisterView

# Import ViewSets
from events.views import EventViewSet

from attendees.views import (
    AttendeeViewSet,
)

from recognition.views import (
    DetectedFaceViewSet,
)

from interactions.views import (
    InteractionViewSet,
)

# Create DRF router
router = DefaultRouter()

# =====================================
# Event Routes
# =====================================

router.register(
    r'events',
    EventViewSet,
    basename='event'
)

# =====================================
# Attendee Routes
# =====================================

router.register(
    r'attendees',
    AttendeeViewSet,
    basename='attendee'
)

# IMPORTANT
# This enables:
# POST /api/events/join/
# Note: Event join endpoint is implemented as an action on EventViewSet

# =====================================
# Recognition Routes
# =====================================

router.register(
    r'detected-faces',
    DetectedFaceViewSet,
    basename='detected-face'
)

# =====================================
# Interaction Routes
# =====================================

router.register(
    r'interactions',
    InteractionViewSet,
    basename='interaction'
)

# =====================================
# URL Patterns
# =====================================

urlpatterns = [

    # DRF API
    path(
        'api/',
        include(router.urls)
    ),

    # Django Admin
    path(
        'admin/',
        admin.site.urls
    ),

    # DRF Login/Logout
    path(
        'api-auth/',
        include('rest_framework.urls')
    ),

    path(
        'api/auth/register/',
        RegisterView.as_view(),
        name='register',
    ),
    path(
        'api/auth/login/',
        TokenObtainPairView.as_view(),
        name='token_obtain_pair',
    ),
    path(
        'api/auth/refresh/',
        TokenRefreshView.as_view(),
        name='token_refresh',
    ),
    path(
        'api/auth/me/',
        CurrentUserView.as_view(),
        name='current_user',
    ),
]

# =====================================
# Static & Media
# =====================================

if settings.DEBUG:

    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )

    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATIC_ROOT
    )

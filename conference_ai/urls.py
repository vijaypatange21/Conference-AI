"""
URL configuration for conference_ai project.

API Routes:
- /api/events/           POST, GET, PUT, DELETE
- /api/events/{id}/      GET, PUT, DELETE  
- /api/events/{id}/upload-image/  POST
- /api/events/{id}/images/        GET
- 
- /api/attendees/        GET
- /api/attendees/{id}/   GET, PUT, PATCH
- /api/attendees/{id}/update-selfie/  PATCH
- /api/events/join/      POST
-
- /api/detected-faces/   GET
- /api/detected-faces/{id}/  GET
- /api/detected-faces/by-event/  GET
- /api/detected-faces/stats/  GET
-
- /api/interactions/     GET
- /api/interactions/{id}/ GET
- /api/interactions/my-connections/  GET
- /api/interactions/top-combinations/ GET

Media:
- /media/               Uploaded selfies and event images

Admin:
- /admin/               Django admin interface

Technology Stack:
- REST Framework: DRF (Django Rest Framework)
- Routing: DefaultRouter for automatic viewset registration
- Media: /media/ folder for uploaded files
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter

# Import ViewSets from all apps
from events.views import EventViewSet
from attendees.views import AttendeeViewSet
from recognition.views import DetectedFaceViewSet
from interactions.views import InteractionViewSet

# Create router and register viewsets
router = DefaultRouter()

# Event management routes
router.register(r'events', EventViewSet, basename='event')

# Attendee management routes  
router.register(r'attendees', AttendeeViewSet, basename='attendee')

# Recognition (face detection) routes
router.register(r'detected-faces', DetectedFaceViewSet, basename='detected-face')

# Interaction (connection) routes
router.register(r'interactions', InteractionViewSet, basename='interaction')

urlpatterns = [
    # DRF API endpoints
    path('api/', include(router.urls)),
    
    # Django admin
    path('admin/', admin.site.urls),
    
    # DRF authentication endpoints (login/logout)
    path('api-auth/', include('rest_framework.urls')),
]

# Serve media files in development
# In production, use a static file server (Nginx, S3, CloudFront)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

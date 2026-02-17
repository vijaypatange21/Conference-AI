from django.apps import AppConfig


class AttendeesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'attendees'
    
    def ready(self):
        """Register signals when app is ready."""
        import attendees.signals  # noqa

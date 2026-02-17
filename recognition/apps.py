from django.apps import AppConfig


class RecognitionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'recognition'
    
    def ready(self):
        """Register signals when app is ready."""
        import recognition.signals  # noqa

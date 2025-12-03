from django.apps import AppConfig
import os

class MainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main'

    def ready(self):
        # Import signals
        import main.signals

        # Only start scheduler when running the server, not during migrations
        if os.environ.get("RUN_MAIN") == "true":
            from .tasks import fetch_career_advice
            fetch_career_advice()

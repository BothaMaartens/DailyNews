from django.apps import AppConfig


class DailynewsAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'DailyNews_App'

    def ready(self):
        import DailyNews_App.signals

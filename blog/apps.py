from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.core.management import call_command


def create_default_superuser(sender, **kwargs):
    """Create a default superuser after migrations complete"""
    call_command('create_superuser')


class BlogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "blog"

    def ready(self):
        """
        Connect signals and perform startup operations
        """
        post_migrate.connect(create_default_superuser, sender=self)

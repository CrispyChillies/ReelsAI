from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os
from django.conf import settings

User = get_user_model()


class Command(BaseCommand):
    help = "Create a superuser if none exists"

    def handle(self, *args, **options):
        if not User.objects.filter(is_superuser=True).exists():
            username = getattr(settings, "DJANGO_SUPERUSER_USERNAME")
            email = getattr(settings, "DJANGO_SUPERUSER_EMAIL")
            password = getattr(settings, "DJANGO_SUPERUSER_PASSWORD")

            User.objects.create_superuser(
                username=username, email=email, password=password
            )
            self.stdout.write(
                self.style.SUCCESS(f"Superuser {username} created successfully")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("Superuser already exists, skipping creation")
            )

from django.core.management.base import BaseCommand
from blog.create_test_data import create_test_data

class Command(BaseCommand):
    help = 'Creates test data for the blog app'

    def handle(self, *args, **kwargs):
        create_test_data()
        self.stdout.write(self.style.SUCCESS('Successfully created test data')) 
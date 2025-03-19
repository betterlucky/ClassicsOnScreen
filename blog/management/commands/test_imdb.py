from django.core.management.base import BaseCommand
import requests
from django.conf import settings

class Command(BaseCommand):
    help = 'Test IMDB codes against OMDB API'

    def handle(self, *args, **options):
        test_codes = [
            ('tt0076759', 'Star Wars'),
            ('tt0068646', 'The Godfather'),
            ('tt0107290', 'Jurassic Park')
        ]

        # Strip any quotes from the API key
        api_key = str(settings.OMDB_API_KEY).strip('"\'')

        for imdb_code, expected_title in test_codes:
            try:
                response = requests.get(
                    'http://www.omdbapi.com/',
                    params={
                        'i': imdb_code,
                        'apikey': api_key
                    }
                )
                data = response.json()
                
                self.stdout.write(f"\nTesting {imdb_code} (Expected: {expected_title})")
                self.stdout.write(f"API Key used (raw): {settings.OMDB_API_KEY}")
                self.stdout.write(f"API Key used (stripped): {api_key}")
                self.stdout.write(f"Response: {data}")
                
                if data.get('Response') == 'False':
                    self.stdout.write(self.style.ERROR(f"Error: {data.get('Error')}"))
                else:
                    actual_title = data.get('Title', '')
                    self.stdout.write(self.style.SUCCESS(f"Found: {actual_title}"))
                    
            except requests.RequestException as e:
                self.stdout.write(self.style.ERROR(f"Network error: {str(e)}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Other error: {str(e)}")) 
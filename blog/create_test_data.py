from django.core.management.base import BaseCommand
from django.utils import timezone
from blog.models import Film, Location, Show, ShowOption
from django.contrib.auth import get_user_model
from datetime import timedelta

def create_test_data():
    # Create test user if not exists
    User = get_user_model()
    test_user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'test@example.com',
            'is_active': True,
            'credits': 100  # Give the user some initial credits
        }
    )
    if created:
        test_user.set_password('testpass123')
        test_user.save()
    else:
        # Update existing user's credits
        test_user.credits = 100
        test_user.save()
    print("Created test user: testuser (password: testpass123) with 100 credits")

    # Create locations
    locations = [
        Location.objects.get_or_create(
            name='Royal',
            defaults={
                'max_capacity': 100,
                'min_capacity': 40,
                'contact_email': 'royal@example.com'
            }
        )[0],
        Location.objects.get_or_create(
            name='Regal',
            defaults={
                'max_capacity': 70,
                'min_capacity': 40,
                'contact_email': 'regal@example.com'
            }
        )[0],
        Location.objects.get_or_create(
            name='Plaza',
            defaults={
                'max_capacity': 80,
                'min_capacity': 40,
                'contact_email': 'plaza@example.com'
            }
        )[0]
    ]
    print("Created/Updated locations:", [loc.name for loc in locations])

    # Create films with exact IMDB names
    films = [
        Film.objects.get_or_create(
            imdb_code='tt0076759',
            defaults={
                'name': 'Star Wars',
                'description': 'The original Star Wars film from 1977',
                'active': True
            }
        )[0],
        Film.objects.get_or_create(
            imdb_code='tt0068646',
            defaults={
                'name': 'The Godfather',
                'description': '1972 crime drama classic',
                'active': True
            }
        )[0],
        Film.objects.get_or_create(
            imdb_code='tt0107290',
            defaults={
                'name': 'Jurassic Park',
                'description': '1993 dinosaur adventure',
                'active': True
            }
        )[0]
    ]
    print("Created/Updated films:", [film.name for film in films])

    # Create show options
    options = [
        ShowOption.objects.get_or_create(name='Subtitles')[0],
        ShowOption.objects.get_or_create(name='Relaxed Screening')[0],
        ShowOption.objects.get_or_create(name='Party Show')[0],
        ShowOption.objects.get_or_create(name='Q&A')[0]
    ]
    print("Created/Updated show options:", [opt.name for opt in options])

    # Create shows
    base_time = timezone.now() + timedelta(weeks=4)
    shows = []
    for i, (film, location) in enumerate(zip(films, locations * 2)):
        show, created = Show.objects.get_or_create(
            film=film,
            location=location,
            eventtime=base_time + timedelta(days=i*7),
            defaults={
                'body': f"Special screening of {film.name}",
                'created_by': test_user,
                'status': 'tbc'
            }
        )
        if created:
            # Only add options to newly created shows
            show.options.add(options[i % len(options)])
        shows.append(show)
    
    print("Created/Updated shows:", [f"{show.film.name} at {show.location.name}" for show in shows])

    # Add some credits to shows (only if they don't have any)
    for show in shows:
        if show.total_credits() < 10:
            show.add_credits(test_user, 10)
    print("Added initial credits to shows where needed")

if __name__ == '__main__':
    create_test_data() 
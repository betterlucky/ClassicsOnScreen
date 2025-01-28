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
        Location.objects.create(
            name='Royal',
            max_capacity=100,
            min_capacity=40
        ),
        Location.objects.create(
            name='Regal',
            max_capacity=70,
            min_capacity=40
        ),
        Location.objects.create(
            name='Plaza',
            max_capacity=80,
            min_capacity=40
        )
    ]
    print("Created locations:", [loc.name for loc in locations])

    # Create films with exact IMDB names
    films = [
        Film.objects.create(
            name='Star Wars',  # Changed to match IMDB exactly
            description='The original Star Wars film from 1977',
            active=True,
            imdb_code='tt0076759'
        ),
        Film.objects.create(
            name='The Godfather',
            description='1972 crime drama classic',
            active=True,
            imdb_code='tt0068646'
        ),
        Film.objects.create(
            name='Jurassic Park',
            description='1993 dinosaur adventure',
            active=True,
            imdb_code='tt0107290'
        )
    ]
    print("Created films:", [film.name for film in films])

    # Create show options
    options = [
        ShowOption.objects.create(name='Subtitles'),
        ShowOption.objects.create(name='Relaxed Screening'),
        ShowOption.objects.create(name='Party Show'),
        ShowOption.objects.create(name='Q&A')
    ]
    print("Created show options:", [opt.name for opt in options])

    # Create shows
    base_time = timezone.now() + timedelta(weeks=4)
    shows = []
    for i, (film, location) in enumerate(zip(films, locations * 2)):
        show = Show.objects.create(
            film=film,
            location=location,
            body=f"Special screening of {film.name}",
            created_by=test_user,
            eventtime=base_time + timedelta(days=i*7),
            status='tbc'
        )
        # Add random options to each show
        show.options.add(options[i % len(options)])
        shows.append(show)
    
    print("Created shows:", [f"{show.film.name} at {show.location.name}" for show in shows])

    # Add some credits to shows
    for show in shows:
        show.add_credits(test_user, 10)
    print("Added initial credits to shows")

if __name__ == '__main__':
    create_test_data() 
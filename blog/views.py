from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model, authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse, Http404, HttpResponseNotAllowed, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.contrib.sites.models import Site
from django.core.exceptions import PermissionDenied, ValidationError
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from django.db.models import Sum, Count, Q
from blog.forms import (
    SiteUserCreationForm, ShowForm, CommentForm, ShowFilterForm,
    ContactForm, PasswordResetForm
)
from blog.models import SiteUser, Film, Show, Location, Comment, ShowCreditLog, ShowOption, FilmVote, FAQ
from django.utils import timezone
from django.db import connection
from datetime import timedelta
from django.db import models


def reset(request):
    """Handle password reset requests."""
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = SiteUser.objects.get(email=email)
            except SiteUser.DoesNotExist:
                form.add_error('email', 'No user is associated with this email address.')
                return render(request, 'registration/password_reset.html', {'form': form})

            # Generate reset token
            uid = urlsafe_base64_encode(str(user.pk).encode('utf-8'))
            token = default_token_generator.make_token(user)

            # Send reset email
            subject = 'Password Reset Request'
            message = render_to_string('registration/password_reset_email.html', {
                'user': user,
                'uid': uid,
                'token': token,
                'domain': settings.SITE_DOMAIN,
                'protocol': 'https',
            })

            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
            messages.success(request, 'A password reset email has been sent. Please check your inbox.')
            return redirect('/')

    else:
        form = PasswordResetForm()

    return render(request, 'registration/reset.html', {'form': form})


def register(request):
    """Handle user registration."""
    if request.method == 'POST':
        form = SiteUserCreationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            if SiteUser.objects.filter(username=username).exists():
                form.add_error('username', 'This username is already taken. Please choose a different one.')
                return render(request, 'registration/register.html', {'form': form})

            # Create user
            user = SiteUser.objects.create_user(
                username=username,
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password1'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name']
            )

            # Generate confirmation token
            uid = urlsafe_base64_encode(str(user.pk).encode('utf-8'))
            token = default_token_generator.make_token(user)

            # Send confirmation email
            subject = 'Confirm your email'
            message = render_to_string('registration/confirmation_email.html', {
                'user': user,
                'uid': uid,
                'token': token,
                'domain': settings.SITE_DOMAIN,
            })

            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
            messages.success(request, 'Please check your email to confirm your registration.')
            return redirect('/')

    else:
        form = SiteUserCreationForm()

    return render(request, 'registration/register.html', {'form': form})


def activate(request, uidb64, token):
    """Activate a user account."""
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = get_user_model().objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, get_user_model().DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Your account has been activated. You can now log in.')
        return redirect('/')
    else:
        return HttpResponse('Activation link is invalid or has expired.')


def index(request):
    # Initial queryset with all necessary relations
    shows = Show.objects.select_related(
        'film', 
        'location'
    ).prefetch_related(
        'options'
    ).order_by('eventtime')

    # Base filtering for active shows
    shows = shows.filter(
        eventtime__gte=timezone.now()
    ).exclude(
        status__in=['completed', 'expired', 'cancelled']
    )

    form = ShowFilterForm(request.GET)

    if form.is_valid():
        filters = {}
        if form.cleaned_data.get('location'):
            filters['location'] = form.cleaned_data['location']
        if form.cleaned_data.get('film'):
            filters['film'] = form.cleaned_data['film']
        if form.cleaned_data.get('status') and form.cleaned_data['status'] != 'all':
            filters['status'] = form.cleaned_data['status']
            
        if filters:
            shows = shows.filter(**filters)

    if request.htmx:
        return render(request, 'show_listings.html', {
            'shows': shows,
            'form': form,
            'exclude_location_filter': False,
            'exclude_film_filter': False
        })
    
    context = {
        'form': form,
        'shows': shows,
        'active_shows_count': Show.objects.filter(
            eventtime__gte=timezone.now()
        ).exclude(
            status__in=['completed', 'expired', 'cancelled']
        ).count(),
        'available_films_count': Film.objects.filter(active=True).count(),
        'locations_count': Location.objects.count(),
    }
    return render(request, 'index.html', context)


def blog_film(request, film_name):
    """Display shows for a specific film."""
    film = get_object_or_404(Film, name=film_name)
    shows = Show.objects.filter(film=film).select_related('location').order_by("eventtime")
    form = ShowFilterForm(request.GET)

    if form.is_valid() and form.cleaned_data.get('status') and form.cleaned_data['status'] != 'all':
        shows = shows.filter(status=form.cleaned_data['status'])

    if request.htmx:
        return render(request, 'show_listings.html', {
            'shows': shows,
            'form': form,
            'exclude_film_filter': True,
        })

    context = {
        "shows": shows,
        "form": form,
        "title": f"Shows for {film.name}",
        "exclude_film_filter": True,
    }
    return render(request, "show_list.html", context)


def blog_location(request, location_name):
    """Display shows for a specific location."""
    location = get_object_or_404(Location, name=location_name)
    shows = Show.objects.filter(location=location).select_related('film').order_by("eventtime")
    form = ShowFilterForm(request.GET)

    if form.is_valid() and form.cleaned_data.get('status') and form.cleaned_data['status'] != 'all':
        shows = shows.filter(status=form.cleaned_data['status'])

    if request.htmx:
        return render(request, 'show_listings.html', {
            'shows': shows,
            'form': form,
            'exclude_location_filter': True,
        })

    context = {
        "shows": shows,
        "form": form,
        "title": f"Shows at {location.name}",
        "exclude_location_filter": True,
    }
    return render(request, "show_list.html", context)

def blog_detail(request, pk):
    """Display show details and handle comments."""
    show = get_object_or_404(Show.objects.select_related('film', 'location', 'created_by'), pk=pk)
    comments = Comment.objects.filter(show=show).select_related('author')

    if request.method == "POST":
        form = CommentForm(request.POST, request=request)
        if form.is_valid():
            comment = Comment(
                author=form.cleaned_data["user"],
                body=form.cleaned_data["body"],
                show=show,
            )
            comment.save()
            return redirect(request.path_info)
        # No else here. Form errors will be handled in the template
    else:  # This else is for GET requests
        form = CommentForm(request=request)

    context = {
        "show": show,
        "comments": comments,
        "form": form,
        "can_add_credits": show.status in ['inactive', 'tbc']
    }
    return render(request, "detail.html", context)

@login_required
def create_show(request):
    """Create a new show."""
    if request.method == 'POST':
        form = ShowForm(request.POST)
        if form.is_valid():
            show = form.save(commit=False)
            show.created_by = request.user
            
            if request.user.credits < 1:
                messages.error(request, 'You do not have enough credits to create a show.')
                return render(request, 'create_show.html', {'form': form})

            show.eventtime = form.cleaned_data['eventtime']
            
            # Check timing for warning
            min_creation_days = settings.SHOW_CREATION_MIN_DAYS
            min_creation_date = show.eventtime - timedelta(days=min_creation_days)
            
            if timezone.now() > min_creation_date:
                if request.user.is_staff:
                    # Add warning but allow creation
                    messages.warning(
                        request, 
                        f'This show is being created with less than {min_creation_days} days until the event. '
                        'This would normally not be allowed to ensure enough time for ticket sales and film booking, '
                        'but has been permitted due to admin privileges.'
                    )
                    show._skip_timing_validation = True
            
            try:
                show.full_clean()
                show.save()
                
                selected_options = form.cleaned_data.get('selected_options')
                if selected_options:
                    show.options.set(selected_options)
                
                show.add_credits(request.user, 1)
                messages.success(request, 'Show created successfully!')
                return redirect('blog_detail', pk=show.id)
            except ValidationError as e:
                for field, errors in e.message_dict.items():
                    for error in errors:
                        form.add_error(field, error)
    else:
        form = ShowForm()
    
    context = {
        'form': form,
        'min_days_before_event': settings.SHOW_CREATION_MIN_DAYS,
        'is_admin': request.user.is_staff
    }
    return render(request, 'create_show.html', context)


@login_required
def profile(request, username):
    """Display user profile and their shows."""
    profile_user = get_object_or_404(SiteUser, username=username)
    is_own_profile = request.user == profile_user
    
    # Get shows created by user
    shows = Show.objects.filter(created_by=profile_user)
    
    # Get shows user has contributed credits to
    now = timezone.now()
    upcoming_credited_shows = ShowCreditLog.objects.filter(
        user=profile_user,
        show__eventtime__gt=now
    ).select_related('show', 'show__film', 'show__location').order_by('show__eventtime')
    
    past_credited_shows = ShowCreditLog.objects.filter(
        user=profile_user,
        show__eventtime__lte=now
    ).select_related('show', 'show__film', 'show__location').order_by('-show__eventtime')

    form = ShowFilterForm(request.GET)
    if form.is_valid() and form.cleaned_data.get('status') and form.cleaned_data['status'] != 'all':
        shows = shows.filter(status=form.cleaned_data['status'])

    context = {
        'profile_user': profile_user,
        'is_own_profile': is_own_profile,
        'shows': shows,
        'upcoming_credited_shows': upcoming_credited_shows,
        'past_credited_shows': past_credited_shows,
        'form': form,
        'title': f"{profile_user.username}'s Shows",
        'total_credits': profile_user.credits,
        'active_shows_count': shows.filter(status__in=['tbc', 'confirmed']).count(),
        'contributed_shows': profile_user.get_active_contributions().count() if is_own_profile else None
    }
    return render(request, 'profile.html', context)


@login_required
def add_credits_to_show(request, show_id):
    """Add credits to a show."""
    show = get_object_or_404(Show, id=show_id)

    if not show.can_add_credits:
        messages.error(request, "Credits cannot be added to this show.")
        return redirect('blog_detail', pk=show.id)

    if request.method == 'POST':
        try:
            credits_to_add = int(request.POST.get('credits', 0))
            if credits_to_add <= 0:
                raise ValueError("Credits must be positive")
                
            show.add_credits(request.user, credits_to_add)
            messages.success(
                request, 
                f"Added {credits_to_add} credits to show. " + 
                (f"Show status changed to {show.status}" if show.status == 'tbc' else "")
            )
            
        except (ValueError, ValidationError) as e:
            messages.error(request, str(e))

    return redirect('blog_detail', pk=show.id)


@login_required
def update_show_status(request, pk):
    """Update show status."""
    show = get_object_or_404(Show, pk=pk)
    
    if request.user != show.created_by:
        raise PermissionDenied("Only the show creator can update its status.")
        
    new_status = request.POST.get('status')
    if show.can_transition_to(new_status):
        if new_status == 'confirmed':
            show.confirm_show()
        elif new_status == 'cancelled':
            show.cancel_show()
        elif new_status == 'completed':
            show.mark_completed()
            
        messages.success(request, f'Show status updated to {new_status}')
    else:
        messages.error(request, f'Cannot transition from {show.status} to {new_status}')
        
    return redirect('blog_detail', pk=pk)


def blog_about(request):
    """Display about page."""
    return render(request, 'about.html')


def blog_faq(request):
    """Display FAQ page."""
    faqs = FAQ.objects.filter(active=True).order_by('category', 'order', 'created_on')
    faqs_by_category = {}
    for faq in faqs:
        category = faq.get_category_display()
        if category not in faqs_by_category:
            faqs_by_category[category] = []
        faqs_by_category[category].append(faq)
    
    context = {
        'faqs_by_category': faqs_by_category,
        'MAX_FILM_VOTES': settings.MAX_FILM_VOTES,
    }
    return render(request, 'faq.html', context)


def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Get form data
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            
            # Format email message
            email_message = f"""
            New contact form submission:
            
            From: {name}
            Email: {email}
            Subject: {subject}
            
            Message:
            {message}
            """
            
            # Send email
            try:
                send_mail(
                    subject=f"Contact Form: {subject}",
                    message=email_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.CONTACT_EMAIL],
                    fail_silently=False,
                )
                
                if request.htmx:
                    return render(request, 'contact.html', {'success': True})
                return render(request, 'contact.html', {'success': True})
                
            except Exception as e:
                if request.htmx:
                    form.add_error(None, "Failed to send message. Please try again later.")
                    return render(request, 'contact.html', {'form': form})
                messages.error(request, "Failed to send message. Please try again later.")
        
        if request.htmx:
            return render(request, 'contact.html', {'form': form})
    else:
        form = ContactForm()
    
    return render(request, 'contact.html', {'form': form})


@login_required
def refund_credits_view(request, show_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    
    show = get_object_or_404(Show, id=show_id)
    
    # Check if show is confirmed
    if show.is_confirmed:
        messages.error(request, "Cannot refund credits for confirmed shows.")
        return redirect('profile', username=request.user.username)
    
    # Refund the requesting user's credits
    if show.refund_credits(user=request.user):
        messages.success(request, "Your credits have been refunded successfully.")
    else:
        messages.error(request, "Unable to refund credits. They may have already been refunded.")
    
    return redirect('profile', username=request.user.username)


@login_required
def buy_credits(request):
    """Temporary placeholder for credit purchase system."""
    if request.method == 'POST':
        # Add 10 credits to user's account
        request.user.credits += 10
        request.user.save()
        messages.success(request, 'Added 10 credits to your account.')
    return redirect(request.META.get('HTTP_REFERER', 'index'))


def film_list(request):
    # Get search query
    search_query = request.GET.get('search', '').strip()
    
    # Get all active films with their vote counts
    films = Film.objects.filter(active=True).annotate(
        vote_count=Count('votes', filter=models.Q(votes__created_on__gt=timezone.now() - timedelta(days=30)))
    )
    
    # Apply search filter if query exists
    if search_query:
        films = films.filter(name__icontains=search_query)
    
    films = films.order_by('name')
    
    # Initialize voting-related variables
    user_voted_films = set()
    days_remaining = {}
    votes_remaining = 0

    # Only process voting data for authenticated users
    if request.user.is_authenticated:
        user_votes = FilmVote.objects.filter(
            user=request.user,
            created_on__gt=timezone.now() - timedelta(days=30)
        )
        user_vote_count = user_votes.count()
        user_voted_films = set(vote.film_id for vote in user_votes)
        days_remaining = {vote.film_id: vote.days_remaining for vote in user_votes}
        votes_remaining = settings.MAX_FILM_VOTES - user_vote_count

    # Get top 5 most desired films
    top_films = Film.objects.filter(active=True).annotate(
        vote_count=Count('votes', filter=models.Q(votes__created_on__gt=timezone.now() - timedelta(days=30)))
    ).order_by('-vote_count')[:5]

    context = {
        'films': films,
        'top_films': top_films,
        'user_voted_films': user_voted_films,
        'votes_remaining': votes_remaining,
        'days_remaining': days_remaining,
        'search_query': search_query,
        'MAX_FILM_VOTES': settings.MAX_FILM_VOTES,
    }

    if request.htmx:
        # Return the show_listings template for HTMX requests
        return render(request, 'show_listings.html', context)
    
    return render(request, 'film_list.html', context)

@login_required
def most_desired_films(request):
    films = Film.objects.filter(active=True).annotate(
        vote_count=Count('votes', filter=Q(votes__created_on__gt=timezone.now() - timedelta(days=30)))
    ).order_by('-vote_count')
    
    return render(request, 'most_desired_films.html', {'films': films})

@login_required
def toggle_film_vote(request, film_id):
    if request.method != 'POST':
        return redirect('film_list')

    film = get_object_or_404(Film, id=film_id, active=True)
    user_votes = FilmVote.objects.filter(
        user=request.user,
        created_on__gt=timezone.now() - timedelta(days=30)
    )
    
    # Check if user already voted for this film
    existing_vote = user_votes.filter(film=film).first()
    
    if existing_vote:
        # Remove vote if it exists
        existing_vote.delete()
        messages.success(request, f'Vote removed for {film.name}')
    else:
        # Add new vote if user hasn't reached limit
        if user_votes.count() >= settings.MAX_FILM_VOTES:
            messages.error(request, f'You can only vote for up to {settings.MAX_FILM_VOTES} films at a time')
        else:
            FilmVote.objects.create(user=request.user, film=film)
            messages.success(request, f'Vote added for {film.name}')
    
    return redirect('film_list')

def validate_username(request):
    """Validate username availability."""
    username = request.POST.get('username', '').strip()
    response = {'is_valid': True, 'message': ''}
    
    if not username:
        response['is_valid'] = False
        response['message'] = 'Username is required.'
    elif len(username) < 3:
        response['is_valid'] = False
        response['message'] = 'Username must be at least 3 characters long.'
    elif SiteUser.objects.filter(username=username).exists():
        response['is_valid'] = False
        response['message'] = 'This username is already taken.'
    
    if request.htmx:
        if response['is_valid']:
            return HttpResponse('')
        return HttpResponse(
            f'<div class="invalid-feedback d-block">{response["message"]}</div>'
        )
    return JsonResponse(response)

def validate_email(request):
    """Validate email availability and format."""
    email = request.POST.get('email', '').strip()
    response = {'is_valid': True, 'message': ''}
    
    if not email:
        response['is_valid'] = False
        response['message'] = 'Email is required.'
    elif SiteUser.objects.filter(email=email).exists():
        response['is_valid'] = False
        response['message'] = 'This email is already registered.'
    
    if request.htmx:
        if response['is_valid']:
            return HttpResponse('')
        return HttpResponse(
            f'<div class="invalid-feedback d-block">{response["message"]}</div>'
        )
    return JsonResponse(response)


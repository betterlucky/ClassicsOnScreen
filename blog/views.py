from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.http import HttpResponse, Http404
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
from blog.models import SiteUser, Film, Show, Location, Comment


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


def blog_index(request):
    """Display and filter shows."""
    shows = Show.objects.select_related('film', 'location', 'created_by')
    form = ShowFilterForm(request.GET)

    if form.is_valid():
        filters = {}
        if form.cleaned_data.get('location'):
            filters['location'] = form.cleaned_data['location']
        if form.cleaned_data.get('film'):
            filters['film'] = form.cleaned_data['film']
        if form.cleaned_data.get('status') and form.cleaned_data['status'] != 'all':
            filters['status'] = form.cleaned_data['status']
        else:
            shows = shows.exclude(status__in=['completed', 'expired', 'cancelled'])
            
        if filters:
            shows = shows.filter(**filters)

    context = {
        'shows': shows,
        'form': form,
        'active_shows_count': shows.filter(status__in=['tbc', 'confirmed']).count(),
        'films_count': Film.objects.count(),
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
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = Comment(
                author=form.cleaned_data["author"],
                body=form.cleaned_data["body"],
                show=show,
            )
            comment.save()
            return redirect(request.path_info)
    else:
        form = CommentForm()

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
            try:
                show.full_clean()
                show.save()
                messages.success(request, 'Show created successfully!')
                return redirect('blog_detail', pk=show.id)
            except ValidationError as e:
                for field, errors in e.message_dict.items():
                    for error in errors:
                        form.add_error(field, error)
    else:
        form = ShowForm()
    return render(request, 'create_show.html', {'form': form})


@login_required
def profile(request, username):
    """Display user profile and their shows."""
    profile_user = get_object_or_404(SiteUser, username=username)
    is_own_profile = request.user == profile_user
    
    created_shows = Show.objects.filter(created_by=profile_user)\
        .select_related('film', 'location')\
        .prefetch_related('credit_logs')\
        .order_by('-eventtime')

    form = ShowFilterForm(request.GET)
    if form.is_valid() and form.cleaned_data.get('status') and form.cleaned_data['status'] != 'all':
        created_shows = created_shows.filter(status=form.cleaned_data['status'])

    context = {
        'profile_user': profile_user,
        'is_own_profile': is_own_profile,
        'shows': created_shows,
        'form': form,
        'title': f"{profile_user.username}'s Shows",
        'total_credits': profile_user.credits,
        'active_shows_count': created_shows.filter(status__in=['tbc', 'confirmed']).count(),
        'contributed_shows': profile_user.get_active_contributions().count() if is_own_profile else None
    }
    return render(request, 'profile.html', context)


@login_required
def add_credits_to_show(request, show_id):
    """Add credits to a show."""
    show = get_object_or_404(Show, id=show_id)

    if show.status not in ['inactive', 'tbc']:
        messages.error(request, "Credits can only be added to inactive or TBC shows.")
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


@login_required
def buy_credits(request):
    """Handle credit purchase."""
    try:
        credits_to_add = 10  # You might want to make this configurable
        if credits_to_add <= 0:
            raise ValueError("Credits must be a positive number.")

        request.user.credits += credits_to_add
        request.user.save()

        messages.success(request, f'You have successfully purchased {credits_to_add} credits!')
    except ValueError as e:
        messages.error(request, str(e))

    return redirect('profile', username=request.user.username)


def blog_about(request):
    """Display about page."""
    return render(request, 'about.html')


def blog_faq(request):
    """Display FAQ page."""
    return render(request, 'faq.html')


def blog_contact(request):
    """Handle contact form."""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            try:
                send_mail(
                    f'Contact Form Submission from {form.cleaned_data["name"]}',
                    f'Name: {form.cleaned_data["name"]}\n'
                    f'Email: {form.cleaned_data["email"]}\n\n'
                    f'Message:\n{form.cleaned_data["message"]}',
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.CONTACT_EMAIL],
                    fail_silently=False,
                )
                messages.success(request, 'Thank you for your message! We will get back to you shortly.')
                return redirect('/')
            except Exception as e:
                messages.error(request, f'There was an error sending your message: {e}. Please try again later.')
                return redirect('/')
    else:
        form = ContactForm()
    return render(request, 'contact.html', {'form': form})
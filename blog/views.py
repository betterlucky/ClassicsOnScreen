from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.http import HttpResponse, Http404, HttpRequest
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.contrib.sites.models import Site
from django.core.exceptions import PermissionDenied, ValidationError
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from blog.forms import SiteUserCreationForm, ShowForm, CommentForm, ShowFilterForm, ContactForm, PasswordResetForm
from blog.models import SiteUser, Film, Show, Location, Comment

def reset(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = SiteUser.objects.get(email=email)
            except SiteUser.DoesNotExist:
                form.add_error('email', 'No user is associated with this email address.')
                return render(request, 'registration/password_reset.html', {'form': form})

            # Generate the uid and token for password reset
            uid = urlsafe_base64_encode(str(user.pk).encode('utf-8'))
            token = default_token_generator.make_token(user)

            # Prepare the email content
            subject = 'Password Reset Request'
            message = render_to_string('registration/password_reset_email.html', {
                'user': user,
                'uid': uid,
                'token': token,
                'domain': "daveharris.eu.pythonanywhere.com",
                'protocol': 'https',  # Use 'http' if your site doesn't use HTTPS
            })

            # Send the password reset email
            send_mail(subject, message, 'no-reply@classicsbackonscreen.com', [user.email])

            messages.success(request, 'A password reset email has been sent. Please check your inbox.')
            return redirect('/')

    else:
        form = PasswordResetForm()

    return render(request, 'registration/reset.html', {'form': form})

def register(request):
    if request.method == 'POST':
        form = SiteUserCreationForm(request.POST)
        if form.is_valid():
            # Check if the username already exists
            username = form.cleaned_data['username']
            if SiteUser.objects.filter(username=username).exists():
                form.add_error('username', 'This username is already taken. Please choose a different one.')
                return render(request, 'registration/register.html', {'form': form})

            # If the username is unique, create the user
            email = form.cleaned_data['email']
            password = form.cleaned_data['password1']
            user = SiteUser.objects.create_user(username=username, email=email, password=password)

            # Generate the uid and token for email confirmation
            uid = urlsafe_base64_encode(str(user.pk).encode('utf-8'))
            token = default_token_generator.make_token(user)

            # Prepare email content

            subject = 'Confirm your email'
            message = render_to_string('registration/confirmation_email.html', {
                'user': user,
                'uid': uid,
                'token': token,
                'domain': "daveharris.eu.pythonanywhere.com",
            })

            # Send the confirmation email
            send_mail(subject, message, 'no-reply@classicsbackonscreen.com', [user.email])

            messages.success(request, 'Please check your email to confirm your registration.')
            return redirect('/')  # Redirect to login page or any other page after registration

    else:
        form = SiteUserCreationForm()

    return render(request, 'registration/register.html', {'form': form})


def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = get_user_model().objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, get_user_model().DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True  # Activate the user
        user.save()
        return redirect('/')  # Redirect to login after activation
    else:
        return HttpResponse('Activation link is invalid or has expired.')



def blog_about(request):
    return render(request, 'about.html')

def blog_faq(request):
    return render(request, 'faq.html')

def blog_index(request):
    shows = Show.objects.all()

    # Handle filtering by location, film, and status
    form = ShowFilterForm(request.GET)

    if form.is_valid():
        location = form.cleaned_data.get('location')
        film = form.cleaned_data.get('film')
        status = form.cleaned_data.get('status')

        if location:
            shows = shows.filter(location=location)
        if film:
            shows = shows.filter(film=film)

        # Apply the status filter if selected
        if status and status != 'all':
            shows = shows.filter(status=status)
        else:
            # Exclude completed, expired, and cancelled shows by default
            shows = shows.exclude(status__in=['completed', 'expired', 'cancelled'])

    return render(request, 'index.html', {'shows': shows, 'form': form})

def blog_film(request, film_name):
    try:
        film = Film.objects.get(name=film_name)
    except Film.DoesNotExist:
        raise Http404("Film not found")

    shows = Show.objects.filter(film=film).order_by("eventtime")
    context = {
        "shows": shows,
        "title": f"Shows for {film.name}",
    }
    return render(request, "show_list.html", context)


def blog_location(request, location_name):
    try:
        location = Location.objects.get(name=location_name)
    except Location.DoesNotExist:
        raise Http404("Location not found")

    shows = Show.objects.filter(location=location).order_by("eventtime")
    context = {
        "shows": shows,
        "title": f"Shows at {location.name}",
    }
    return render(request, "show_list.html", context)


def blog_detail(request, pk):
    show = get_object_or_404(Show, pk=pk)
    form = CommentForm()
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
    comments = Comment.objects.filter(show=show)
    context = {
        "show": show,
        "comments": comments,
        "form": form
    }
    return render(request, "detail.html", context)


@login_required
def create_show(request):
    if request.method == 'POST':
        form = ShowForm(request.POST)
        if form.is_valid():
            show = form.save(commit=False)
            show.created_by = request.user  # Assign the logged-in user as the creator
            show.save()
            return redirect('/')
    else:
        form = ShowForm()
    return render(request, 'create_show.html', {'form': form})


@login_required
def profile(request, username):
    # Get the user whose profile is being viewed
    profile_user = get_object_or_404(SiteUser, username=username)

    # Determine if the logged-in user is viewing their own profile
    is_own_profile = request.user == profile_user

    # Get the shows created by the profile user
    created_shows = Show.objects.filter(created_by=profile_user).order_by('eventtime')

    context = {
        'profile_user': profile_user,
        'is_own_profile': is_own_profile,
        'created_shows': created_shows,
        'title': f"{profile_user.username}'s Shows"
    }
    return render(request, 'profile.html', context)


@login_required
def add_credits_to_show(request, show_id):
    show = get_object_or_404(Show, id=show_id)

    # Ensure the show is not already completed or cancelled
    if show.status in ['completed', 'cancelled']:
        raise PermissionDenied("Cannot add credits to a completed or cancelled show.")

    # Get credits from POST data
    try:
        credits_to_add = int(request.POST.get('credits'))
        if credits_to_add <= 0:
            raise ValueError("Credits must be a positive number.")
    except (TypeError, ValueError):
        messages.error(request, "Invalid credit amount.")
        return redirect('blog_detail', pk=show.id)

    # Add credits to the show
    try:
        show.add_credits(request.user, credits_to_add)
        messages.success(request, f"Successfully added {credits_to_add} credits to the show.")
    except ValidationError as e:
        messages.error(request, str(e))

    return redirect('blog_detail', pk=show.id)

def blog_contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            message = form.cleaned_data['message']

            try:
                send_mail(
                    f'Contact Form Submission from {name}', # Subject
                    f'Name: {name}\nEmail: {email}\n\nMessage:\n{message}', # Message
                    settings.DEFAULT_FROM_EMAIL, # From email (configured in settings.py)
                    [settings.CONTACT_EMAIL], # To email (configured in settings.py)
                    fail_silently=False,
                )
                messages.success(request, 'Thank you for your message! We will get back to you shortly.')
                return redirect('/') # Redirect to prevent resubmission
            except Exception as e:
                messages.error(request, f'There was an error sending your message: {e}. Please try again later.')
                return redirect('/')

        else:
            messages.error(request, 'There was an error with your submission. Please check the form.')
    else:
        form = ContactForm()
    return render(request, 'contact.html', {'form': form})
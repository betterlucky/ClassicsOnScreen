from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, get_user_model
from django.contrib.auth.decorators import login_required

from blog.forms import  SiteUserCreationForm, CommentForm, ShowForm
from blog.models import Show, Film, Location, Comment, SiteUser

from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.forms import UserCreationForm
from django.core.mail import send_mail




from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.http import HttpResponse
from blog.models import SiteUser  # Import your custom SiteUser model
from django.db import IntegrityError
import random
import string

from django.shortcuts import render, redirect
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.contrib import messages
from blog.forms import SiteUserCreationForm
from blog.models import SiteUser  # Import your custom SiteUser model

from django.shortcuts import render, redirect
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.contrib import messages
from blog.forms import SiteUserCreationForm
from blog.models import SiteUser

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
                'domain': get_current_site(request).domain,
            })

            # Send the confirmation email
            send_mail(subject, message, 'no-reply@example.com', [user.email])

            messages.success(request, 'Please check your email to confirm your registration.')
            return redirect('login')  # Redirect to login page or any other page after registration

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
        return redirect('login')  # Redirect to login after activation
    else:
        return HttpResponse('Activation link is invalid or has expired.')
    
    
def blog_index(request):
    shows = Show.objects.all().order_by("eventtime")
    context = {"shows": shows}
    return render(request, "blog/index.html", context)


def blog_film(request, film_name):
    try:
        film = Film.objects.get(name=film_name)
    except Film.DoesNotExist:
        raise Http404("Film not found")
    
    shows = Show.objects.filter(film=film).order_by("eventtime")
    context = {'film': film, 'shows': shows}
    return render(request, "blog/film.html", context)

def blog_location(request, location_name):
    try:
        location = Location.objects.get(name=location_name)
    except Location.DoesNotExist:
        raise Http404("Location not found")
    
    shows = Show.objects.filter(location=location).order_by("eventtime")
    context = {'location': location, 'shows': shows}
    return render(request, "blog/location.html", context)

def user_shows(request, creator):
    # Get the user by username (creator)
    try:
        user = get_user_model().objects.get(username=creator)
    except get_user_model().DoesNotExist:
        user = None

    # Get all shows created by this user
    shows = Show.objects.filter(created_by=user).order_by('eventtime')

    return render(request, 'blog/user_shows.html', {'shows': shows, 'creator': user.username if user else 'Unknown'})

def blog_detail(request, pk):
    show = Show.objects.get(pk=pk)
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
            return HttpResponseRedirect(request.path_info)
    comments = Comment.objects.filter(show=show)
    context = {"show": show, "comments": comments, "form": form}

    return render(request, "blog/detail.html", context)

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
    return render(request, 'blog/create_show.html', {'form': form})


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
    }
    return render(request, 'blog/profile.html', context)

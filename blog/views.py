from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.http import HttpResponse, Http404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.core.exceptions import PermissionDenied
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from blog.forms import SiteUserCreationForm, ShowForm, CommentForm, ShowFilterForm
from blog.models import SiteUser, Film, Show, Location, Comment

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
    
    

from django.shortcuts import render
from .models import Show, Location, Film
from .forms import ShowFilterForm

def blog_index(request):
    shows = Show.objects.all()
    form = ShowFilterForm(request.GET)
    
    if form.is_valid():
        location = form.cleaned_data.get('location')
        film = form.cleaned_data.get('film')
        
        if location:
            shows = shows.filter(location=location)
        if film:
            shows = shows.filter(film=film)
    
    return render(request, 'blog/index.html', {'shows': shows, 'form': form})


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
    return render(request, "blog/show_list.html", context)


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
    return render(request, "blog/show_list.html", context)


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
        'title': f"{profile_user.username}'s Shows"
    }
    return render(request, 'blog/profile.html', context)


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

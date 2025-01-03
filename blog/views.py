from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.contrib.auth import login, get_user_model
from django.contrib.auth.decorators import login_required


from blog.forms import  CustomUserCreationForm, CommentForm, ShowForm
from blog.models import Show, Film, Location, Comment

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Log the user in after registration
            return redirect('/')  # Redirect to a success page
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

def blog_index(request):
    shows = Show.objects.all().order_by("eventtime")
    context = {"shows": shows}
    return render(request, "blog/index.html", context)


def blog_film(request, film_name):
    try:
        film = Film.objects.get(name=film_name)
    except Film.DoesNotExist:
        raise Http404("Film not found")
    
    shows = Show.objects.filter(film=film).order_by("-created_on")
    context = {'film': film, 'shows': shows}
    return render(request, "blog/film.html", context)

def blog_location(request, location_name):
    try:
        location = Location.objects.get(name=location_name)
    except Location.DoesNotExist:
        raise Http404("Location not found")
    
    shows = Show.objects.filter(location=location).order_by("-created_on")
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


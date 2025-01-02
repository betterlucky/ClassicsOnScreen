from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render

from blog.forms import CommentForm
from blog.models import Comment, Show, Film, Location


def blog_index(request):
    shows = Show.objects.all().order_by("-created_on")
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

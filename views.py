from django.shortcuts import render, get_object_or_404, redirect
from .models import Film, Screening, Comment
from django.contrib.auth.decorators import login_required
from .forms import ScreeningForm, CommentForm

def home(request):
    films = Film.objects.all()
    return render(request, 'home.html', {'films': films})

def film_list(request):
    films = Film.objects.all()
    return render(request, 'films.html', {'films': films})

@login_required
def create_screening(request):
    if request.method == 'POST':
        form = ScreeningForm(request.POST)
        if form.is_valid():
            screening = form.save(commit=False)
            screening.creator = request.user
            screening.save()
            return redirect('screening_detail', screening_id=screening.id)
    else:
        form = ScreeningForm()
    return render(request, 'create_screening.html', {'form': form})

def screening_detail(request, screening_id):
    screening = get_object_or_404(Screening, id=screening_id)
    comments = Comment.objects.filter(screening=screening)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.screening = screening
            comment.user = request.user
            comment.save()
            return redirect('screening_detail', screening_id=screening.id)
    else:
        form = CommentForm()
    return render(request, 'screening_detail.html', {'screening': screening, 'comments': comments, 'form': form})

@login_required
def my_screenings(request):
    screenings = request.user.joined_screenings.all()
    created_screenings = Screening.objects.filter(creator=request.user)
    return render(request, 'my_screenings.html', {'screenings': screenings, 'created_screenings': created_screenings})

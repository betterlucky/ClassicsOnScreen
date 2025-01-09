
from .models import Show, Location, Film
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import SiteUser

class ShowFilterForm(forms.Form):
    location = forms.ModelChoiceField(queryset=Location.objects.all(), required=False, empty_label="All Locations")
    film = forms.ModelChoiceField(queryset=Film.objects.all(), required=False, empty_label="All Films")
    status = forms.ChoiceField(
        choices=[('all', 'Upcoming Shows'), ('inactive', 'Inactive'), ('tbc', 'To Be Confirmed'), ('confirmed', 'Confirmed'), ('completed', 'Completed'), ('expired', 'Expired'), ('cancelled', 'Cancelled')],
        required=False,
        initial='all',
    )

class ContactForm(forms.Form):
    name = forms.CharField(label="Your Name", max_length=100, widget=forms.TextInput(attrs={'placeholder': 'Enter your name'}))
    email = forms.EmailField(label="Your Email", required=False, widget=forms.EmailInput(attrs={'placeholder': 'Enter your email'}))
    message = forms.CharField(label="Your Message", widget=forms.Textarea(attrs={'placeholder': 'Enter your message'}))

class SiteUserCreationForm(UserCreationForm):
    class Meta:
        model = SiteUser
        fields = ['username', 'email', 'password1', 'password2']


class CommentForm(forms.Form):
    author = forms.CharField(
        max_length=60,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Your Name"}
        ),
    )
    body = forms.CharField(
        widget=forms.Textarea(
            attrs={"class": "form-control", "placeholder": "Leave a comment!"}
        )
    )

class ShowForm(forms.ModelForm):
    class Meta:
        model = Show
        fields = ['body', 'film', 'location', 'eventtime']
        widgets = {
            'eventtime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
        labels = {
            'body': 'Description',
            'film': 'Film',
            'location': 'Location',
            'eventtime': 'Event Time',
        }

from .models import Show, Location, Film
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import SiteUser

class ShowFilterForm(forms.Form):
    location = forms.ModelChoiceField(queryset=Location.objects.all(), required=False, empty_label="All Locations")
    film = forms.ModelChoiceField(queryset=Film.objects.all(), required=False, empty_label="All Films")


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
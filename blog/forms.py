
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
    first_name = forms.CharField(
        max_length=30,
        required=True,
        help_text="Enter your first name."
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        help_text="Enter your last name."
    )
    email = forms.EmailField(
        required=True,
        help_text="Enter a valid email address."
    )

    class Meta:
        model = SiteUser
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if SiteUser.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email address already exists.")
        return email

class PasswordResetForm(forms.Form):
    email = forms.EmailField(
        label="Email Address",
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address',
        })
    )

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
        fields = ['body', 'film', 'location', 'eventtime', 'subtitles', 'relaxed_screening']
        widgets = {
            'eventtime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
        labels = {
            'body': 'Description',
            'film': 'Film',
            'location': 'Location',
            'eventtime': 'Event Time',
            'subtitles': 'Subtitled',
            'relaxed_screening': 'Relaxed Screening'

        }
from .models import Show, Location, Film, ShowOption
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import SiteUser
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field, HTML, Hidden
from datetime import datetime
from django.utils import timezone


class ShowFilterForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.layout = Layout(
            Row(
                Column('location', css_class='form-group col-md-4 mb-0'),
                Column('film', css_class='form-group col-md-4 mb-0'),
                Column('status', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Submit('submit', 'Filter Shows', css_class='btn btn-primary')
        )

    location = forms.ModelChoiceField(queryset=Location.objects.all(), required=False, empty_label="All Locations")
    film = forms.ModelChoiceField(queryset=Film.objects.all(), required=False, empty_label="All Films")
    status = forms.ChoiceField(
        choices=[('all', 'Upcoming Shows'), ('inactive', 'Inactive'), ('tbc', 'To Be Confirmed'), 
                ('confirmed', 'Confirmed'), ('completed', 'Completed'), ('expired', 'Expired'), 
                ('cancelled', 'Cancelled')],
        required=False,
        initial='all',
    )


class ContactForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='form-group col-md-6 mb-3'),
                Column('email', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Field('subject', css_class='mb-3'),
            Field('message', css_class='mb-3'),
        )

    name = forms.CharField(
        label="Your Name",
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter your name',
            'class': 'form-control'
        })
    )
    
    email = forms.EmailField(
        label="Your Email",
        widget=forms.EmailInput(attrs={
            'placeholder': 'Enter your email',
            'class': 'form-control'
        })
    )
    
    subject = forms.CharField(
        label="Subject",
        max_length=200,
        widget=forms.TextInput(attrs={
            'placeholder': 'What is your message about?',
            'class': 'form-control'
        })
    )
    
    message = forms.CharField(
        label="Your Message",
        widget=forms.Textarea(attrs={
            'placeholder': 'How can we help you?',
            'class': 'form-control',
            'rows': 5
        })
    )


class SiteUserCreationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('username', css_class='mb-3'),
            Row(
                Column('first_name', css_class='form-group col-md-6 mb-0'),
                Column('last_name', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Field('email', css_class='mb-3'),
            Field('password1', css_class='mb-3'),
            Field('password2', css_class='mb-3'),
            Submit('submit', 'Register', css_class='btn btn-primary'),
            HTML("""
                <div class="alert alert-info mt-3">
                    After registration, please check your email for a verification link.
                </div>
            """)
        )

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
        help_text="Enter a valid email address. You'll receive a verification email at this address."
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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('email', css_class='mb-3'),
            Submit('submit', 'Reset Password', css_class='btn btn-primary')
        )

    email = forms.EmailField(
        label="Email Address",
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address',
        })
    )


class CommentForm(forms.Form):
    body = forms.CharField(
        label='',
        widget=forms.Textarea(
            attrs={
                "class": "form-control", 
                "placeholder": "Leave a comment!",
                "rows": "3"
            }
        )
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('body', css_class='mb-3'),
            Submit('submit', 'Add Comment', css_class='btn btn-primary')
        )

    def clean(self):
        cleaned_data = super().clean()
        if self.request and self.request.user.is_authenticated:
            cleaned_data['user'] = self.request.user
        else:
            raise forms.ValidationError("User must be authenticated to comment.")
        return cleaned_data

class ShowForm(forms.ModelForm):
    event_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Event Date"
    )
    event_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        label="Event Time"
    )
    selected_options = forms.ModelMultipleChoiceField(
        queryset=ShowOption.objects.filter(active=True),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control',
            'style': 'display: none;'
        })
    )
    available_options = forms.ModelChoiceField(
        queryset=ShowOption.objects.filter(active=True),
        required=False,
        empty_label="Select show options...",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_available_options'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        
        self.helper.layout = Layout(
            HTML("""<p class="mt-3">Please remember it takes time to book the film, so your show must be a *minimum* of 3 weeks in the future.</p>"""),
            Field('film', css_class='mb-3'),
            Field('location', css_class='mb-3'),
            Row(
                Column('event_date', css_class='form-group col-md-6'),
                Column('event_time', css_class='form-group col-md-6'),
                css_class='mb-3'
            ),
            Field('body', css_class='mb-3 form-control', rows=2),
            Field('available_options', css_class='mb-2'),
            Field('selected_options'),
            HTML("""
                <div id="selected-options" class="mb-3">
                </div>
            """),
            Submit('submit', 'Create Show', css_class='btn btn-primary mt-3')
        )
        self.fields['film'].queryset = Film.objects.filter(active=True)

    class Meta:
        model = Show
        fields = ['film', 'location', 'event_date', 'event_time', 'body', 'selected_options']
        labels = {'body': 'Tell us about your show'}
        widgets = {
            'body': forms.Textarea(attrs={'class': 'form-control mb-3', 'rows': 4}),
        }

    def clean(self):
        cleaned_data = super().clean()
        event_date = cleaned_data.get('event_date')
        event_time = cleaned_data.get('event_time')
        if event_date and event_time:
            # Combine date and time into a single datetime object
            naive_eventtime = datetime.combine(event_date, event_time)
            # Make the datetime aware using Django's timezone
            cleaned_data['eventtime'] = timezone.make_aware(naive_eventtime)
        else:
            if not event_date:
                self.add_error('event_date', "Event date must be set.")
            if not event_time:
                self.add_error('event_time', "Event time must be set.")

        return cleaned_data
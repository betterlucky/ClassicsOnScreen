from .models import Show, Location, Film
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import SiteUser
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field, Div, HTML


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
            Field('name', css_class='mb-3'),
            Field('email', css_class='mb-3'),
            Field('message', css_class='mb-3'),
            Submit('submit', 'Send Message', css_class='btn btn-primary')
        )

    name = forms.CharField(label="Your Name", max_length=100, 
                         widget=forms.TextInput(attrs={'placeholder': 'Enter your name'}))
    email = forms.EmailField(label="Your Email", required=False, 
                           widget=forms.EmailInput(attrs={'placeholder': 'Enter your email'}))
    message = forms.CharField(label="Your Message", 
                            widget=forms.Textarea(attrs={'placeholder': 'Enter your message'}))


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
            Submit('submit', 'Register', css_class='btn btn-primary')
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
        widget=forms.Textarea(
            attrs={"class": "form-control", "placeholder": "Leave a comment!"}
        )
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None) # Pop the request
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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-group'
        self.helper.layout = Layout(
            HTML("""<p class="mt-3">Please remember it takes time to book the film, so your show must be a *minimum* of 3 weeks in the future.</p>"""),
            Field('film', wrapper_class='mb-3'),  # Use wrapper_class
            Field('location', wrapper_class='mb-3'),
            Field('eventtime', wrapper_class='mb-3'),
            Field('body', wrapper_class='mb-3', rows=4),
            Row(
                Column('subtitles', css_class='form-group col-md-6'),
                Column('relaxed_screening', css_class='form-group col-md-6'),
                css_class='mb-3'
            ),
            Submit('submit', 'Create Show', css_class='btn btn-primary mt-3')
        )
        self.fields['film'].queryset = Film.objects.filter(active=True)

    class Meta:
        model = Show
        fields = ['body', 'film', 'location', 'eventtime', 'subtitles', 'relaxed_screening']
        widgets = {
            'eventtime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'body': forms.Textarea(attrs={'rows': 4}),
        }
        labels = {
            'body': 'Description',
            'film': 'Film',
            'location': 'Location',
            'eventtime': 'Event Time',
            'subtitles': 'Subtitled',
            'relaxed_screening': 'Relaxed Screening'
        }

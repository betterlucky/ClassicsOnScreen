from django import forms
from .models import Screening, Comment

class ScreeningForm(forms.ModelForm):
    class Meta:
        model = Screening
        fields = ['film', 'date_time', 'location']

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']

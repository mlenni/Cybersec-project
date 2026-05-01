from django import forms
from django.contrib.auth.models import User
from .models import Note


class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["username", "password"]


class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ["title", "content", "secret_value"]
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Profile


REGISTRATION_ROLE_CHOICES = (
    ('student', 'Patient'),
    ('doctor', 'Doctor'),
)


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'input', 'placeholder': 'name@example.com'}),
    )
    role = forms.ChoiceField(
        choices=REGISTRATION_ROLE_CHOICES,
        widget=forms.RadioSelect,
    )
    age = forms.IntegerField(
        required=False,
        min_value=0,
        max_value=120,
        widget=forms.NumberInput(attrs={'class': 'input', 'placeholder': 'Your age'}),
    )
    photo = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'input', 'accept': 'image/*'}),
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'role', 'age', 'photo')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Choose a username'}),
            'password1': forms.PasswordInput(attrs={'class': 'input', 'placeholder': 'Create a password'}),
            'password2': forms.PasswordInput(attrs={'class': 'input', 'placeholder': 'Confirm your password'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ('username', 'email', 'password1', 'password2'):
            self.fields[field_name].widget.attrs.setdefault('class', 'input')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

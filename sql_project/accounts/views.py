from django import forms as dj_forms
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import RegistrationForm
from .models import Profile


def _sync_role(profile, user):
    if user.is_staff or user.is_superuser:
        if profile.role != 'admin':
            profile.role = 'admin'
            profile.save(update_fields=['role'])
    return profile


def register(request):
    if request.user.is_authenticated:
        return redirect('home')

    form = RegistrationForm(request.POST or None, request.FILES or None)

    if request.method == 'POST' and form.is_valid():
        user       = form.save(commit=False)
        user.email = form.cleaned_data.get('email', '')
        user.save()

        profile, _ = Profile.objects.get_or_create(user=user)
        profile.role = form.cleaned_data['role']
        profile.age  = form.cleaned_data.get('age')
        if form.cleaned_data.get('photo'):
            profile.photo = form.cleaned_data['photo']
        profile.save()

        login(request, user)
        messages.success(request, 'Account created successfully.')
        return redirect('home')

    return render(request, 'registration/register.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
def profile_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    profile = _sync_role(profile, request.user)

    if request.method == 'POST':
        # Update basic info
        request.user.first_name = request.POST.get('first_name', '').strip()
        request.user.last_name  = request.POST.get('last_name', '').strip()
        request.user.email      = request.POST.get('email', '').strip()
        request.user.save()

        profile.age = request.POST.get('age') or None
        if request.FILES.get('photo'):
            profile.photo = request.FILES['photo']

        # Doctor extra fields
        if profile.role == 'doctor':
            profile.specialty        = request.POST.get('specialty', '').strip()
            profile.department       = request.POST.get('department', '').strip()
            profile.bio              = request.POST.get('bio', '').strip()
            profile.qualifications   = request.POST.get('qualifications', '').strip()
            profile.experience_years = int(request.POST.get('experience_years') or 0)

        profile.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('profile')

    return render(request, 'accounts/profile.html', {'profile': profile})

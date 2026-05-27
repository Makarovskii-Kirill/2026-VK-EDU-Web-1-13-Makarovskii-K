from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.urls import is_valid_path
from django.http import HttpResponseRedirect
from .forms import LoginForm, SignUpForm, ProfileForm


def login(request):
    if request.user.is_authenticated:
        return redirect('questions:home')

    next_url = request.GET.get('next', '')
    if next_url and not is_valid_path(next_url):
        next_url = ''

    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            if next_url:
                return HttpResponseRedirect(next_url)
            return redirect('questions:home')
    else:
        form = LoginForm()

    return render(request, 'core/login.html', {
        'form': form,
        'next': next_url,
    })


def signup(request):
    if request.user.is_authenticated:
        return redirect('questions:home')

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect('questions:home')
    else:
        form = SignUpForm()

    return render(request, 'core/signup.html', {'form': form})


def logout(request):
    auth_logout(request)
    next_url = request.GET.get('next', request.META.get('HTTP_REFERER', '/'))
    return redirect(next_url)


@login_required
def profile(request):
    profile_obj = request.user.profile

    if request.method == 'POST':
        form = ProfileForm(
            request.POST,
            request.FILES,
            instance=profile_obj,
            user=request.user
        )
        if form.is_valid():
            form.save()
            return redirect('core:profile')
    else:
        form = ProfileForm(instance=profile_obj, user=request.user)

    return render(request, 'core/profile.html', {'form': form})
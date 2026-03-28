from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import get_object_or_404, redirect, render

from .forms import SpecialistProfileForm, UserRegistrationForm
from .models import SpecialistProfile


def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('home')
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    from django.contrib.auth import logout

    logout(request)
    return redirect('login')


@login_required
def profile_view(request):
    specialist_profile = getattr(request.user, 'specialist_profile', None)
    return render(request, 'accounts/profile.html', {'specialist_profile': specialist_profile})


def specialists_list_view(request):
    specialists = SpecialistProfile.objects.select_related('user').filter(
        moderation_status='approved'
    ).order_by('full_name')
    return render(request, 'accounts/specialists_list.html', {'specialists': specialists})


def specialist_detail_view(request, pk):
    specialist = get_object_or_404(SpecialistProfile, pk=pk, moderation_status='approved')
    return render(request, 'accounts/specialist_detail.html', {'specialist': specialist})


@login_required
def edit_specialist_profile_view(request):
    profile = getattr(request.user, 'specialist_profile', None)
    if profile is None:
        profile = SpecialistProfile(user=request.user)

    if request.method == 'POST':
        form = SpecialistProfileForm(request.POST, instance=profile)
        if form.is_valid():
            specialist = form.save(commit=False)
            specialist.user = request.user
            specialist.save()
            if request.user.role != 'specialist':
                request.user.role = 'specialist'
                request.user.save(update_fields=['role'])
            messages.success(request, 'Профиль специалиста сохранён.')
            return redirect('profile')
    else:
        form = SpecialistProfileForm(instance=profile)

    return render(request, 'accounts/edit_specialist_profile.html', {'form': form})

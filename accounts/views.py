from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .forms import RegisterForm


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


@login_required
def upload_photo(request):
    if request.method == 'POST' and request.FILES.get('photo'):
        profile = request.user.profile
        profile.photo = request.FILES['photo']
        profile.save()
        return JsonResponse({'success': True, 'url': profile.photo.url})
    return JsonResponse({'success': False, 'error': 'No file provided'}, status=400)
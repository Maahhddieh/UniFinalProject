from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from .forms import PlacementTestReservationForm
import re
from django.core.validators import validate_email
from django.core.exceptions import ValidationError


def home(request):
    return render(request, 'home.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Wrong username or password!')

    return render(request, 'login.html')



def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm = request.POST.get('confirm_password', '')

        # 1. هیچ فیلدی خالی نمونه
        if not username or not email or not password or not confirm:
            messages.error(request, 'All fields are required.')
            return redirect('signup')

        # 2. ایمیل معتبر
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, 'Invalid email address.')
            return redirect('signup')

        # 3. پسورد قوی
        password_regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{8,}$'
        if not re.match(password_regex, password):
            messages.error(request, 'Password must be at least 8 characters and include uppercase, lowercase, number, and special character.')
            return redirect('signup')

        if password != confirm:
            messages.error(request, 'Passwords do not match.')
            return redirect('signup')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'This username is already taken!')
            return redirect('signup')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'This email is already registered!')
            return redirect('signup')

        user = User.objects.create_user(username=username, email=email, password=password)
        messages.success(request, 'Successful registration! You can login now.')
        return redirect('login')

    return render(request, 'signup.html')



@login_required
def dashboard(request):
    return render(request, 'dashboard.html')


def logout_view(request):
    logout(request)
    return redirect('home')




from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import PlacementTestReservationForm

@login_required
def placement_test(request):
    if request.method == 'POST':
        form = PlacementTestReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.user = request.user
            reservation.save()
            return redirect('reservation_success')  # ریدایرکت به صفحه موفقیت
    else:
        form = PlacementTestReservationForm()
    return render(request, 'placement_test.html', {'form': form})

@login_required
def reservation_success(request):
    return render(request, 'reservation_success.html')

from django.http import JsonResponse
from .models import PlacementTestReservation

def get_reserved_times(request):
    date = request.GET.get('date')
    if date:
        reserved = PlacementTestReservation.objects.filter(date=date).values_list('time', flat=True)
        times = [t.strftime('%H:%M') for t in reserved]
        return JsonResponse({'reserved_times': times})
    return JsonResponse({'reserved_times': []})


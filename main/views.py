from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
from django.contrib import messages
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
import re
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import PlacementTestReservationForm
from django.http import JsonResponse
from .models import PlacementTestReservation


User = get_user_model()


def home(request):
    return render(request, 'home.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if not username or not password:
            messages.error(request, 'Username and password are required.')
            return render(request, 'login.html')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.user_type == 'teacher':
                return redirect('teacher_dashboard')
            else:
                return redirect('student_dashboard')
        else:
            messages.error(request, 'Wrong username or password!')

    return render(request, 'login.html')





def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm = request.POST.get('confirm_password', '')
        user_type = request.POST.get('user_type', '').strip()
        registration_code = request.POST.get('registration_code', '').strip()

        if not username or not email or not password or not confirm or not user_type:
            messages.error(request, 'All fields are required, including user type.')
            return redirect('signup')

        if user_type == 'teacher':
            VALID_CODE = "moon123789@"
            if registration_code != VALID_CODE:
                messages.error(request, 'Invalid registration code for teacher.')
                return redirect('signup')

        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, 'Invalid email address.')
            return redirect('signup')

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
        user.user_type = user_type
        user.save()

        messages.success(request, 'Successful registration! You can login now.')
        return redirect('login')

    return render(request, 'signup.html')




@login_required
def student_dashboard(request):
    return render(request, 'student_dashboard.html')

@login_required
def teacher_dashboard(request):
    return render(request, 'teacher_dashboard.html')



def logout_view(request):
    logout(request)
    return redirect('home')




@login_required
def placement_test(request):
    if request.method == 'POST':
        form = PlacementTestReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.user = request.user
            reservation.save()
            return redirect('reservation_success')
    else:
        form = PlacementTestReservationForm()
    return render(request, 'placement_test.html', {'form': form})

@login_required
def reservation_success(request):
    return render(request, 'reservation_success.html')


def get_reserved_times(request):
    date = request.GET.get('date')
    if date:
        reserved = PlacementTestReservation.objects.filter(date=date).values_list('time', flat=True)
        times = [t.strftime('%H:%M') for t in reserved]
        return JsonResponse({'reserved_times': times})
    return JsonResponse({'reserved_times': []})


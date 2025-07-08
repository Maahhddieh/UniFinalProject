from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup, name='signup'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
    path('placement_test/', views.placement_test, name='placement_test'),
    path('reservation-success/', views.reservation_success, name='reservation_success'),
    path('get-reserved-times/', views.get_reserved_times, name='get_reserved_times'),
]

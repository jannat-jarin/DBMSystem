from django.contrib.auth.views import LoginView
from django.urls import path

from .views import logout_view, profile_view, register


urlpatterns = [
    path('register/', register, name='register'),
    path('login/', LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', logout_view, name='logout'),
    path('profile/', profile_view, name='profile'),
]

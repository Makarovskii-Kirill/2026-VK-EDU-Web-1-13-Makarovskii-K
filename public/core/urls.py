from django.urls import path
from core import views

app_name = 'core'

urlpatterns = [
    path('login', views.login, name='login'),
    path('signup', views.signup, name='signup'),
    path('settings', views.settings, name='settings'),
]
from django.urls import path
from questions import views

app_name = 'questions'

urlpatterns = [
    path('', views.home, name='home'),
    path('ask', views.ask, name='ask'),
    path('question/35', views.question, name='question'),
    path('tag', views.tag, name='tag'),
    path('hot', views.hot, name='hot'),
]
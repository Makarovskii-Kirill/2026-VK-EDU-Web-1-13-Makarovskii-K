from django.urls import path
from . import views

app_name = 'questions'

urlpatterns = [
    path('', views.home, name='home'),
    path('hot/', views.hot, name='hot'),
    path('tag/<slug:tag_title>/', views.tag, name='tag'),
    path('question/<int:question_id>/', views.question, name='question'),
    path('ask/', views.ask, name='ask'),
    path('ajax/like-question/', views.like_question, name='like_question'),
    path('ajax/like-answer/', views.like_answer, name='like_answer'),
    path('ajax/correct-answer/', views.correct_answer, name='correct_answer'),
    path('centrifugo/token/', views.centrifugo_token, name='centrifugo_token'),
]
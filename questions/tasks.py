import requests
from celery import shared_task
from django.core.cache import cache
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from .models import Tag, Question, Answer, QuestionLike, AnswerLike
from django.conf import settings




@shared_task
def update_popular_tags():
    three_months_ago = timezone.now() - timedelta(days=90)
    
    tags = Tag.objects.filter(
        questions__created_at__gte=three_months_ago
    ).annotate(
        question_count=Count('questions')
    ).order_by('-question_count')[:10]
    
    result = [
        {
            'title': tag.title,
            'slug': tag.slug,
            'question_count': tag.question_count,
        }
        for tag in tags
    ]
    
    cache.set('popular_tags', result, timeout=60 * 15)  
    return result


@shared_task
def update_best_members():
    week_ago = timezone.now() - timedelta(days=7)
    
    best_question_authors = User.objects.filter(
        questions__created_at__gte=week_ago
    ).annotate(
        score=Count('questions__question_likes', distinct=True)
    ).order_by('-score')[:10]
    
    best_answer_authors = User.objects.filter(
        answers__created_at__gte=week_ago
    ).annotate(
        score=Count('answers__answer_likes', distinct=True)
    ).order_by('-score')[:10]
    
    users = {}
    for user in best_question_authors:
        users[user.id] = {'user': user, 'score': user.score}
    for user in best_answer_authors:
        if user.id in users:
            users[user.id]['score'] += user.score
        else:
            users[user.id] = {'user': user, 'score': user.score}
    
    sorted_users = sorted(users.values(), key=lambda x: x['score'], reverse=True)[:10]
    
    result = [
        {
            'username': item['user'].username,
            'score': item['score'],
        }
        for item in sorted_users
    ]
    
    cache.set('best_members', result, timeout=60 * 15) 
    return result


@shared_task
def notify_new_answer(question_id, answer_data):
    url = settings.CENTRIFUGO_API_URL
    api_key = settings.CENTRIFUGO_API_KEY
    
    data = {
        "method": "publish",
        "params": {
            "channel": f"questions:question:{question_id}",
            "data": answer_data,
        }
    }
    
    try:
        response = requests.post(url, json=data, headers={
            'Authorization': f'apikey {api_key}',
            'Content-Type': 'application/json',
        }, timeout=5)
        print(f'CENTRIFUGO RESPONSE: {response.status_code} {response.text}')
    except Exception as e:
        print(f'CENTRIFUGO ERROR: {e}')
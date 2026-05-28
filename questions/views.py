from django.shortcuts import render, get_object_or_404, redirect
from .pagination import paginate
from django.db.models import Count
from .models import Question, Tag, Answer, QuestionLike, AnswerLike
from django.contrib.auth.decorators import login_required
from .forms import QuestionForm, AnswerForm
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.cache import cache
from .tasks import update_popular_tags, update_best_members, notify_new_answer
import jwt
import time
from django.conf import settings


def get_popular_tags():
    tags = cache.get('popular_tags')
    if tags is None:
        tags = update_popular_tags()
    return tags


def get_best_members():
    members = cache.get('best_members')
    if members is None:
        members = update_best_members()
    return members



def home(request):
    questions = Question.objects.new_questions().prefetch_related('tags').select_related('author')
    page_obj = paginate(request, questions, per_page=5)
    return render(request, "questions/home.html", {"questions": page_obj.object_list, "page_obj": page_obj, "popular_tags": get_popular_tags(), "best_members": get_best_members(),})   

def hot(request):
    questions = Question.objects.best_questions().prefetch_related("tags").select_related("author")
    page_obj = paginate(request, questions, per_page=5)
    return render(request, "questions/hot.html", {"questions": page_obj.object_list, "page_obj": page_obj, "popular_tags": get_popular_tags(), "best_members": get_best_members(),})

def tag(request, tag_title):
    tag_obj = get_object_or_404(Tag, slug=tag_title)
    questions = Question.objects.by_tag(tag_obj.title).prefetch_related("tags").select_related("author")
    page_obj = paginate(request, questions, per_page=5)
    return render(request, "questions/tag.html", {"questions": page_obj.object_list, "page_obj": page_obj, "tag": tag_obj, "popular_tags": get_popular_tags(), "best_members": get_best_members(),})

def question(request, question_id):
    question_obj = get_object_or_404(Question.objects.annotate(likes_count=Count("question_likes")).prefetch_related("tags").select_related("author"), id=question_id)
    answers = Answer.objects.for_question(question_obj)
    page_obj = paginate(request, answers, per_page=5)

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('core:login')
        form = AnswerForm(request.POST)
        if form.is_valid():
            answer = form.save(commit=False)
            answer.question = question_obj
            answer.author = request.user
            answer.save()
            notify_new_answer.delay(question_id, {
                'id': answer.id,
                'content': answer.content[:200],
                'author': answer.author.username,
                'likes_count': 0,
                'is_correct': answer.is_correct,
                'created_at': answer.created_at.strftime('%d.%m.%Y %H:%M'),
            })
            return redirect(f'{request.path}#answer-{answer.id}')
        
    else:
        form = AnswerForm()

    return render(request, "questions/question.html", {"question": question_obj, "page_answer": page_obj.object_list, "page_obj": page_obj, "form": form, "popular_tags": get_popular_tags(), "best_members": get_best_members(),})
    

@login_required
def ask(request):
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.author = request.user
            question.save()
            form._save_tags(question)
            return redirect('question', question_id=question.id)
    else:
        form = QuestionForm()

    return render(request, 'questions/ask.html', {'form': form})


@require_POST
@login_required
def like_question(request):
    question_id = request.POST.get('question_id')
    action = request.POST.get('action')  

    if action not in ('like', 'dislike'):
        return JsonResponse({'error': 'Invalid action'}, status=400)

    question = get_object_or_404(Question, pk=question_id)

    if action == 'like':
        like, created = QuestionLike.objects.get_or_create(
            user=request.user,
            question=question
        )
        if not created:
            return JsonResponse({'error': 'Already liked'}, status=400)
    else:
        deleted, _ = QuestionLike.objects.filter(
            user=request.user,
            question=question
        ).delete()
        if not deleted:
            return JsonResponse({'error': 'Not liked yet'}, status=400)

    likes_count = question.question_likes.count()
    return JsonResponse({'likes_count': likes_count})


@require_POST
@login_required
def like_answer(request):
    answer_id = request.POST.get('answer_id')
    action = request.POST.get('action') 

    if action not in ('like', 'dislike'):
        return JsonResponse({'error': 'Invalid action'}, status=400)

    answer = get_object_or_404(Answer, pk=answer_id)

    if action == 'like':
        like, created = AnswerLike.objects.get_or_create(
            user=request.user,
            answer=answer
        )
        if not created:
            return JsonResponse({'error': 'Already liked'}, status=400)
    else:
        deleted, _ = AnswerLike.objects.filter(
            user=request.user,
            answer=answer
        ).delete()
        if not deleted:
            return JsonResponse({'error': 'Not liked yet'}, status=400)

    likes_count = answer.answer_likes.count()
    return JsonResponse({'likes_count': likes_count})


@require_POST
@login_required
def correct_answer(request):
    answer_id = request.POST.get('answer_id')
    answer = get_object_or_404(Answer, pk=answer_id)

    if answer.question.author != request.user:
        return JsonResponse({'error': 'Not authorized'}, status=403)

    Answer.objects.filter(question=answer.question).update(is_correct=False)
    answer.is_correct = True
    answer.save()

    return JsonResponse({'status': 'ok', 'answer_id': answer.id})




def centrifugo_token(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    token = jwt.encode({
        'sub': str(request.user.id),
        'exp': int(time.time()) + 3600 * 24,  # 24 часа
    }, settings.CENTRIFUGO_TOKEN_SECRET, algorithm='HS256')
    
    return JsonResponse({'token': token})
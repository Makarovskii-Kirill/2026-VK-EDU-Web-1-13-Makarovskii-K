from django.shortcuts import render, get_object_or_404, redirect
from .pagination import paginate
from django.db.models import Count
from .models import Question, Tag, Answer, QuestionLike, AnswerLike
from django.contrib.auth.decorators import login_required
from .forms import QuestionForm, AnswerForm
from django.http import JsonResponse
from django.views.decorators.http import require_POST


def home(request):
    questions = Question.objects.new_questions().prefetch_related('tags').select_related('author')
    page_obj = paginate(request, questions, per_page=5)
    return render(request, "questions/home.html", {"questions": page_obj.object_list, "page_obj": page_obj})   

def hot(request):
    questions = Question.objects.best_questions().prefetch_related("tags").select_related("author")
    page_obj = paginate(request, questions, per_page=5)
    return render(request, "questions/hot.html", {"questions": page_obj.object_list, "page_obj": page_obj})

def tag(request, tag_title):
    tag_obj = get_object_or_404(Tag, slug=tag_title)
    questions = Question.objects.by_tag(tag_obj.title).prefetch_related("tags").select_related("author")
    page_obj = paginate(request, questions, per_page=5)
    return render(request, "questions/tag.html", {"questions": page_obj.object_list, "page_obj": page_obj, "tag": tag_obj})

def question(request, question_id):
    question_obj = get_object_or_404(Question.objects.annotate(likes_count=Count("question_likes")).prefetch_related("tags").select_related("author"), id=question_id)
    answers = Answer.objects.for_question(question_obj)
    page_obj = paginate(request, answers, per_page=5)

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login')
        form = AnswerForm(request.POST)
        if form.is_valid():
            answer = form.save(commit=False)
            answer.question = question_obj
            answer.author = request.user
            answer.save()
            return redirect(f'{request.path}?page={page_obj.paginator.num_pages}#answer-{answer.id}')
        
    else:
        form = AnswerForm()

    return render(request, "questions/question.html", {"question": question_obj, "page_answer": page_obj.object_list, "page_obj": page_obj, "form": form,})
    

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
    """Лайк/дизлайк ответа."""
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
    """Выбор правильного ответа (только автор вопроса)."""
    answer_id = request.POST.get('answer_id')
    answer = get_object_or_404(Answer, pk=answer_id)

    # Проверка: только автор вопроса может выбирать правильный ответ
    if answer.question.author != request.user:
        return JsonResponse({'error': 'Not authorized'}, status=403)

    # Снимаем метку со всех ответов на этот вопрос
    Answer.objects.filter(question=answer.question).update(is_correct=False)
    # Ставим метку на выбранный ответ
    answer.is_correct = True
    answer.save()

    return JsonResponse({'status': 'ok', 'answer_id': answer.id})
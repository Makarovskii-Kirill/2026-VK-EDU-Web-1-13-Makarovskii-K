from django.shortcuts import render
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

QUESTIONS = [
    {
        'id': i,
        'title': f'Question number {i}',
        'text': f'Text {i}',
    }
    for i in range (1, 21)
]

ANSWERS = [
    {
        'id': i,
        'title': f'Answer number {i}',
        'text': f'Text {i}',
    }
    for i in range (1, 21)
]


def home(request):
    page_obj = paginate(QUESTIONS, request)
    return render(request, 'questions/home.html', context={'questions': page_obj.object_list, 'page_obj': page_obj})

def ask(request):
    return render(request, 'questions/ask.html')

def question(request):
    page_obj = paginate(ANSWERS, request)
    return render(request, 'questions/question.html', context={'answers': page_obj.object_list, 'page_obj': page_obj})

def tag(request):
    page_obj = paginate(QUESTIONS, request)
    return render(request, 'questions/tag.html', context={'questions': page_obj.object_list, 'page_obj': page_obj})

def hot(request):
    page_obj = paginate(QUESTIONS, request)
    return render(request, 'questions/hot.html', context={'questions': page_obj.object_list, 'page_obj': page_obj})


def paginate(objects_list, request, per_page=5):
    paginator = Paginator(objects_list, per_page)
    page_number = request.GET.get('page', 1)

    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    return page_obj
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.db.models import Count, Prefetch
from django.utils.html import format_html
from questions.models import Tag, Question, QuestionLike, Answer, AnswerLike





class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0 
    fields = ('author', 'content_short', 'is_correct', 'created_at')
    readonly_fields = ('created_at', 'content_short')
    show_change_link = True  
    can_delete = True

    def content_short(self, obj):
        if obj.content:
            return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
        return '-'
    content_short.short_description = 'Текст ответа'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('author')




    

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['title', 'question_count', 'created_at']
    search_fields = ['title', ]
    list_filter = ['created_at', ]
    ordering = ['title', ]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_question_count = Count('questions'))
    
    def question_count(self, obj):
        return obj._question_count
    
    question_count.short_description = 'Количество вопросов'
    question_count.admin_order_field = '_question_count'

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'tags_list', 'likes_count', 'answers_count', 'is_answered', 'created_at']
    
    search_fields = ['title', 'content', 'author__username', 'tags__title']
    
    list_filter = ['created_at', 'updated_at', 'tags',('author', admin.RelatedOnlyFieldListFilter),  ]
    
    readonly_fields = ['created_at', 'updated_at', 'likes_count', 'answers_count']
    
    fieldsets = (
        ('Основное', {'fields': ('title', 'content', 'author', 'tags')}),
        ('Статистика', {'fields': ('likes_count', 'answers_count'), 'classes': ('collapse',)}),
        ('Даты', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    
    raw_id_fields = ['author', ]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('author').prefetch_related('tags').annotate(_likes_count = Count('question_likes', distinct=True), _answers_count = Count('answers', distinct=True))
    
    def tags_list(self, obj):
        return ', '.join(tag.title for tag in obj.tags.all())
    tags_list.short_description = 'Теги'

    
    def likes_count(self, obj):
        return obj._likes_count
    likes_count.short_description = 'Лайки'
    likes_count.admin_order_field = '_likes_count'


    def answers_count(self, obj):
        return obj._answers_count
    answers_count.short_description = 'Ответы'
    answers_count.admin_order_field = '_answers_count'


    def is_answered(self, obj):
        return obj.answers.filter(is_correct = True).exists()
    is_answered.short_description = 'Решён'
    is_answered.boolean = True  


@admin.register(QuestionLike)
class QuestionLikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'question_link', 'created_at']
    search_fields = ['user__username', 'question__title']
    list_filter = ['created_at',]
    raw_id_fields = ['user', 'question']
    date_hierarchy = 'created_at'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'question')
    
    def question_link(self, obj):
        from django.urls import reverse
        url = reverse('admin:questions_question_change', args=[obj.question.id])
        return format_html('<a href="{}">{}</a>', url, obj.question.title[:50])
    question_link.short_description = 'Вопрос'


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ['short_content', 'question_link', 'author', 'is_correct', 'likes_count', 'created_at']
    search_fields = ['content', 'author__username', 'question__title']
    list_filter = ['is_correct', 'created_at', ('question', admin.RelatedOnlyFieldListFilter), ('author', admin.RelatedOnlyFieldListFilter)]
    readonly_fields = ['created_at', 'updated_at', 'likes_count']
    raw_id_fields = ['question', 'author']  

    fieldsets = (
        ('Основное', {'fields': ('question', 'author', 'content', 'is_correct')}),
        ('Статистика', {'fields': ('likes_count',), 'classes': ('collapse',)}),
        ('Даты', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('question', 'author').annotate(_likes_count = Count('answer_likes', distinct=True))

    def short_content(self, obj):
        return obj.content[:80] + '...' if len(obj.content) > 80 else obj.content
    short_content.short_description = 'Текст ответа'

    def question_link(self, obj):
        from django.urls import reverse
        url = reverse('admin:questions_question_change', args=[obj.question.id])
        return format_html('<a href="{}">{}</a>', url, obj.question.title[:50])
    question_link.short_description = 'Вопрос'

    def likes_count(self, obj):
        return obj._likes_count
    likes_count.short_description = 'Лайки'
    likes_count.admin_order_field = '_likes_count'


@admin.register(AnswerLike)
class AnswerLikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'answer_short', 'question_link', 'created_at']
    search_fields = ['user__username', 'answer__content', 'answer__question__title']
    list_filter = ['created_at',]
    raw_id_fields = ['user', 'answer']
    date_hierarchy = 'created_at'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'answer__question', 'answer__author')

    def answer_short(self, obj):
        return obj.answer.content[:60] + '...' if len(obj.answer.content) > 60 else obj.answer.content
    answer_short.short_description = 'Ответ'

    def question_link(self, obj):
        from django.urls import reverse
        url = reverse('admin:questions_question_change', args=[obj.answer.question.id])
        return format_html('<a href="{}">{}</a>', url, obj.answer.question.title[:50])
    question_link.short_description = 'Вопрос'

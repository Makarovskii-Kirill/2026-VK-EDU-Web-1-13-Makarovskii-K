from django.db import models
from django.db.models import Count
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify


class Tag(models.Model):
    title = models.CharField(max_length=50, unique=True, verbose_name='Название')

    created_at = models.DateTimeField(default=timezone.now, verbose_name='Создано')

    slug = models.SlugField(max_length=255, unique=True, verbose_name="Слаг")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['title']
        verbose_name = "Тег"
        verbose_name_plural = "Теги"
    

class QuestionManager(models.Manager):
    def new_questions(self):
        return self.annotate(likes_count=Count('question_likes', distinct=True), answers_count=Count('answers', distinct=True)).order_by('-created_at')
    
    def best_questions(self):
        return self.annotate(likes_count = Count('question_likes', distinct=True), answers_count=Count('answers', distinct=True)).order_by('-likes_count', '-created_at')
    
    def by_tag(self, tag_title):
        return self.filter(tags__title = tag_title).annotate(likes_count = Count("question_likes", distinct=True), answers_count=Count('answers', distinct=True)).order_by("-created_at")
    

class AnswerManager(models.Manager):
    def for_question(self, question):
        return self.filter(question=question).annotate(likes_count = Count("answer_likes", distinct=True)).select_related("author").order_by("-created_at")



class Question(models.Model):
    title = models.CharField(max_length=255, verbose_name='Название')
    content = models.TextField(verbose_name='Текст')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="questions",
        verbose_name='Автор'
    )

    tags = models.ManyToManyField(
        Tag,
        related_name="questions",
        blank=True,
        verbose_name='Теги'
    )

    created_at = models.DateTimeField(default=timezone.now, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Изменено')

    objects = QuestionManager()

    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"


class Answer(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="answers",
        verbose_name='Вопрос'
    )

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name='Автор'
    )

    content = models.TextField(verbose_name='Текст')
    is_correct = models.BooleanField(default=False, verbose_name='Корректность')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Изменено')

    objects = AnswerManager()

    def __str__(self):
        return f"Answer by {self.author.username} to {self.question.title}"
    
    class Meta:
        ordering = ['-is_correct', '-created_at']
        verbose_name = "Ответ"
        verbose_name_plural = "Ответы"


class QuestionLike(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='question_likes',
        verbose_name='Пользователь'
    )

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='question_likes',
        verbose_name='Вопрос'
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Добавлен')

    def __str__(self):
        return f"{self.user.username} likes {self.question.title}"
    
    class Meta:
        unique_together = ('user', 'question')
        verbose_name = "Лайк на вопрос"
        verbose_name_plural = "Лайки на вопросы"

    
class AnswerLike(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="answer_likes",
        verbose_name='Пользователь'
    )

    answer = models.ForeignKey(
        Answer,
        on_delete=models.CASCADE,
        related_name="answer_likes",
        verbose_name='Ответ'

    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Добавл')

    def __str__(self):
        return f"{self.user.username} likes answer by {self.answer.author.username}"
    
    class Meta:
        unique_together = ('user', 'answer')
        verbose_name = "Лайк на ответ"
        verbose_name_plural = "Лайки на ответы"
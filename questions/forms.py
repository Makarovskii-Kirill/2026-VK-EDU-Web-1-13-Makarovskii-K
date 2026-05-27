from django import forms
from .models import Question, Answer, Tag


class QuestionForm(forms.ModelForm):
    tags = forms.CharField(
        label='Теги',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите теги через запятую'
        }),
        required=False
    )

    class Meta:
        model = Question
        fields = ('title', 'content')
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Заголовок вопроса'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Текст вопроса'
            }),
        }

    def clean_title(self):
        title = self.cleaned_data['title']
        if len(title) < 10:
            raise forms.ValidationError('Заголовок должен быть не менее 10 символов.')
        return title

    def clean_tags(self):
        tags_str = self.cleaned_data['tags']
        if not tags_str.strip():
            raise forms.ValidationError('Необходимо указать хотя бы один тег.')
        tag_names = [t.strip().lower() for t in tags_str.split(',') if t.strip()]
        if not tag_names:
            raise forms.ValidationError('Необходимо указать хотя бы один тег.')
        if len(tag_names) > 5:
            raise forms.ValidationError('Максимум 5 тегов.')
        return tag_names

    def save(self, commit=True):
        question = super().save(commit=False)
        if commit:
            question.save()
            self._save_tags(question)
        return question

    def _save_tags(self, question):
        tag_names = self.cleaned_data.get('tags', [])
        for name in tag_names:
            tag, _ = Tag.objects.get_or_create(title=name)
            question.tags.add(tag)


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ('content',)
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Введите ваш ответ...'
            }),
        }

    def clean_content(self):
        content = self.cleaned_data['content']
        if len(content) < 5:
            raise forms.ValidationError('Ответ должен быть не менее 5 символов.')
        return content
import random
import time
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction

from faker import Faker

from questions.models import Tag, Question, Answer, QuestionLike, AnswerLike

fake = Faker('ru_RU')


import re

def translit_slugify(text):
    translit = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e',
        'ё': 'yo', 'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k',
        'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r',
        'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'h', 'ц': 'ts',
        'ч': 'ch', 'ш': 'sh', 'щ': 'sch', 'ъ': '', 'ы': 'y', 'ь': '',
        'э': 'e', 'ю': 'yu', 'я': 'ya'
    }
    text = text.lower()
    result = ''
    for char in text:
        result += translit.get(char, char)
    result = re.sub(r'[^a-z0-9]+', '-', result).strip('-')
    return result or 'tag'



class Command(BaseCommand):
    help = 'Заполняет базу тестовыми данными: python manage.py fill_db [ratio]'

    def add_arguments(self, parser):
        parser.add_argument(
            'ratio',
            type=int,
            default=1,
            help='Коэффициент заполнения'
        )

    def handle(self, *args, **options):
        ratio = options['ratio']
        start_time = time.time()

        total_users = ratio
        total_questions = ratio * 10
        total_answers = ratio * 100
        total_tags = ratio
        total_likes = ratio * 200

        self.stdout.write(f'Ratio: {ratio}')
        self.stdout.write(f'Users: {total_users}')
        self.stdout.write(f'Questions: {total_questions}')
        self.stdout.write(f'Answers: {total_answers}')
        self.stdout.write(f'Tags: {total_tags}')
        self.stdout.write(f'Likes: {total_likes}')
        self.stdout.write('=' * 50)

        self.stdout.write('Creating users...')
        users = self._create_users(total_users)
        user_ids = list(users.values_list('id', flat=True))

        self.stdout.write('Creating tags...')
        tags = self._create_tags(total_tags)
        tag_ids = list(tags.values_list('id', flat=True))

        self.stdout.write('Creating questions...')
        questions = self._create_questions(total_questions, user_ids)
        question_ids = list(questions.values_list('id', flat=True))

        self.stdout.write('Linking questions with tags...')
        self._link_questions_tags(question_ids, tag_ids)

        self.stdout.write('Creating answers...')
        answers = self._create_answers(total_answers, user_ids, question_ids)
        answer_ids = list(answers.values_list('id', flat=True))

        self.stdout.write('Creating question likes...')
        self._create_question_likes(total_likes, user_ids, question_ids)

        self.stdout.write('Creating answer likes...')
        self._create_answer_likes(total_likes, user_ids, answer_ids)

        elapsed = time.time() - start_time
        self.stdout.write(self.style.SUCCESS(
            f'Done in {elapsed:.2f} seconds!'
        ))



    def _create_users(self, count):
        BATCH_SIZE = 1000
        users = []

        existing_count = User.objects.count()
        if existing_count >= count:
            self.stdout.write(f'  Users already exist: {existing_count} >= {count}, skipping')
            return User.objects.all()[:count]

        for i in range(count):
            username = f'{fake.user_name()}_{i}_{random.randint(1, 999999)}'
            while len(username) > 30:
                username = f'{fake.user_name()[:20]}_{i}'

            users.append(User(
                username=username,
                email=fake.email(),
                password='testpass123',
                date_joined=timezone.now() - timedelta(
                    days=random.randint(0, 365)
                ),
            ))

            if len(users) >= BATCH_SIZE:
                User.objects.bulk_create(users)
                self.stdout.write(f'  Created {len(users)} users...')
                users = []

        if users:
            User.objects.bulk_create(users)
            self.stdout.write(f'  Created {len(users)} users (final batch)')

        return User.objects.all()[:count]

    def _create_tags(self, count):
        from django.utils.text import slugify
        
        BATCH_SIZE = 1000
        tags = []
        used_titles = set()

        while len(used_titles) < count:
            title = fake.word()[:50]
            if title not in used_titles:
                used_titles.add(title)

        for title in used_titles:
            tags.append(Tag(
                title=title,
                slug=translit_slugify(title)
            ))

            if len(tags) >= BATCH_SIZE:
                Tag.objects.bulk_create(tags, ignore_conflicts=True)
                tags = []

        if tags:
            Tag.objects.bulk_create(tags, ignore_conflicts=True)

        return Tag.objects.all()[:count]


    def _create_questions(self, count, user_ids):
        BATCH_SIZE = 500
        questions = []

        for i in range(count):
            questions.append(Question(
                title=fake.sentence()[:255],
                content='\n'.join(fake.paragraphs(3)),
                author_id=random.choice(user_ids),
                created_at=timezone.now() - timedelta(
                    days=random.randint(0, 365)
                ),
            ))

            if len(questions) >= BATCH_SIZE:
                Question.objects.bulk_create(questions)
                self.stdout.write(f'  Created {len(questions)} questions...')
                questions = []

        if questions:
            Question.objects.bulk_create(questions)

        return Question.objects.all()[:count]

    def _link_questions_tags(self, question_ids, tag_ids):
        BATCH_SIZE = 5000
        through_model = Question.tags.through
        links = []

        for question_id in question_ids:
            num_tags = random.randint(1, min(5, len(tag_ids)))
            for tag_id in random.sample(tag_ids, num_tags):
                links.append(through_model(
                    question_id=question_id,
                    tag_id=tag_id,
                ))

                if len(links) >= BATCH_SIZE:
                    through_model.objects.bulk_create(links, ignore_conflicts=True)
                    links = []

        if links:
            through_model.objects.bulk_create(links, ignore_conflicts=True)

    def _create_answers(self, count, user_ids, question_ids):
        BATCH_SIZE = 1000
        answers = []

        for i in range(count):
            answers.append(Answer(
                question_id=random.choice(question_ids),
                author_id=random.choice(user_ids),
                content=fake.paragraph(),
                is_correct=random.random() < 0.1,  # 10% правильных
                created_at=timezone.now() - timedelta(
                    days=random.randint(0, 365)
                ),
            ))

            if len(answers) >= BATCH_SIZE:
                Answer.objects.bulk_create(answers)
                self.stdout.write(f'  Created {len(answers)} answers...')
                answers = []

        if answers:
            Answer.objects.bulk_create(answers)

        return Answer.objects.all()[:count]

    def _create_question_likes(self, count, user_ids, question_ids):
        BATCH_SIZE = 5000
        likes = []
        used_pairs = set()

        likes_to_create = count // 2

        while len(likes) < likes_to_create:
            user_id = random.choice(user_ids)
            question_id = random.choice(question_ids)
            pair = (user_id, question_id)

            if pair not in used_pairs:
                used_pairs.add(pair)
                likes.append(QuestionLike(
                    user_id=user_id,
                    question_id=question_id,
                ))

                if len(likes) >= BATCH_SIZE:
                    QuestionLike.objects.bulk_create(
                        likes, ignore_conflicts=True
                    )
                    self.stdout.write(
                        f'  Created {len(likes)} question likes...'
                    )
                    likes = []

        if likes:
            QuestionLike.objects.bulk_create(likes, ignore_conflicts=True)

    def _create_answer_likes(self, count, user_ids, answer_ids):
        BATCH_SIZE = 5000
        likes = []
        used_pairs = set()

        likes_to_create = count // 2

        while len(likes) < likes_to_create:
            user_id = random.choice(user_ids)
            answer_id = random.choice(answer_ids)
            pair = (user_id, answer_id)

            if pair not in used_pairs:
                used_pairs.add(pair)
                likes.append(AnswerLike(
                    user_id=user_id,
                    answer_id=answer_id,
                ))

                if len(likes) >= BATCH_SIZE:
                    AnswerLike.objects.bulk_create(
                        likes, ignore_conflicts=True
                    )
                    self.stdout.write(
                        f'  Created {len(likes)} answer likes...'
                    )
                    likes = []

        if likes:
            AnswerLike.objects.bulk_create(likes, ignore_conflicts=True)
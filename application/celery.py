import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'application.settings')

app = Celery('application')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')


app.conf.beat_schedule = {
    'update-popular-tags': {
        'task': 'questions.tasks.update_popular_tags',
        'schedule': crontab(minute='*/15'),  
    },
    'update-best-members': {
        'task': 'questions.tasks.update_best_members',
        'schedule': crontab(minute='*/15'),  
    },
}
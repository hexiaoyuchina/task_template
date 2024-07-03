from __future__ import absolute_import, unicode_literals    # 保证 celery.py不和library冲突
import os
import logging
import django
from django.conf import settings
from celery import Celery
from celery.signals import after_setup_logger, after_setup_task_logger
from utils.log_helper import MyLoggerHandler
# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'task_template.settings')
django.setup()

app = Celery('task_template')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app config.
# app.autodiscover_tasks()
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS, force=True)


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))



# celery customer logger
class TaskFormatter(logging.Formatter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            from celery._state import get_current_task
            self.get_current_task = get_current_task
        except ImportError:
            self.get_current_task = lambda: None

    def format(self, record):
        task = self.get_current_task()
        if task and task.request:
            workflow_id = ""
            if task.request.kwargs and task.request.kwargs.get('workflow_id'):
                workflow_id = task.request.kwargs.get('workflow_id')
            elif task.request.args and isinstance(task.request.args[0], dict) and task.request.args[0].get('workflow_id'):
                workflow_id = task.request.args[0].get('workflow_id')
            if workflow_id:
                workflow_id = f"{workflow_id}: "
            record.__dict__.update(task_id=task.request.id, task_name=task.name, workflow_id=workflow_id)
        else:
            record.__dict__.setdefault('task_name', '')
            record.__dict__.setdefault('task_id', '')
            record.__dict__.setdefault('workflow_id', '')
        return super().format(record)


def create_celery_logger_handler(logger, propagate):
    celery_handler = MyLoggerHandler(
        filename=settings.LOG_PATH('worker.log'),
        when="D",
        backup_count=365
    )
    celery_formatter = TaskFormatter('%(asctime)s - %(levelname)s - %(task_id)s - %(task_name)s - %(name)s::%(lineno)d'
                                     ' - %(workflow_id)s%(message)s')
    celery_handler.setFormatter(celery_formatter)

    logger.addHandler(celery_handler)
    logger.logLevel = logging.INFO
    logger.propagate = propagate


@after_setup_task_logger.connect
def after_setup_celery_task_logger(logger, **kwargs):
    """ This function sets the 'celery.task' logger handler and formatter """
    create_celery_logger_handler(logger, False)


@after_setup_logger.connect
def after_setup_celery_logger(logger, **kwargs):
    """ This function sets the 'celery' logger handler and formatter """
    create_celery_logger_handler(logger, False)
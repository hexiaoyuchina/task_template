celery -A task_template worker -l info -c 25 -Q task,workflow -f logs/celery.log

celery beat -A task_template -l info -f logs/beat.log

celery -A task_template worker -l info -c 25 -Q task,workflow -f logs/celery.log


celery beat -A task_template -l info -f logs/beat.log

# 查看所有激活队列的
celery -A  task_template inspect active_queues

# 监控

celery -A task_template flower --port=5555

http://localhost:5555

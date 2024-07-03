# 本地指定的celery log日志
celery -A task_template worker -l info -c 25 -Q task,workflow -f logs/celery.log
celery beat -A task_template -l info -f logs/beat.log

# 运行，使用celerylog日志
celery -A task_template worker -l info -c 25 -O fair --without-gossip --without-mingle --without-heartbeat
celery beat -A task_template -l info



# 查看所有激活队列的
celery -A  task_template inspect active_queues

# 监控

celery -A task_template flower --port=5555

http://localhost:5555

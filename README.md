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
# worker 必须加上-E支持监控
celery -A task_template worker -l info -c 25 -O fair -E --without-gossip --without-mingle --without-heartbeat
http://localhost:5555

# 手动插入任务
INSERT INTO task.workflows (id, resource_type, gic_resource_id, phy_resource_id, workflow_type, status, params, `result`, error_step, error_msg, customer_id, user_id, site_id, site_name, charge, suborder_id, recycling_id, recycling_step, depend_id, pri, queue, is_valid, run_env, source_type, created_at, updated_at) VALUES('c22c7a35-32c1-11ef-8a27-1c697a6f532d', 'instance', '28536c1a-32c1-11ef-a7a9-1c697a6f532d', '', 'instance_create', 'waiting', '{"instance_id": "28536c1a-32c1-11ef-a7a9-1c697a6f532d", "core_type": "syadn"}', '{}', NULL, NULL, 'test', 'test', '', '', NULL, '', 0, '', '', 2, 'default', 1, 'test', 'person', '2024-06-25 20:19:40', '2024-06-27 15:00:02');
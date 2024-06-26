import os
import django
from django.conf import settings
from django.db import transaction
from django.db.models import Q

os.environ.setdefault("PROJECT_ENV", "local")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "task_template.settings")
django.setup()
import celery
from celery.utils.log import get_task_logger
from models.qos_template.models import Workflows
from workflow.core.executor import WorkflowExecutor


logger = get_task_logger(__name__)


def handle_workflow(workflow):
    try:
        WorkflowExecutor.execute(workflow)
    except Exception as e:
        import traceback
        workflow.status = workflow.ERROR
        workflow.error_step = Workflows.PREPARE_PARALLEL
        error_msg = traceback.format_exc()
        workflow.error_msg = error_msg
        logger.error(f"{workflow.id}: handle workflow err: {e}", exc_info=True)
        # 处理redis连接的报错, 将任务修改为waiting 进行重试
        if 'redis.exceptions.ConnectionError: Error 32 while writing to socket. Broken pipe.' in error_msg:
            logger.info(
                f"workflow {id} [Error 32 while writing to socket. Broken pipe.], update status error to waiting")
            workflow.status = Workflows.WAITING
        elif 'redis.exceptions.ConnectionError: Error 104 while writing to socket. Connection reset by peer.' in error_msg:
            logger.info(
                f"workflow {id} [Error 104 while writing to socket. Connection reset by peer.], update status error to waiting")
            workflow.status = Workflows.WAITING
        workflow.save(update_fields=['status', 'error_step', 'error_msg'])


@celery.task
def produce_workflows():
    """定时任务，用于查询需要做的任务，并创建该任务的任务链，发送到消息队列，让worker消费做任务"""
    logger.info("produce workflows ....")
    workflows = Workflows.objects.need_do_workflows()
    if not workflows:
        logger.info("no workflows ....")
    else:
        for workflow in workflows:
            handle_workflow(workflow=workflow)


if __name__ == '__main__':
    task = Workflows.objects.get(id='ccee7d7a-c1a4-11ee-97ef-28dfeb2d090f')
    task.status = 'waiting'
    task.run_env = 'test'
    task.save()
    handle_workflow(workflow=task)

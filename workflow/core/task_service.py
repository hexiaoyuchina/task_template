import logging
from celery.result import AsyncResult
from models.qos_template.models import Tasks

logger = logging.getLogger(__file__)


class TaskService:
    def task_prepare(self, workflow_id, task_type, request, params, task_index=0, func_index=0):
        """任务执行前的准备动作

        第一次执行任务，插入任务记录，后续重试动作则会更新celery_task_id，celery_parent_id。
        1、没有子任务，则创建子任务，继续执行
        2、有子任务
            2.1 success状态的不再执行，直接返回成功
            2.2 doing状态根据request_id判断是否还有celery任务，没有则重新执行
            2.3 其余状态重新执行

        Args:
            workflow_id: 工作流id
            task_type: 任务类型
            request: task request
            params: 本次任务汇总参数
            task_index: 同任务批量的序号
        Returns:
            Task obj, run_flag

        Notes:
            request.id: 当前celery子任务id
            request.parent_id: 当前celery子任务所属父任务id
            request.retries: 第几次重试，0代表非重试状态，1代表第一次重试，以此类推
        """
        # task_index: 重新赋值为func_index * 10 + task_index, 为了区分不同批量子任务，使用同名处理函数
        # ex: {"syadn":[('KEY1', func1), ('KEY2', func1)]}, 此处func1同名,需要区分key1和key2的func1
        task_index += func_index * 10
        task = Tasks.objects.filter(workflow_id=workflow_id, task_type=task_type, task_index=task_index)
        if task.exists():
            task = task.first()
        else:
            task = Tasks.objects.create(workflow_id=workflow_id, task_type=task_type, task_index=task_index)

        check_run_handler = {
            Tasks.WAITING: self.check_waiting_run,
            Tasks.DOING: self.check_doing_run,
            Tasks.SUCCESS: self.check_success_run,
            Tasks.ERROR: self.check_error_run
        }.get(task.status, None)

        if callable(check_run_handler):
            run_flag = check_run_handler(workflow_id, task)
        else:
            run_flag = True

        # 重试的任务直接执行
        if int(request.retries) > 1:
            run_flag = True

        # 需要执行任务的话，则更新当前celery task id
        if run_flag:
            task.celery_task_id = request.id
            task.celery_parent_id = request.parent_id
            task.status = Tasks.DOING
            task.params = params
            task.save(update_fields=["celery_task_id", "celery_parent_id", "status", "params"])

        return task, run_flag

    def check_waiting_run(self, workflow_id, task):
        """检查waiting状态下的任务是否需要执行
        """
        logger.info(f"task {task.id} is waiting status, run_flag: True!!!")
        return True

    def check_doing_run(self, workflow_id, task):
        """"检查doing状态下的任务是否需要执行
        """
        celery_task_id = task.celery_task_id
        AsyncResult(celery_task_id)
        logger.info(f"task {task.id} is doing status, run_flag: True!!!")
        return True

    def check_success_run(self, workflow_id, task):
        """检查success状态下的任务是否需要执行
        """
        logger.info(f"task {task.id} is success status, skip!!!")
        return False

    def check_error_run(self, workflow_id, task):
        """检查error状态下的任务是否需要执行
        """
        logger.info(f"task {task.id} is error status, run_flag: True!!!")
        return True

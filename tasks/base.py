
import logging
import time

import celery
from copy import deepcopy
from workflow.core.base_celery import BaseCeleryTask
from common.exception import RetryException
# from utils.http_api_kit import RequestAPI
from models.qos_template.models import Workflows, Tasks

logger = logging.getLogger(__name__)


class BaseTask(BaseCeleryTask):
    """注册为celery函数， 类继承的方式运行，注册celery任务时，指定基类"""
    workflow_id = None
    task_id = None
    task_type = None
    task_index = 0
    task_param = None

    def __call__(self, *args, **kwargs):
        """执行celery任务前需要做的事情"""
        logger.info(f"current queue: {self.Q}")
        logger.info(f"Start task {self.name} args: {args} kwargs: {kwargs}")
        self.workflow_id = kwargs.get("workflow_id")
        self.task_param = kwargs.get("task_params", {})
        self.task_index = kwargs.get("task_index", 0)
        self.func_index = kwargs.get("func_index", 0)
        self.task_type = self.name.split('.')[-1]
        name = self.task_type
        try:
            # celery request属性：1. 当开始执行任务的时候，self.requests.reties被设置为0，说明任务开始执行。
            # 2. 当内部调用self.retry()来进行重试时，同一个request会被同一个worker再次执行。这时，self.request.reties变为1.
            # 总结来说，task开始执行时，self.request.reties的下标为0，第n尝试时，self.request.reties的下标为n。
            retry = int(self.request.retries)
            if retry > 0:
                name = f"{self.task_type}_{retry}"
        except Exception as e:
            name = self.task_type

        # 构建本次用到的params，参数来源是上次的任务返回，或prepare阶段的返回, 该方法处于父类
        self.params = self.build_params(deepcopy(args[0]))
        parallel_params_key = kwargs.get("parallel_params_key", None)
        if parallel_params_key:
            self.task_param.update(self.params.get(parallel_params_key)[self.task_index])
        self.params.update(self.task_param)
        self.callback_service = self.params.get("callback_service")

        try:
            # 创建子任务记录
            task, need_run = self.task_service.task_prepare(
                self.workflow_id,
                self.task_type,
                self.request,
                self.params,
                self.task_index,
                self.func_index
            )
            self.task_id = task.id
            logger.info(f"task {task.id} type {name} need run is {need_run}")
            if need_run:
                # 运行celery任务
                result = super().__call__(*args, **kwargs) or {}
            else:
                result = task.result

            Tasks.objects.update_to_success(self.task_id, result)
            logger.info(f"End task {self.name} and finish it")
            return {
                'result': {self.task_type: result},
                'params': self.params
            }

        except RetryException as e:
            retry = int(self.request.retries) + 1
            logger.error(f"task {self.task_id} start retry {retry} error {e}")
            self.retry(exc=e, countdown=retry * 2)
        except Exception as e:
            logger.error(f"task {self.task_id} error: {e}")
            raise

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        return super().after_return(status, retval, task_id, args, kwargs, einfo)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"on_failure, exc: {exc}, einfo: {einfo}, self.params: {self.params}")
        Tasks.objects.update_to_error(self.task_id, einfo)
        error_info = str(einfo)
        if 'redis.exceptions.ConnectionError: Error 32 while writing to socket. Broken pipe.' in error_info or \
                'redis.exceptions.ConnectionError: Error 104 while writing to socket. Connection reset by peer.' in error_info:
            logger.info(f"workflow {self.workflow_id} get redis connection error, update status to waiting")
            time.sleep(3)
            Workflows.objects.update_status(self.workflow_id, Workflows.WAITING)
            return
        Workflows.objects.update_to_error(self.workflow_id, Workflows.PROCESS, einfo)
        # RequestAPI.access_wan_service_callback(self.workflow_id)
        return super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        Tasks.objects.retry_plus_1(self.task_id)
        return super().on_retry(exc, task_id, args, kwargs, einfo)


@celery.task(bind=True, base=BaseTask, Q="task")
def pass_task(self, *args, **kwargs):
    return {"step": "pass"}
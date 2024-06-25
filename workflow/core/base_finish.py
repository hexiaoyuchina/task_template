import logging
import time

from workflow.core.base_celery import BaseCeleryTask
from models.qos_template.models import Workflows

logger = logging.getLogger(__name__)


class BaseFinish(BaseCeleryTask):
    def __call__(self, *args, **kwargs):
        """调用任务类需要做的事情"""
        logger.info(f"workflow finish({self.name}) start! args: {args} kwargs: {kwargs}")

        self.workflow_id = kwargs.get('workflow_id')
        # 构建本次用到的params，参数来源是上次的任务返回，位于args[0], 类型为字典或列表
        self.params = self.build_params(args[0])
        self.callback_service = self.params.get('callback_service')
        workflow = Workflows.objects.get_workflow(self.workflow_id)

        if 'finish' not in workflow.result or workflow.error_step == Workflows.FINISH:
            result = super().__call__(*args) or {}
        else:
            logger.info(f"finish step is success status, skip!!!")
            result = workflow.result.get('finish')

        # 由on_success处搬上来，原因：on_success目前非串行
        Workflows.objects.update_finish_result(self.workflow_id, result, Workflows.SUCCESS)

        logger.info(f"workflow finish({self.name}) end!")

        return {
            'result': result,
            'params': self.params
        }

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        logger.info('{0!r} after return: {1!r}'.format(task_id, status))
        # if self.callback_service == 'network-logic':
        #     RequestAPI.access_network_logic(self.workflow_id)
        # else:
        #     RequestAPI.access_wan_service_callback(self.workflow_id)
        return super().after_return(status, retval, task_id, args, kwargs, einfo)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"on_failure, exc: {exc}, einfo: {einfo}, self.params: {self.params}")
        error_info = str(einfo)
        if 'redis.exceptions.ConnectionError: Error 32 while writing to socket. Broken pipe.' in error_info or \
                'redis.exceptions.ConnectionError: Error 104 while writing to socket. Connection reset by peer.' in error_info:
            logger.info(f"workflow {self.workflow_id} get redis connection error, update status to waiting")
            time.sleep(3)
            Workflows.objects.update_status(self.workflow_id, Workflows.WAITING)
            return
        Workflows.objects.update_to_error(self.workflow_id, Workflows.FINISH, einfo)
        return super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        return super().on_retry(exc, task_id, args, kwargs, einfo)

    def on_success(self, retval, task_id, args, kwargs):
        return super().on_success(retval, task_id, args, kwargs)

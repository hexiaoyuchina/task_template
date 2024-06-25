import logging
import time

from workflow.core.base_celery import BaseCeleryTask
from models.qos_template.models import Workflows

logger = logging.getLogger(__name__)


class BasePrepare(BaseCeleryTask):
    def __call__(self, *args, **kwargs):
        """调用任务类需要做的事情"""
        logger.info(f"workflow prepare({self.name}) start! args: {args} kwargs: {kwargs}")

        self.workflow_id = kwargs.get('workflow_id')
        workflow = Workflows.objects.get_workflow(self.workflow_id)
        # self.params = workflow.params
        self.params = kwargs.get('params')
        # 必须的参数
        self.params.update(
            {
                "customer_id": workflow.customer_id,
                "site_id": workflow.site_id
            }
        )
        if 'prepare' not in workflow.result or workflow.error_step == Workflows.PREPARE:
            result = super().__call__(*args) or {}
        else:
            logger.info(f"prepare step is success status, skip!!!")
            result = workflow.result.get('prepare')

        # 由on_success处搬上来，原因：on_success目前非串行
        # 更新prepare处理的结果到result字段里,同时状态转到下一个 prepare -> process
        Workflows.objects.update_prepare_result(id=self.workflow_id, result=result, status=Workflows.PROCESS)

        logger.info(f"workflow prepare({self.name}) done!")

        return {
            'result': result,
            'params': self.params
        }

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
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
        Workflows.objects.update_to_error(self.workflow_id, Workflows.PREPARE, einfo)
        return super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        return super().on_retry(exc, task_id, args, kwargs, einfo)

    def on_success(self, retval, task_id, args, kwargs):
        return super().on_success(retval, task_id, args, kwargs)



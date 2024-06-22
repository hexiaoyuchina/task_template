import logging

import celery
from celery.worker.request import Request
from workflow.core.failure import Failure
from workflow.core.task_service import TaskService
logger = logging.getLogger(__file__)


class BaseRequest(Request):
    """
    通用request
    """

    def on_timeout(self, soft, timeout):
        super().on_timeout(soft, timeout)
        if not soft:
            logger.warning(f'A hard timeout was enforced for task {self.task.name}')

    def on_failure(self, exc_info, send_failed_event=True, return_ok=False):
        super().on_failure(
            exc_info,
            send_failed_event=send_failed_event,
            return_ok=return_ok
        )
        logger.warning(f'Failure detected for task {self.task.name}')


class BaseCeleryTask(celery.Task):
    """
    celery 类继承注册celery类， 注册任务时指定基类
    """
    Request = BaseRequest
    task_service = TaskService()

    def build_params(self, result):
        """
        把上个步骤的结果合并到通用self.params里
        Args:
            result: 上个任务的结果，dict格式，key包含result和params，result为上个任务的返回结果，params为任务链到此步骤汇集的结果
        Returns: params
            赋值到self.params
        """
        try:
            if isinstance(result, dict):
                params = result.get('params')
                params.update(result.get('result'))
            elif isinstance(result, list):
                # 上游任务是group，则返回list
                # params默认取第一个
                params = result[0].get('params')
                for r in result:
                    for k, v in r.get('result').items():
                        if k in params:
                            if not isinstance(params[k], list):
                                params[k] = [params[k]]
                            params[k].append(v)
                        else:
                            params[k] = v
            else:
                raise TypeError(f"子任务的返回必须是dict or list类型 err:{type(result)}")
            return params
        except Exception as e:
            logger.error(f"task build_params failed: {e}")
            raise

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        return super().after_return(status, retval, task_id, args, kwargs, einfo)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        failure_op = Failure(self.workflow_id, exc, task_id, args, kwargs, einfo)
        failure_op.main()
        return super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        return super().on_retry(exc, task_id, args, kwargs, einfo)

    def on_success(self, retval, task_id, args, kwargs):
        return super().on_success(retval, task_id, args, kwargs)

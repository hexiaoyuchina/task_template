import logging
import functools
from celery import Task, task, chain, group
from models.qos_template.models import Workflows
logger = logging.getLogger(__file__)


class Workflow:
    """
    任务流基类
    任务流基类，将函数注册为celery任务的功能函数
        Attributes:
            queue (str): 任务流步骤任务使用的队列
            prepare_step (celery.task): 任务流过程中的准备步骤
            build_step (celery.task's chain): 任务流过程中的任务执行步骤
            finish_step (celery.task): 任务流过程中的成功回调步骤
    """

    queue = 'workflow'
    prepare_step = None
    build_step = None
    finish_step = None
    task_params = None


    @classmethod
    def prepare_decorator(cls, prepare_func):
        """装饰器：将任务类中的prepare函数注册为celery任务"""
        cls.prepare_step = make_task(prepare_func, queue=cls.queue)
        return cls.prepare_step

    @classmethod
    def build_decorator(cls, build_func):
        """装饰器：将任务类中的build函数注册为celery任务"""
        pass

    @classmethod
    def finish_decorator(cls, finish_func):
        """装饰器：将任务类中的finish函数注册为celery任务"""
        @functools.wraps(finish_func)
        def _finish(self, *args):
            Workflows.objects.update_status(self.worflow_id, Workflows.FINISH)
            return finish_func(self)
        cls.finish_step = make_task(_finish, queue=cls.queue)
        return cls.finish_step


def make_task(func, queue):
    """包装为celery task
    传入的参数会包装为类属性，每个步骤会继承于各步骤处理的父类，便于统一处理

    Args:
        func: 任务流步骤功能函数
        queue: 任务流步骤所使用的队列
    Returns:
        celery task
    Notes:
        步骤函数名称必须按如下定义，目前有 prepare，build，finish
        后续再增加其他处理步骤，这里要同步添加
    """
    from workflow.core.base_prepare import BasePrepare
    from workflow.core.base_finish import BaseFinish
    step = {
        "prepare": BasePrepare,
        "finish": BaseFinish
    }
    # 注册任务的名称
    name = "{}.{}".format(func.__module__, func.__name__)
    base_class = step.get(func.__name__) if func.__name__ in step else Task

    @task(bind=True, base=base_class, name=name, queue=queue, options={"queue": queue})
    def cel_task(self, *args, **kwargs):
        return func(self, *args, **kwargs)
    return cel_task

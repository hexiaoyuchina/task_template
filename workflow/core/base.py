import logging
import functools
from celery import Task, task, chain, group
from models.qos_template.models import Workflows
from common.exception import ParamsNotValidException, WorkflowSyntaxException, TaskSignatureException
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
        @functools.wraps(build_func)
        def _build(**kwargs):
            # 执行任务传进来的参数
            site_id = kwargs.get("site_id")
            core_type = kwargs.get("params").get("core_type")
            cls.task_params = kwargs.get("params", {})
            if not core_type:
                raise ParamsNotValidException("未定义core_type")
            task_dict = build_func(cls)
            if not isinstance(task_dict, dict) or not isinstance(task_dict.get(core_type), list):
                raise WorkflowSyntaxException("build 函数必须指定格式构建任务列表")

            task_func = task_dict.get(core_type)
            workflow_id = kwargs.get("workflow_id")
            params = kwargs.get("params")
            tasks = []
            pre_func = None
            for func_index, func in enumerate(task_func):
                if not isinstance(func, Task) and not isinstance(func, tuple) and type(func)==type(pre_func):
                    # celery的限制，两个并行列表，提示需要合并，需要使用pass_task隔离
                    raise WorkflowSyntaxException("构建并行子任务时错误，挨在一起的并行任务需要合并")
                pre_func = func

                # 不同的任务并行
                if isinstance(func, list):
                    # 任务链，将celery任务创建成签名，使用签名执行任务，
                    # signature（签名 Subtask 子任务） 方法将函数和参数打包起来成为一个 signature （签名）对象，
                    # 在这个对象中可以保存函数的参数以及任务执行的参数。
                    group_funcs = [task_s(task=f, workflow_id=workflow_id) for f in func]
                    # 将一组任务作为原子任务,group 函数也接受一个任务列表，这些任务会同时加入到任务队列中，且执行顺序没有任何保证
                    tasks.append(group(group_funcs))
                    continue

                # 相同的任务，多个资源并行
                if isinstance(func, tuple):
                    func = list(func)
                    sub_group_key = func.pop(0)  # 批量参数名，当前资源的相关顺序子任务
                    group_funcs = []  # 多资源的子任务并行处理
                    if sub_group_key not in params:
                        raise WorkflowSyntaxException(f"构建并行子任务失败， 指定参数{sub_group_key}不存在")

                    if not isinstance(params.get(sub_group_key), list):
                        raise WorkflowSyntaxException(f"构建并行子任务失败， 指定参数{sub_group_key}应该返回list")

                    for i, p in enumerate(params.get(sub_group_key)):  # 批量任务参数
                        # 单个资源的任务处理流程
                        chain_funcs = [
                            task_s(  # celery任务变成签名
                                task=f,
                                workflow_id=workflow_id,
                                task_index=i,
                                task_params=p,
                                parallel_params_key=sub_group_key,
                                func_index=func_index+1
                            ) for f in func
                        ]
                        # 单资源的任务链
                        group_funcs.append(chain(*chain_funcs))
                    if group_funcs:  # 多资源饿任务链，使用任务组，作为一组原子任务执行，执行顺序无先后
                        tasks.append(group(group_funcs))
                    continue
                # 单个任务
                if not isinstance(func, Task):
                    raise WorkflowSyntaxException(f"函数 {func.__name__}不是一个celery任务 ")
                tasks.append(chain(task_s(task=func, workflow_id=workflow_id, func_index=func_index+1)))
            logger.info(f"build tasks: {tasks}")
            return tasks

        cls.build_step = _build
        return cls.build_step

    @classmethod
    def finish_decorator(cls, finish_func):
        """装饰器：将任务类中的finish函数注册为celery任务"""
        @functools.wraps(finish_func)
        def _finish(self, *args):
            Workflows.objects.update_status(self.workflow_id, Workflows.FINISH)
            return finish_func(self)
        cls.finish_step = make_task(_finish, queue=cls.queue)
        return cls.finish_step

    # 执行任务
    @classmethod
    def signature(cls, **kwargs):
        """任务入口: workflow_id=workflow.id, site_id=workflow.site_id, params=params"""
        return chain_task(cls.prepare_step, cls.build_step, cls.finish_step, kwargs)


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


def task_s(**kwargs):
    """
            s签名
            签名后才能作为workflow流的一部分
        :param kwargs:
        :return:
        """
    if "task" not in kwargs:
        raise TaskSignatureException(f"task step {kwargs} become workflow need task params")
    task = kwargs.pop("task")
    queue = task.Q
    pri = kwargs.pop("priority", 3)
    # signature('tasks.add', args=(2, 2), countdown=10)  任务名称，参数等
    # 不能通过 s() 定义执行选项，但是可以通过 set 的链式调用解决
    # 快捷方法： add.s(2, 2).set(countdown=1)
    return task.s(**kwargs).set(queue=queue, priority=pri)  # 创建签名的快捷方法


def task_step(build_step, kwargs):
    """返回工作流任务处理链

    Args:
        build_step: build function
        kwargs:
    Returns:
        celery task chain
    """
    return build_step(**kwargs)


def log_celery_tasks(chord_task, prefix=''):
    for index, task in enumerate(chord_task.tasks):
        if task.subtask_type in ('chord', 'group'):
            log_celery_tasks(task, f'{prefix}{index}==')
        elif task.subtask_type == 'chain':
            log_celery_tasks(task, f'{prefix}{index}--')
        else:
            logger.info(f'{prefix}{task.name}')


def chain_task(prepare_step, build_step, finish_step, kwargs):
    """按规定的顺序组装任务流处理步骤
    Args:
        prepare_step (celery.task): workflow prepare function wrapped by celery.task
        build_step (celery.task): workflow build function (Note: The result of this function is chain, No need to wrap)
        finish_step (celery.task): workflow finish function wrapped by celery.task
        kwargs (dict): workflow params
    Returns:
        flow task chain
    """
    prepare_sig = chain(prepare_step.si(**kwargs))
    build_sig_list = task_step(build_step, kwargs)
    finish_sig = chain(finish_step.s(**kwargs))
    workflow_chain = chain(prepare_sig, *build_sig_list, finish_sig)

    logger.info(f'======workflow chain {kwargs.get("workflow_id")}======')
    log_celery_tasks(workflow_chain)
    logger.info('===========================end============================')

    return workflow_chain


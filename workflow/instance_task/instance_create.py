from workflow.core.register_task import register_workflow
from workflow.core.base import Workflow
from service.instance.instance_service import InstanceService
from tasks.syadn.instance import instance_create_task, db_instance_create_task, test_task
from tasks.base import pass_task

"""
register_workflow装饰器：
    将prepare， finish: 注册为celery任务流
    将build中多资源的celery任务，创建签名，并创建任务链及任务组
"""


@register_workflow("instance_create")
class InstanceCreate(Workflow):
    @classmethod
    def params_schema(cls):
        # 任务执行参数校验
        return {
            'instance_id': {'type': 'string'}
        }

    # 执行celery任务时进行参数获取
    @staticmethod
    def prepare_parallel(params):
        instance_id = params.get("instance_id")
        every_obj_param_list = InstanceService.get_all_obj_params(instance_id)
        return {
            'every_obj_param_list': every_obj_param_list,
            'test_tasks': [{"name": 1}, {"name": 2}]

        }

    def prepare(self):
        return {"prepare_param": "test"}

    def build(self):
        return {
            # syadn ： core_type
            'syadn': [
                ('every_obj_param_list', instance_create_task, db_instance_create_task),
                pass_task,
                ('test_tasks', test_task)
            ]
        }

    def finish(self):
        pass

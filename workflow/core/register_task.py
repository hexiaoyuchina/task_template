from common.exception import RegisterWorkflowException

REGISTER_WORKFLOWS = {}


def register_workflow(workflow_type):
    """

    :param workflow_type: 任务类型
    :return:
    类装饰器，将工作流类注册成celery任务，然后将步骤函数组成任务链及组
    """
    print("register task %s" % workflow_type)

    def decorator(cls):
        if workflow_type in REGISTER_WORKFLOWS:
            RegisterWorkflowException(f"工作流类名称重复{workflow_type}, 请确保唯一")
        # 基类函数（任务流类函数）
        cls.prepare_decorator(cls.prepare)
        cls.bulid_decorator(cls.build)
        cls.finish_decorator(cls.finish)
        REGISTER_WORKFLOWS[workflow_type] = cls
        return cls
    return decorator()


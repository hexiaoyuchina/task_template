from common.exception import RegisterWorkflowException

REGISTER_WORKFLOWS = {}


def register_workflow(workflow_type):
    """

    :param workflow_type: 任务类型
    :return:
    类装饰器，使用基类中的函数装饰器，将工作流类中的函数注册成celery任务，然后将步骤函数组成任务链
    """
    print("register task %s" % workflow_type)

    def decorator(cls):
        if workflow_type in REGISTER_WORKFLOWS:
            RegisterWorkflowException(f"工作流类名称重复{workflow_type}, 请确保唯一")
        # 基类函数（任务流类函数）
        cls.prepare_decorator(cls.prepare)  # 注册为celery任务
        cls.bulid_decorator(cls.build)  # 注册为celery任务
        cls.finish_decorator(cls.finish)  # 组建子任务链，多资源变成任务组执行，函数定义时注册为celery任务
        REGISTER_WORKFLOWS[workflow_type] = cls
        return cls
    return decorator()


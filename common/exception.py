class RegisterWorkflowException(Exception):
    """
        注册工作流异常
    """


class ParamsNotValidException(TypeError):
    """
        参数不合法异常
    """


class WorkflowSyntaxException(Exception):
    """
        工作流语法错误
    """


class TaskSignatureException(Exception):
    """
    celery任务创建签名错误
    """
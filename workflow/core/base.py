class Workflow:
    """
    任务流基类
    """
    @classmethod
    def prepare_decorator(cls, prepare_func):
        pass

    @classmethod
    def build_decorator(cls, build_func):
        pass

    @classmethod
    def finish_decorator(cls, finish_func):
        pass


import logging

import celery
from celery.worker.request import Request


class BaseCeleryTask(celery.Task):
    """
    celery 类继承注册celery类， 注册任务时指定基类
    """
    pass

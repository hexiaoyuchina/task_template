from __future__ import absolute_import, unicode_literals

# 这确保了在 Django 启动时加载应用程序，以便celery任务装饰器将使用这个文件
from .celery import app as celery_app

__all__ = ('celery_app',)

import logging
import time

from workflow.core.base_celery import BaseCeleryTask
from models.qos_template.models import Workflows

logger = logging.getLogger(__name__)


class BasePrepare(BaseCeleryTask):
    def __call__(self, *args, **kwargs):
        """调用任务类需要做的事情"""
        pass



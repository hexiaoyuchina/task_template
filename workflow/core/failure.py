# -*- coding: utf-8 -*-
# @Time    : 2019-12-4 11:45

import logging

from django.db import transaction

from models.gic.models import Instance
from models.qos_template.models import Workflows, Tasks
from workflow.core.register_task import REGISTER_WORKFLOWS

logger = logging.getLogger(__name__)


class Failure:
    """
        任务失败处理类
    """

    def __init__(self, workflow_id, exc, task_id, args, kwargs, einfo):
        self.workflow_id = workflow_id
        self.exc = exc
        self.celery_task_id = task_id
        self.args = args
        self.kwargs = kwargs
        self.einfo = einfo
        self.einfo_repr = repr(einfo)
        self._workflow = None
        self.gic_resource_error_op_dict = {
            'instance': self.instance_error_op
        }

    @property
    def workflow(self):
        if self._workflow is None:
            self._workflow = Workflows.objects.get_workflow(self.workflow_id)
        return self._workflow

    def main(self):

        gic_resource_error_op = self.gic_resource_error_op_dict.get(self.workflow.resource_type, None)
        if gic_resource_error_op is not None:
            logger.info(f'修改{self.workflow.resource_type}上层表状态为error')
            gic_resource_error_op()

        workflow_cls = REGISTER_WORKFLOWS.get(self.workflow.workflow_type, None)
        if hasattr(workflow_cls, 'on_failure'):
            logger.info(f'处理{self.workflow.workflow_type}任务错误回调')
            params = self.workflow.params
            params.update(workflow_id=self.workflow_id)
            params.update(self.workflow.result.get('parallel_params', {}))
            params.update(self.workflow.result.get('prepare', {}))
            workflow_cls.on_failure(params)

    def instance_error_op(self):
        with transaction.atomic():
            Instance.objects.filter(id=self.workflow.gic_resource_id).update(status='error')

# -*- coding: utf-8 -*-
# @Time    : 2019-12-4 11:45

import logging

from django.db import transaction

from models.gic.models import NsxVpc, Pipe, App, GPN, GlobalSSHLink
from models.coreTasker.models import Workflows, Tasks
from models.gic.models import Task as GicTask
from models.automatic_product.models import Task as ATask
from common.mixin.register import REGISTER_WORKFLOWS

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
            'VPC': self.vpc_error_op,
            'subnet': self.subnet_error_op,
            'gpn': self.gpn_error_op,
            'global_ssh': self.global_ssh_error_op,
        }

    @property
    def workflow(self):
        if self._workflow is None:
            self._workflow = Workflows.objects.get_workflow(self.workflow_id)
        return self._workflow

    def main(self):
        GicTask.objects.update_to_error(self.workflow_id, self.einfo_repr)
        ATask.objects.update_to_error(self.workflow_id, self.einfo_repr[:1000])
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

    def vpc_error_op(self):
        with transaction.atomic(using="cdscp"):
            NsxVpc.objects.filter(id=self.workflow.gic_resource_id).update(status='error')
            App.objects.filter(id=self.workflow.gic_resource_id).update(create_status=2)

    def subnet_error_op(self):
        Pipe.objects.filter(pk=self.workflow.gic_resource_id).update(status='error')

    def gpn_error_op(self):
        GPN.objects.filter(pk=self.workflow.gic_resource_id).update(status='error')

    def global_ssh_error_op(self):
        GlobalSSHLink.objects.filter(pk=self.workflow.gic_resource_id).update(status='error')

    def retry_redis_broken_pipe_error(self):
        error_info = str(self.einfo)
        if 'redis.exceptions.ConnectionError: Error 32 while writing to socket. Broken pipe.' in error_info:
            logger.info(f"workflow {id} get Broken pipe error, update status error to waiting")
            self.workflow.status = Workflows.WAITING
            self.workflow.save(update_fields=["status"])
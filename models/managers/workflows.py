import datetime
import time
import logging
from django.db import transaction
from django.db.models import Manager, Q
from django.conf import settings
from common.exception import ObjectDoesNotExistException
logger = logging.getLogger(__file__)


class WorkflowsManager(Manager):
    def need_do_workflows(self):
        """
            获取待执行的工作流任务
        :return:
        """
        return self.select_related('depend').filter(
            Q(status=self.model.WAITING, run_env=settings.RUN_ENV, is_valid=1) &
            (
                    Q(depend=None) |
                    Q(depend='') |
                    Q(depend__status=self.model.SUCCESS)
            )
        ).order_by('pri').order_by('created_at')[:50]

    def update_status(self, id, status):
        """
            更改工作流状态
        :param id:
        :param status:
        :return:
        """
        workflow = self.get_workflow(id)
        workflow.status = status
        workflow.updated_at = datetime.datetime.now()
        workflow.save(update_fields=["status", "updated_at"])

    def set_to_prepare(self, id):
        with transaction.atomic(using="task"):
            workflow = self.using('task').select_for_update().get(id=id)
            if workflow.status != self.model.WAITING:
                logger.info(f"{workflow.id}: Workflow is not waiting and will not execute, "
                            f"May be executed by other workers!")
                return False
            workflow.status = self.model.PREPARE
            workflow.save(update_fields=["status"])
        return workflow

    def update_to_error(self, id, error_step, error_msg):
        """
            置主工作流失败
        :param id:
        :param error_step:
        :param error_msg:
        :return:
        """
        workflow = self.get_workflow(id)
        workflow.error_step = error_step
        workflow.error_msg = error_msg
        workflow.status = self.model.ERROR
        workflow.updated_at = datetime.datetime.now()
        workflow.save(update_fields=["error_step", "error_msg", "status", "updated_at"])

    def update_prepare_result(self, id, result, status=None):
        """
        设置prepare结果
        :param id:
        :param result:
        :param status:
        :return:
        """
        update_fields = ["result"]
        workflow = self.get_workflow(id)
        workflow.result.update({'prepare': result})
        if status:
            workflow.status = status
            update_fields.append("status")
        workflow.save(update_fields=update_fields)

    def update_finish_result(self, id, result, status=None):
        """
        设置finish结果
        :param id:
        :param result:
        :param status:
        :return:
        """
        update_fields = ["result"]
        workflow = self.get_workflow(id)
        workflow.result.update({'finish': result})
        if status:
            workflow.status = status
            update_fields.append("status")
        workflow.save(update_fields=update_fields)

    def get_workflow(self, workflow_id):
        retry = 3
        while True:
            try:
                return self.get(id=workflow_id)
            except ObjectDoesNotExistException:
                if retry > 0:
                    time.sleep(1)
                    retry -= 1
                else:
                    raise

    def create_new_workflow(self, workflow_id, workflow_type, resource_type, gic_resource_id, phy_resource_id, params,
                            customer_id, user_id, site_id, site_name, suborder_id, recycling_id, recycling_step,
                            depend_id, source_type, run_env, status='waiting'):
        self.create(
            id=workflow_id,
            workflow_type=workflow_type,
            resource_type=resource_type,
            gic_resource_id=gic_resource_id,
            phy_resource_id=phy_resource_id,
            params=params,
            customer_id=customer_id,
            user_id=user_id,
            site_id=site_id,
            site_name=site_name,
            suborder_id=suborder_id,
            recycling_id=recycling_id,
            recycling_step=recycling_step,
            depend_id=depend_id,
            source_type=source_type,
            run_env=run_env,
            status=status
        )
import datetime
import logging
from django.db import transaction
from django.db.models import Manager, Q
from django.conf import settings
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


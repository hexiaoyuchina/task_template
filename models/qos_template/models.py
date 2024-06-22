
import jsonfield
from django.db import models

from models.managers.workflows import WorkflowsManager
from models.managers.tasks import TasksManager
from utils import create_uuid


class Workflows(models.Model):
    """
        主任务表
    """
    WAITING = "waiting"
    WAIT_FOR_AGGREGATING = "wait_for_aggregating"
    AGGREGATING = "aggregating"
    PREPARE_PARALLEL = "prepare_parallel"
    PREPARE = "prepare"
    PROCESS = "process"
    FINISH = "finish"
    SUCCESS = "success"
    ERROR = "error"

    WORKFLOW_STATUS = (
        (WAITING, "等待中"),
        (PREPARE, "准备中"),
        (PROCESS, "执行中"),
        (FINISH, "结束中"),
        (SUCCESS, "成功"),
        (ERROR, "失败")
    )

    id = models.CharField(u"UID", max_length=36, primary_key=True, default=create_uuid)
    resource_type = models.CharField("resource type", max_length=64, null=False, blank=False)
    gic_resource_id = models.CharField("gic resource id", max_length=36, null=False, blank=False)
    phy_resource_id = models.CharField("physical resource id", max_length=36, null=False, blank=False)
    workflow_type = models.CharField(u"操作类型", default="createVpc", null=True, blank=True, max_length=32)
    status = models.CharField(u"主任务状态", max_length=32, default="waiting", choices=WORKFLOW_STATUS)
    params = jsonfield.JSONField(u"参数", default={}, null=True, blank=True)
    result = jsonfield.JSONField(u"结果", default={}, null=True, blank=True)
    error_step = models.CharField(u"错误所在的步骤", max_length=32, null=True, blank=True)
    error_msg = models.TextField(u"错误信息", null=True, blank=True)
    customer_id = models.CharField(u"客户ID", max_length=36, default="")
    user_id = models.CharField(u"用户ID", max_length=36, default="")
    site_id = models.CharField(u"节点ID", max_length=36, null=True, blank=True)
    site_name = models.CharField(u"节点名称", max_length=36, null=True, blank=True)
    charge = models.CharField("订单回调结果", max_length=16, null=True, blank=True, default=None)
    suborder_id = models.CharField("子订单id", max_length=36, null=True, blank=True, default='')
    recycling_id = models.IntegerField("回收任务id", null=True, default=None)
    recycling_step = models.CharField('回收步骤', max_length=36, null=True, blank=True, default=None)
    depend = models.ForeignKey("Workflows", on_delete=models.DO_NOTHING, null=True, blank=True, default=None)
    pri = models.IntegerField(u"优先级", default=2)
    queue = models.CharField(u"队列", max_length=16, default="default")
    is_valid = models.BooleanField(u"是否有效", default=True)
    source_type = models.CharField("任务来源", max_length=16, null=False, blank=False)
    run_env = models.CharField("运行环境", max_length=36, default="pro")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = WorkflowsManager()

    class Meta:
        manage = False
        app_label = "task"
        db_table = "workflows"

    def __unicode__(self):
        return "id:%s, type:%s" % (self.id, self.workflow_type)


class Tasks(models.Model):
    """
        工作流任务表
    """
    WAITING = "waiting"
    DOING = "doing"
    SUCCESS = "success"
    ERROR = "error"

    TASK_STATUS = (
        (WAITING, "等待中"),
        (DOING, "执行中"),
        (SUCCESS, "成功"),
        (ERROR, "失败")
    )

    id = models.CharField(u"UID", max_length=36, primary_key=True, default=create_uuid)
    workflow = models.ForeignKey(Workflows, on_delete=models.DO_NOTHING)
    task_type = models.CharField(u"任务操作类型", null=True, blank=True, max_length=128)
    task_index = models.IntegerField(u"同任务批量的序号", default=0)
    status = models.CharField(u"子任务状态", max_length=32, default="waiting", choices=TASK_STATUS)
    params = jsonfield.JSONField(u"参数", default={}, null=True, blank=True)
    result = jsonfield.JSONField(u"结果", default={}, null=True, blank=True)
    error_msg = models.TextField(u"错误信息", null=True, blank=True)
    retry = models.IntegerField(u"错误信息", default=0)
    celery_task_id = models.CharField(u"celery任务ID", max_length=36, null=True, blank=True)
    celery_parent_id = models.CharField(u"兄弟任务ID", max_length=36, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TasksManager()

    class Meta:
        manage = False
        app_label = "task"
        db_table = "tasks"

    def __unicode__(self):
        return "p:%s, c: %s" % (self.workflow_id, self.id)

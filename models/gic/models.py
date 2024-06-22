
import jsonfield
from django.db import models

from models.managers.workflows import WorkflowsManager
from models.managers.tasks import TasksManager
from utils import create_uuid


class Instance(models.Model):
    id = models.CharField(u"UID", max_length=36, primary_key=True, default=create_uuid)
    name = models.CharField(max_length=36, default="")
    status = models.CharField(max_length=20)
    class Meta:
        manage = False
        app_label = "task"
        db_table = "instance"
import time
import datetime
from django.db.models import F
from django.db.models import Manager
from common.exception import ObjectDoesNotExistException


class TasksManager(Manager):
    def retry_plus_1(self, id):
        """
            失败重试+1
        :return:
        """
        self.filter(id=id).update(retry=F('retry') + 1)

    def update_to_success(self, id, result):
        """
            置任务成功
        :param id:
        :param result:
        :return:
        """
        retry = 0
        while retry < 3:
            try:
                task = self.get(id=id)
                task.result = result
                task.status = self.model.SUCCESS
                task.updated_at = datetime.datetime.now()
                task.save(update_fields=["result", "status", "updated_at"])
                break
            except ObjectDoesNotExistException:
                time.sleep(1)
                retry += 1

    def update_to_error(self, id, einfo):
        """
            置任务失败
        :param id:
        :param einfo:
        :return:
        """
        retry = 0
        while retry < 3:
            try:
                task = self.get(id=id)
                task.error_msg = einfo
                task.status = self.model.ERROR
                task.updated_at = datetime.datetime.now()
                task.save(update_fields=["error_msg", "status", "updated_at"])
                break
            except ObjectDoesNotExistException:
                time.sleep(1)
                retry += 1

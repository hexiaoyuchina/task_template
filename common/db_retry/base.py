# -*- coding: utf-8 -*-

import logging
from django.db.backends.mysql.base import DatabaseWrapper as MysqlWrapper

logger = logging.getLogger(__name__)


class DatabaseWrapper(MysqlWrapper):
    def _cursor(self, *args, **kwargs):
        """
        检查连接看是否可用，不可用就关闭，后面django会重新建立连接
        基本Django的web项目长时间运行之后，其中的定时任务或者长时驻留的自定义线程在操作数据库的时候偶尔或者必然发生连接失效的错误

        """
        if self.connection and not self.is_usable():
            logger.info("django db conn is usable, close and reconnect!")
            self.connection.close()
            self.connection = None
        return super(DatabaseWrapper, self)._cursor(*args, **kwargs)

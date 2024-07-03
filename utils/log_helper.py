# -*- coding: utf-8 -*-

import datetime
import logging
import os
import re

try:
    import codecs
except ImportError:
    codecs = None


class MyLoggerHandler(logging.FileHandler):
    def __init__(self, filename, when='D', backup_count=0, encoding=None, delay=False):
        dir_name, base_name = os.path.split(filename)
        self.prefix = base_name
        self.when = when.upper()
        # S - Every second a new file
        # M - Every minute a new file
        # H - Every hour a new file
        # D - Every day a new file
        # month - Every month a new file
        if self.when == 'S':
            self.suffix = "%Y-%m-%d_%H-%M-%S"
            self.extMatch = r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}$"
        elif self.when == 'M':
            self.suffix = "%Y-%m-%d_%H-%M"
            self.extMatch = r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}$"
        elif self.when == 'H':
            self.suffix = "%Y-%m-%d_%H"
            self.extMatch = r"^\d{4}-\d{2}-\d{2}_\d{2}$"
        elif self.when == 'D':
            self.suffix = "%Y-%m-%d"
            self.extMatch = r"^\d{4}-\d{2}-\d{2}$"
        elif self.when == 'MONTH':
            self.suffix = "%Y-%m"
            self.extMatch = r"^\d{4}-\d{2}$"
        else:
            raise ValueError("Invalid rollover interval specified: %s" % self.when)
        self.filefmt = "%s.%s" % (filename, self.suffix)
        self.file_path = datetime.datetime.now().strftime(self.filefmt)
        _dir = os.path.dirname(self.file_path)
        try:
            if os.path.exists(_dir) is False:
                os.makedirs(_dir)
        except Exception:
            print("can not make dirs")
            print("filepath is " + self.file_path)

        self.backup_count = backup_count
        if codecs is None:
            encoding = None
        self.delay = delay
        logging.FileHandler.__init__(self, self.file_path, 'a', encoding, delay)

    def should_change_file_to_write(self):
        _file_path = datetime.datetime.now().strftime(self.filefmt)
        if _file_path != self.file_path:
            self.file_path = _file_path
            return 1
        return 0

    def do_change_file(self):
        self.base_filename = os.path.abspath(self.file_path)
        if self.stream is not None:
            self.stream.flush()
            self.stream.close()
        if not self.delay:
            self.stream = self._open()
        if self.backup_count > 0:
            for s in self.get_files_to_delete():
                os.remove(s)

    def get_files_to_delete(self):
        dir_name, base_name = os.path.split(self.base_filename)
        file_names = os.listdir(dir_name)
        result = []
        prefix = self.prefix + "."
        plen = len(prefix)
        for file_name in file_names:
            if file_name[:plen] == prefix:
                suffix = file_name[plen:]
                if re.compile(self.extMatch).match(suffix):
                    result.append(os.path.join(dir_name, file_name))
        result.sort()
        if len(result) < self.backup_count:
            result = []
        else:
            result = result[:len(result) - self.backup_count]
        return result

    def emit(self, record):
        """
        Emit a record.
        """
        try:
            if self.should_change_file_to_write():
                self.do_change_file()
            logging.FileHandler.emit(self, record)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

# -*- coding: utf-8 -*-

"""
作用：自动导入workflow任务
"""
import os
from .core.producer import *
import glob

cur_dir = os.path.dirname(os.path.realpath(__file__))

for name in glob.glob(f'{cur_dir}/*.py'):
    exec(f'from .{os.path.basename(name).split(".")[0]} import *')

for name in glob.glob(f'{cur_dir}/instance_task/*.py'):
    exec(f'from .instance_task.{os.path.basename(name).split(".")[0]} import *')

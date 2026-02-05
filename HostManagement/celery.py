# celery.py 初始化 Celery 实例、加载 Django 配置
import os
from celery import Celery

# 设置Django的环境变量，让Celery能找到Django的配置
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HostManagement.settings')

# 创建Celery实例，命名为你的项目名（比如HostManagement）
app = Celery('HostManagement')

# 从Django的settings.py中加载Celery配置（前缀为CELERY_）
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自动发现所有APP中的tasks.py文件（比如host/tasks.py）
app.autodiscover_tasks()


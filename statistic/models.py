# /statistic/models.py
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
class Statistic(models.Model):
    date = models.DateField(verbose_name='统计日期')
    # 使用ContentType关联不同模型,city/server_room,后续可扩展主机状态等
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    dimension = GenericForeignKey('content_type', 'object_id')
    host_count = models.IntegerField(default=0)

    class Meta:
        verbose_name = '统计数据'
        verbose_name_plural = verbose_name
        unique_together = ('content_type', 'object_id','date')
# city/models.py
from django.db import models
class City(models.Model):
    name = models.CharField(max_length=30)
    province = models.CharField(max_length=30)
    country = models.CharField(max_length=30)
    def __str__(self):
        return self.name
    @property
    def host_count(self):  # 间接外键关系
        from django.db.models import Count
        from server_room.models import ServerRoom
        '''
            filter(city=self): 过滤出「当前城市的所有机房」
            aggregate(): 全局聚合，所有联表后的 Host 数据做全局的 COUNT 统计
        '''
        return ServerRoom.objects.filter(city=self).aggregate(
            total=Count('host')
        )['total'] or 0

    class Meta:
        verbose_name = '城市管理'
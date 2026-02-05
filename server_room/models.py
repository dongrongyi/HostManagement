# server_room/models.py
from django.db import models
from city.models import City
class ServerRoom(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=100)
    address = models.TextField() # 无显式长度上限
    type = models.CharField(max_length=120)
    contact_person = models.CharField(max_length=30)
    contact_phone = models.CharField(max_length=30)
    def __str__(self):
        return self.name
    @property
    def host_count(self): # 动态属性
        return self.host_set.count() # host_set 反向关系查询器

    class Meta:
        verbose_name = '机房管理'
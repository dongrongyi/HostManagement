# /statistic/tasks.py
# 需求：每天 00:00 按城市和机房维度统计主机数量，并把统计数据写入数据库
'''
    step 1:先写tasks.py定义统计某个城市和机房主机数量的任务
    step 2:写批量统计城市和机房主机数量的任务
    step 3: 在settings.py中的CELERY_BEAT_SCHEDULE中配置定时任务
    step 4: 启动 Celery Beat（定时任务调度器）
'''
import logging
from celery import shared_task, group
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from city.models import City
from server_room.models import ServerRoom
from statistic.models import Statistic
logger = logging.getLogger(__name__)
@shared_task(bind=True)
def statistic_host_count(self,content_type_id,object_id):
    try:
        content_type = ContentType.objects.get(id=content_type_id)
        model_class = content_type.model_class()
        dimension_instance = model_class.objects.get(id=object_id)
        host_count = dimension_instance.host_count
        statistic = Statistic.objects.create(
            dimension=dimension_instance,  # 直接传City/ServerRoom实例，自动填充content_type/object_id
            host_count=host_count,
            date=timezone.localdate(),  # Django时区日期，替代原生datetime
            # 可补充其他字段：如statistic_type=dimension_name等
        )
        result = {
            "dimension_type": model_class.__name__,
            "dimension_instance": dimension_instance.name,
            "host_count": host_count,
            "statistic_date": str(statistic.date),
            "status": "success"
        }
        logger.info(f"主机数量统计成功：{result}")
        return result
    except Exception as e:
        error_msg = f"统计失败：临时异常 - {str(e)}，即将重试"
        logger.error(error_msg)
        self.retry(exc=e)
    '''
        使用方式
        # 1. 获取要统计的城市实例
        city = City.objects.get(name="北京")
        # 2. 获得City model对应的ContentType实例
        city_ct = ContentType.objects.get_for_model(City)
        # 3. 调用Celery任务（核心：传两个int，而非实例）
        statistic_host_count.delay(content_type_id=city_ct.id, object_id=city.id)
    '''
@shared_task()
def batch_statistic_host_count():
    # 1. 获取ContentTypeID
    city_ct_id = ContentType.objects.get_for_model(City).id
    sr_ct_id = ContentType.objects.get_for_model(ServerRoom).id
    # 2. 构造所有统计任务的参数（城市+机房）
    task_args = []
    # 加入所有城市的参数
    for city in City.objects.all():
        task_args.append((city_ct_id, city.pk))
    # 加入所有机房的参数
    for server_room in ServerRoom.objects.all():
        task_args.append((sr_ct_id, server_room.pk))
    task_group = group(statistic_host_count.s(content_type_id,object_id) for content_type_id,object_id in task_args)
    result = task_group.apply_async()
    print(f"批量统计任务已下发，共{len(task_args)}个维度，任务ID：{result.id}")
    # 调用方式：batch_statistic_host_count.delay()






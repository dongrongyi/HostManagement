# /HostManagement/middleware.py
import time
import logging
from django.db import connection
logger = logging.getLogger(__name__) # 默认日志器
class PerformanceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    def __call__(self, request):
        # 记录开始时间
        start_time = time.time()
        response = self.get_response(request)
        # 计算耗时
        duration = time.time() - start_time
        query_count = len(connection.queries)
        # 记录到日志或数据库
        logger.info(
            f"路径:{request.path} | "
            f"耗时:{duration:.3f}s | "
            f"ORM查询次数:{query_count} | "
            f"用户:{request.user.username if request.user.is_authenticated else '匿名'}"
        )
        # 添加响应头（便于前端监控）
        response['X-Request-Duration'] = f'{duration:.3f}s'
        response['X-Query-Count'] = str(query_count)
        return response
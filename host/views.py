# /host/views.py
import logging

from django.utils import timezone
from pythonping import ping
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from host.models import Host
from host.permissions import IsHostAdmin
from host.serializers import HostSerializer

class HostViewSet(viewsets.ModelViewSet):
    queryset = Host.objects.all()
    serializer_class = HostSerializer

    @action(detail=True, methods=['post'],url_path='ping') # 通过@action装饰器给视图集新增自定义方法，Router 会自动生成对应路由，支持GET/POST
    def ping(self, request, pk=None):
        host = self.get_object()
        result = ping(f"{host.ip}").success()
        host.is_reachable = result
        host.last_ping_time = timezone.now()
        host.save()
        return Response({'主机是否可达：': result})


# 审计日志器
audit_logger = logging.getLogger("host_pwd_audit")
# 主机密码查看接口
class HostPwdView(APIView):
    """
    单台主机密码查看接口（仅超管可访问）
    访问地址：/host/{pk}/pwd/
    请求方式：GET
    """
    permission_classes = [IsAuthenticated, IsHostAdmin]  # 权限控制

    def get(self, request, pk):
        try:
            host = Host.objects.get(pk=pk)
            # 校验加密密码是否存在
            if not host.encrypted_pwd:
                return Response(
                    {"code": 400, "msg": "该主机未设置密码", "data": None},
                    status=status.HTTP_400_BAD_REQUEST
                )
            # 自动解密获取明文
            plain_pwd = host.plain_pwd
            if plain_pwd == "密码解密失败！密文被篡改或密钥错误":
                audit_logger.error(
                    f"密码查看解密失败 | 用户{request.user.username} | 主机{host.ip}({host.hostname})",
                    extra={
                        "operate_user": request.user.username,
                        "host_ip": host.ip,
                        "host_hostname": host.hostname,
                        "operate_type": "密码查看解密失败"
                    }
                )
                return Response(
                    {"code": 500, "msg": plain_pwd, "data": None},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            # 记录审计日志（操作留痕）
            audit_logger.info(
                f"密码查看成功 | 用户{request.user.username} | 主机{host.ip}({host.hostname}) | 机房{host.server_room.name}",
                extra={
                    "operate_user": request.user.username,
                    "host_ip": host.ip,
                    "host_hostname": host.hostname,
                    "server_room": host.server_room.name,
                    "operate_type": "密码查看成功"
                }
            )
            # 返回数据（明文仅临时返回，前端需即时展示）
            return Response({
                "code": 200,
                "msg": "密码查看成功（仅临时有效，系统每8小时自动修改）",
                "data": {
                    "hostname": host.hostname,
                    "ip": host.ip,
                    "login_user": request.user.username,
                    "plain_pwd": plain_pwd,
                    "server_room": host.server_room.name
                }
            })
        except Host.DoesNotExist:
            return Response(
                {"code": 404, "msg": "主机不存在", "data": None},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            audit_logger.error(
                f"密码查看异常 | 用户{request.user.username} | 主机ID{pk} | 错误：{str(e)}",
                extra={
                    "operate_user": request.user.username,
                    "host_id": pk,
                    "operate_type": "密码查看异常"
                }
            )
            return Response(
                {"code": 500, "msg": f"密码查看失败：{str(e)}", "data": None},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

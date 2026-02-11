# host/tasks.py
import logging

from celery import shared_task
from celery.utils.log import get_task_logger
from django.utils import timezone

from .models import Host
from pythonping import ping

from .utils import update_host_pwd, generate_secure_pwd


@shared_task(bind=True, retry_backoff=3, retry_kwargs={'max_retries': 2})
def ping_host_task(self, host_id):
    """异步检测单台主机的ping可达性（带重试机制）"""
    try:
        host = Host.objects.get(id=host_id)
        # 执行ping检测（1包+1秒超时+关闭打印）
        response = ping(host.ip, count=1, timeout=1, verbose=False)
        # 解析结果
        is_reachable = response.packet_loss == 0.0
        ping_delay = round(response.rtt_avg_ms, 2) if is_reachable else 0.0
        # 更新主机状态
        host.is_reachable = is_reachable
        host.last_ping_time = timezone.now()
        host.save()
        return f"主机{host.ip}检测完成：{'可达' if is_reachable else '不可达'}，延迟{ping_delay}ms last_ping_time={host.last_ping_time}ms"
    except Host.DoesNotExist:
        return f"错误：主机ID{host_id}不存在"
    except Exception as e:
        # 任务失败时重试（最多2次，每次间隔3秒）
        self.retry(exc=e)


# 任务专用日志器（记录改密执行情况）
task_logger = get_task_logger("host_pwd_task")
# 审计日志器（记录改密操作，和查看密码共用）
audit_logger = logging.getLogger("host_pwd_audit")

@shared_task(bind=True, max_retries=3)
def update_single_host_pwd(self, host_id: int):
    """
    单台主机改密子任务（失败自动重试3次，每次间隔5秒）
    :param host_id: 主机ID
    """
    try:
        host = Host.objects.get(pk=host_id)
        # 1. 校验旧密码是否存在
        old_pwd = host.plain_pwd
        if not old_pwd or old_pwd == "密码解密失败！密文被篡改或密钥错误":
            msg = f"无有效旧密码，跳过改密"
            task_logger.warning(f"主机{host.ip}({host.hostname}) | {msg}")
            return f"主机{host.ip} | {msg}"

        # 2. 按系统类型生成新密码（Windows无特殊字符）
        use_special = False if host.os_type == "Windows" else True
        new_pwd = generate_secure_pwd(length=16, use_special=use_special)

        # 3. 远程修改主机实际密码
        success, remote_msg = update_host_pwd(
            host_ip=host.ip,
            os_type=host.os_type,
            username='root',
            old_pwd=old_pwd,
            new_pwd=new_pwd
        )
        if not success:
            raise Exception(f"远程改密失败：{remote_msg}")

        # 4. 加密存储新密码+更新改密时间
        host.plain_pwd = new_pwd
        host.save()

        # 5. 记录任务日志+审计日志（操作留痕）
        success_msg = f"改密成功，新密码已加密存储"
        task_logger.info(f"主机{host.ip}({host.hostname}) | {success_msg}")
        audit_logger.info(
            f"系统自动改密 | 主机{host.hostname}({host.ip}) | 机房{host.server_room.name} | 系统类型{host.os_type}",
            extra={
                "operate_user": "system",
                "host_ip": host.ip,
                "host_hostname": host.hostname,
                "server_room": host.server_room.name,
                "operate_type": "自动改密成功"
            }
        )
        return f"主机{host.ip} | {success_msg}"

    except Host.DoesNotExist:
        err_msg = f"主机ID{host_id}不存在"
        task_logger.error(err_msg)
        return err_msg
    except Exception as e:
        # 失败重试，每次间隔5秒
        task_logger.error(f"主机ID{host_id}改密失败，即将重试 | 错误：{str(e)}")
        self.retry(exc=e, countdown=5)


@shared_task
def batch_update_all_host_pwd():
    """
    批量改密主任务（Celery Beat每8小时调度）
    遍历所有主机，内部调用update_single_host_pwd任务
    """
    task_logger.info("========== 开始执行【每8小时批量改密任务】==========")
    # 获取所有主机（可按机房过滤，如：Host.objects.filter(server_room__name="北京机房")）
    hosts = Host.objects.all()
    if not hosts:
        task_logger.warning("无主机数据，批量改密任务结束")
        audit_logger.info("系统自动改密 | 无主机数据，任务结束",
                          extra={"operate_user": "system", "operate_type": "自动改密无数据"})
        return "无主机数据，批量改密任务结束"

    # 下发异步子任务，单台失败不影响其他主机
    for host in hosts:
        update_single_host_pwd.delay(host.id)

    task_logger.info(f"批量改密任务已下发 | 共{hosts.count()}台主机待处理")
    audit_logger.info(
        f"系统自动改密 | 任务下发成功 | 共{hosts.count()}台主机",
        extra={"operate_user": "system", "operate_type": "自动改密任务下发"}
    )
    return f"批量改密任务下发成功，共{hosts.count()}台主机待处理"
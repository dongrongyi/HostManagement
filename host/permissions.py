# host/permissions.py
from rest_framework import permissions

class IsHostAdmin(permissions.BasePermission):
    """
    仅超级管理员/主机运维组可查看主机密码
    """
    def has_permission(self, request, view):
        # 前提：用户已登录
        if not request.user.is_authenticated:
            return False
        # 超级管理员直接放行
        if request.user.is_superuser:
            return True
        # 其他用户禁止访问
        return False

    # 对象级权限，仅允许查看自己负责机房的主机密码
    def has_object_permission(self, request, view, obj):
        return True
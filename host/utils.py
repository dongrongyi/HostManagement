# host/utils.py
import secrets
import string
import paramiko # Python 的 SSH 协议客户端库, 用于Linux 主机的远程管理
import winrm # Python 的 WinRM 协议客户端库 —— 专用于Windows 主机的远程管理
from typing import Tuple
from cryptography.fernet import InvalidToken
from django.conf import settings

# Fernet 仅负责「明文密码↔密文密码」的对称加密 / 解密，不参与任何其他环节
# Fernet是「最适配 Django 生态」的「密码学安全级」对称加密算法，对比其他加密方案（Signer、MD5/SHA、自定义加密），优势是安全、简单、开箱即用
# Fernet 是 Django 官方文档中推荐的敏感信息加密方案，且依赖的cryptography库是 Django 的「官方关联依赖」，安装简单（pip install cryptography），无需自己写复杂的加解密逻辑，只需encrypt/decrypt两个方法，就能实现明文和密文的互转，适配 Django 的模型字段（数据库存字符串）
# Fernet 是经过密码学验证的安全算法: 防篡改、可选过期机制、无密钥不可解密



def generate_secure_pwd(length: int = 16, use_special: bool = True) -> str: # 生成安全的随机密码,基于 Python 的secrets模块实现
    """
    生成密码学安全的随机密码，适配Linux/Windows
    :param length: 密码长度，推荐12-20位
    :param use_special: 是否包含特殊字符（Windows设为False，避免兼容问题）
    :return: 明文随机密码
    """
    # 基础字符集：大小写字母+数字（必选，保证复杂度）
    char_pool = string.ascii_letters + string.digits
    # 兼容的特殊字符（过滤\ ' "等易冲突字符）
    special_chars = r"!@#$%^&*()_+-=[]{}|;:,.?~`"
    if use_special:
        char_pool += special_chars

    # 强制密码复杂度：至少包含大写、小写、数字，开启特殊字符则再加1位
    pwd_parts = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits)
    ]
    if use_special:
        pwd_parts.append(secrets.choice(special_chars))

    # 填充剩余长度并打乱顺序（避免固定前缀）
    remaining = length - len(pwd_parts)
    pwd_parts += [secrets.choice(char_pool) for _ in range(remaining)]
    secrets.SystemRandom().shuffle(pwd_parts)
    return ''.join(pwd_parts)

# 远程修改linux主机密码
def update_linux_pwd(host_ip: str, username: str, old_pwd: str, new_pwd: str) -> Tuple[bool, str]:
    """
    远程修改Linux主机密码（基于paramiko）
    :return: (是否成功, 提示信息)
    """
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        # 连接主机（超时10秒，避免阻塞）
        ssh.connect(host_ip, username=username, password=old_pwd, timeout=10,look_for_keys=False, allow_agent=False)
        # Linux通用改密命令（echo 用户名:新密码 | chpasswd）
        cmd = f"echo {username}:{new_pwd} | chpasswd"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        error = stderr.read().decode('utf-8', errors='ignore').strip()
        if error:
            return False, f"改密失败：{error}"
        return True, "改密成功"
    except Exception as e:
        return False, f"连接/改密失败：{str(e)}"
    finally:
        ssh.close()

# 远程修改Windows主机密码
def update_windows_pwd(host_ip: str, username: str, old_pwd: str, new_pwd: str) -> Tuple[bool, str]:
    """
    远程修改Windows主机密码（基于WinRM，需开启主机WinRM服务）
    :return: (是否成功, 提示信息)
    """
    try:
        # 初始化WinRM连接（默认端口5985，超时10秒）
        session = winrm.Session(
            f"http://{host_ip}:5985/wsman",
            auth=(username, old_pwd),
            timeout=10
        )
        # Windows改密命令（PowerShell）
        cmd = f'net user {username} "{new_pwd}"'
        result = session.run_ps(cmd)
        if result.status_code != 0:
            err = result.std_err.decode('utf-8', errors='ignore').strip()
            return False, f"改密失败：{err}"
        return True, "改密成功"
    except Exception as e:
        return False, f"连接/改密失败：{str(e)}"

def update_host_pwd(host_ip: str, os_type: str, username: str, old_pwd: str, new_pwd: str) -> Tuple[bool, str]:
    """
    统一远程改密入口（兼容Linux/Windows）
    """
    if os_type == "Linux":
        return update_linux_pwd(host_ip, username, old_pwd, new_pwd)
    elif os_type == "Windows":
        return update_windows_pwd(host_ip, username, old_pwd, new_pwd)
    else:
        return False, f"不支持的系统类型：{os_type}"

# 基于Fernet的明文-->密文
def encrypt_pwd(plain_pwd: str) -> str:
    """明文→Fernet密文（无明文拼接）"""
    if not plain_pwd or not isinstance(plain_pwd, str):
        return None
    plain_bytes = plain_pwd.encode('utf-8')
    cipher_bytes = settings.FERNET_PWD_CRYPT.encrypt(plain_bytes)
    return cipher_bytes.decode('utf-8')

# 基于Fernet的密文-->明文
def decrypt_pwd(cipher_pwd: str) -> str:
    """Fernet密文→明文"""
    if not cipher_pwd or not isinstance(cipher_pwd, str):
        return None
    try:
        cipher_bytes = cipher_pwd.encode('utf-8')
        plain_bytes = settings.FERNET_PWD_CRYPT.decrypt(cipher_bytes)
        return plain_bytes.decode('utf-8')
    except InvalidToken:
        raise ValueError("密码解密失败！密文被篡改、密钥错误或格式无效")
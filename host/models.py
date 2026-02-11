from server_room.models import ServerRoom
from django.db import models
from django.conf import settings
from cryptography.fernet import InvalidToken

class Host(models.Model):
    hostname = models.CharField(max_length=100,verbose_name='主机名')
    ip = models.GenericIPAddressField()
    os_type =  models.CharField(choices=(('Linux', 'Linux'), ('Windows', 'Windows')),max_length=10,default='Linux')
    server_room = models.ForeignKey(ServerRoom, on_delete=models.CASCADE)
    encrypted_pwd = models.CharField(verbose_name="加密主机密码", max_length=256, blank=True, null=True)
    is_reachable = models.BooleanField(default=True)
    last_ping_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')


    class Meta:
        verbose_name = '主机'

    def __str__(self):
        return self.hostname or self.ip

    # Fernet解密   读plain_pwd时获取到的是经过解密的明文密码
    @property
    def plain_pwd(self):
        if not self.encrypted_pwd: # 未设置密码
            return None
        try:
            cipher_bytes = self.encrypted_pwd.encode('utf-8')
            plain_bytes = settings.FERNET_PWD_CRYPT.decrypt(cipher_bytes)
            return plain_bytes.decode('utf-8')
        except InvalidToken:
            return "密码解密失败！密文被篡改或密钥错误"

    # Fernet加密  写plain_pwd是把加密后的密码赋值给encrypted_pwd
    @plain_pwd.setter
    def plain_pwd(self, value):
        if value and isinstance(value, str):
            plain_bytes = value.encode('utf-8')
            cipher_bytes = settings.FERNET_PWD_CRYPT.encrypt(plain_bytes)
            self.encrypted_pwd = cipher_bytes.decode('utf-8')
        else:
            self.encrypted_pwd = None
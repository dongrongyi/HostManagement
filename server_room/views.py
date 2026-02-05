
from rest_framework.viewsets import ModelViewSet

from server_room.models import ServerRoom
from server_room.serializers import ServerRoomSerializer


# Create your views here.
class ServerRoomViewSet(ModelViewSet):
    queryset = ServerRoom.objects.all() # 动态生成数据源
    serializer_class = ServerRoomSerializer
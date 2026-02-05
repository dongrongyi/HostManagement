from rest_framework import serializers

from server_room.models import ServerRoom


class ServerRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServerRoom
        fields = '__all__'
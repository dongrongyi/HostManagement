from rest_framework import serializers

from host.models import Host


class HostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Host
        fields = '__all__'
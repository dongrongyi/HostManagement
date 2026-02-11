from rest_framework import serializers

from host.models import Host
from statistic.models import Statistic


class StatisticSerializer(serializers.ModelSerializer):
    class Meta:
        model = Statistic
        fields = '__all__'
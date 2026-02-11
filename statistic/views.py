from rest_framework import viewsets
from statistic.models import Statistic
from statistic.serializers import StatisticSerializer


# Create your views here.
class statisticViewSet(viewsets.ModelViewSet):
    queryset = Statistic.objects.all()
    serializer_class = StatisticSerializer
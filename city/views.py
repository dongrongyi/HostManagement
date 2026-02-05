# /city/views/
from rest_framework import viewsets
from city.models import City
from city.serializers import CitySerializer
class CityViewSet(viewsets.ModelViewSet):
    queryset = City.objects.all()
    serializer_class = CitySerializer
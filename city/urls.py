# /city/urls.py
from rest_framework.routers import SimpleRouter
from city.views import CityViewSet
router = SimpleRouter()
router.register('', CityViewSet)
urlpatterns = router.urls
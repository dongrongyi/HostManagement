from rest_framework.routers import SimpleRouter

from statistic.views import statisticViewSet

router = SimpleRouter()
router.register('', statisticViewSet)
urlpatterns = router.urls
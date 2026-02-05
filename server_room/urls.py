from rest_framework.routers import SimpleRouter

from server_room.views import ServerRoomViewSet

router = SimpleRouter()
router.register('', ServerRoomViewSet)
urlpatterns = router.urls
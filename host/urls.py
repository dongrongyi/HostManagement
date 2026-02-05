from django.urls import path
from rest_framework.routers import SimpleRouter

from host import views
from host.views import HostViewSet

router = SimpleRouter()
router.register('', HostViewSet)
urlpatterns = router.urls

urlpatterns += [
    # 密码查看接口
    path("<int:pk>/pwd/", views.HostPwdView.as_view(), name="host-pwd"),
]


from rest_framework.routers import DefaultRouter

from .views import CreatorResponseViewSet

router = DefaultRouter()
router.register("", CreatorResponseViewSet, basename="creator-response")
urlpatterns = router.urls

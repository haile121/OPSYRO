from rest_framework.routers import DefaultRouter

from .views import ExperimentViewSet

router = DefaultRouter()
router.register("", ExperimentViewSet, basename="experiment")
urlpatterns = router.urls

from rest_framework.routers import DefaultRouter

from .views import CreatorSessionViewSet

router = DefaultRouter()
router.register("", CreatorSessionViewSet, basename="creator-session")
urlpatterns = router.urls

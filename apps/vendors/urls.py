from rest_framework.routers import DefaultRouter

from .views import VendorProfileViewSet

router = DefaultRouter()
router.register("", VendorProfileViewSet, basename="vendor")

urlpatterns = router.urls

"""
`categories` URL configuration — mounted under `/api/v1/` by the project
root URLconf (same pattern as `universities`/`vendors`/`stores`).
"""

from rest_framework.routers import DefaultRouter

from .views import CategoryViewSet

router = DefaultRouter()
router.register("", CategoryViewSet, basename="category")

urlpatterns = router.urls

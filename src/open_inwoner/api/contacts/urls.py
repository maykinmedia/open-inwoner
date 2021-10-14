from rest_framework import routers

from .views import ContactViewSet

router = routers.SimpleRouter()
router.register(r"", ContactViewSet, basename="contacts")
urlpatterns = router.urls

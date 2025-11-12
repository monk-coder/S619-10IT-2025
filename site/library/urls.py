from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CurrentUserView,
    LoginView,
    LogoutView,
    ReadingEntryViewSet,
    ReadingNoteViewSet,
    ReadingStatusViewSet,
    RegisterView,
    TagViewSet,
)


router = DefaultRouter()

router.register("statuses", ReadingStatusViewSet, basename="reading-statuses")
router.register("tags", TagViewSet, basename="tags")
router.register("entries", ReadingEntryViewSet, basename="reading-entries")
router.register("notes", ReadingNoteViewSet, basename="reading-notes")


urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/me/", CurrentUserView.as_view(), name="current-user"),
    path("", include(router.urls)),
]

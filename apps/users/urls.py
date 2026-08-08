from django.urls import path

from .views import MeView, SetActiveUniversityView

app_name = "users"

urlpatterns = [
    path("me/", MeView.as_view(), name="me"),
    path(
        "me/active-university/",
        SetActiveUniversityView.as_view(),
        name="set-active-university",
    ),
]

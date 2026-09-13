# ------------------------------------------------------------------
# urls.py
# ------------------------------------------------------------------
from django.urls import path
from .views import StudentOnboardingCreateView

urlpatterns = [
    path(
        "onboarding/",
        StudentOnboardingCreateView.as_view(),
        name="student-onboarding-create",
    ),
]

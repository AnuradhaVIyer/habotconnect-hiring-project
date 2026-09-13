# ------------------------------------------------------------------
# views.py
# ------------------------------------------------------------------
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import StudentOnboarding
from .serializers import StudentOnboardingSerializer


class StudentOnboardingCreateView(APIView):
    def post(self, request):
        serializer = StudentOnboardingSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"status": "REJECTED", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        validated = serializer.validated_data

        instance = StudentOnboarding.objects.create(
            student_id=validated["student_id"],
            lsa_id=validated.get("lsa_id", ""),
            guardian_email=validated["guardian_email"],
            onboarding_status=validated["onboarding_status"],
            region=validated["region"],
        )

        return Response(
            {"status": "ACCEPTED", "id": instance.id},
            status=status.HTTP_201_CREATED,
        )

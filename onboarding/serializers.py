import re
from rest_framework import serializers


def dcyn_is_valid_email(value: str) -> bool:
    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    return bool(re.match(pattern, value))


def dcyn_is_known_status(value: str) -> bool:
    allowed = {"PENDING", "APPROVED", "REJECTED"}
    return value in allowed


def dcyn_is_valid_region_code(value: str) -> bool:
    return bool(re.match(r"^[A-Z]{2}$", value))


def dcyn_is_nonempty_id(value: str) -> bool:
    return isinstance(value, str) and 1 <= len(value) <= 64


class StudentOnboardingSerializer(serializers.Serializer):
    student_id = serializers.CharField(max_length=64)
    lsa_id = serializers.CharField(max_length=64, allow_blank=True, required=False)
    guardian_email = serializers.EmailField(max_length=254)
    onboarding_status = serializers.CharField(max_length=20)
    region = serializers.CharField(max_length=2)

    def validate_student_id(self, value):
        if not dcyn_is_nonempty_id(value):
            raise serializers.ValidationError(
                "student_id must be a non-empty string of 1-64 characters."
            )
        return value

    def validate_lsa_id(self, value):
        if value and not dcyn_is_nonempty_id(value):
            raise serializers.ValidationError(
                "lsa_id must be 1-64 characters when provided."
            )
        return value

    def validate_guardian_email(self, value):
        if not dcyn_is_valid_email(value):
            raise serializers.ValidationError(
                "guardian_email failed strict DCYN email format check."
            )
        return value

    def validate_onboarding_status(self, value):
        if not dcyn_is_known_status(value):
            raise serializers.ValidationError(
                "onboarding_status must be exactly one of: PENDING, APPROVED, REJECTED."
            )
        return value

    def validate_region(self, value):
        if not dcyn_is_valid_region_code(value):
            raise serializers.ValidationError(
                "region must be a 2-letter uppercase code (e.g. 'AE', 'IN')."
            )
        return value

    def validate(self, attrs):
        if attrs.get("onboarding_status") == "APPROVED" and not attrs.get("lsa_id"):
            raise serializers.ValidationError(
                "Cannot APPROVE onboarding without an assigned lsa_id."
            )
        return attrs

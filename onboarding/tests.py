"""
Unit tests for the DCYN validation library and StudentOnboardingSerializer.
These cover both the "Yes" (accept) and "No" (reject) path for each rule,
since a Poka-Yoke system needs proof it actually blocks bad input, not
just that it accepts good input.
"""

from django.test import TestCase
from onboarding.serializers import (
    StudentOnboardingSerializer,
    dcyn_is_valid_email,
    dcyn_is_known_status,
    dcyn_is_valid_region_code,
    dcyn_is_nonempty_id,
)


class DCYNFunctionTests(TestCase):
    def test_valid_email_accepted(self):
        self.assertTrue(dcyn_is_valid_email("guardian@example.com"))

    def test_invalid_email_rejected(self):
        self.assertFalse(dcyn_is_valid_email("not-an-email"))

    def test_known_status_accepted(self):
        self.assertTrue(dcyn_is_known_status("APPROVED"))

    def test_unknown_status_rejected(self):
        self.assertFalse(dcyn_is_known_status("MAYBE"))

    def test_valid_region_code_accepted(self):
        self.assertTrue(dcyn_is_valid_region_code("AE"))

    def test_lowercase_region_code_rejected(self):
        self.assertFalse(dcyn_is_valid_region_code("ae"))

    def test_nonempty_id_accepted(self):
        self.assertTrue(dcyn_is_nonempty_id("STU-001"))

    def test_empty_id_rejected(self):
        self.assertFalse(dcyn_is_nonempty_id(""))

    def test_oversized_id_rejected(self):
        self.assertFalse(dcyn_is_nonempty_id("x" * 65))


class StudentOnboardingSerializerTests(TestCase):
    def valid_payload(self, **overrides):
        payload = {
            "student_id": "STU-001",
            "lsa_id": "LSA-100",
            "guardian_email": "guardian@example.com",
            "onboarding_status": "PENDING",
            "region": "AE",
        }
        payload.update(overrides)
        return payload

    def test_valid_payload_is_accepted(self):
        serializer = StudentOnboardingSerializer(data=self.valid_payload())
        self.assertTrue(serializer.is_valid())

    def test_invalid_email_is_rejected(self):
        payload = self.valid_payload(guardian_email="not-an-email")
        serializer = StudentOnboardingSerializer(data=payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("guardian_email", serializer.errors)

    def test_unknown_status_is_rejected(self):
        payload = self.valid_payload(onboarding_status="MAYBE")
        serializer = StudentOnboardingSerializer(data=payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("onboarding_status", serializer.errors)

    def test_lowercase_region_is_rejected(self):
        payload = self.valid_payload(region="ae")
        serializer = StudentOnboardingSerializer(data=payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("region", serializer.errors)

    def test_approved_without_lsa_is_rejected(self):
        """
        Object-level DCYN rule: directly guards against the schema-mismatch
        incident described in the brief (approving a record with missing
        downstream-critical data).
        """
        payload = self.valid_payload(onboarding_status="APPROVED", lsa_id="")
        serializer = StudentOnboardingSerializer(data=payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)

    def test_approved_with_lsa_is_accepted(self):
        payload = self.valid_payload(onboarding_status="APPROVED", lsa_id="LSA-100")
        serializer = StudentOnboardingSerializer(data=payload)
        self.assertTrue(serializer.is_valid())

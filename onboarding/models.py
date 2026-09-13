# ------------------------------------------------------------------
# models.py
# ------------------------------------------------------------------
from django.db import models


class StudentOnboarding(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    student_id = models.CharField(max_length=64, unique=True)
    lsa_id = models.CharField(max_length=64, blank=True)
    guardian_email = models.EmailField(max_length=254)
    onboarding_status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    region = models.CharField(max_length=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["region"]),
            models.Index(fields=["onboarding_status"]),
        ]

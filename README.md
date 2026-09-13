# HabotConnect FZCO — Hiring Project Submission

**Candidate:** Anuradha Iyer

**Contact:** anuradha.v.iyer@gmail.com | +91 9892405079

**Position:** Junior Cloud & DevOps Engineer (GCP / Django / React)

**Submission Date:** 13th September 2026

---

## Overview

This project addresses the staging incident described in the Hiring Project Form: unencrypted API credentials pushed to the codebase, and a database schema mismatch that broke downstream analytics. The submission is organized into three parts corresponding to the three required tasks, plus a presentation covering the architecture and demonstrated fail-closed behavior.

## Architecture Summary

**Flow 1 — Provisioned infrastructure (Task 1), independent of Flow 2:**
```
terraform apply (run manually, not part of CI/CD)
        |
        +--> GCS Bucket (D0 Raw Landing) --> [batch load job, not built] --+
        |                                                                  |
        +--> Pub/Sub Topic (App event stream) --> [streaming sub, not built] --> BigQuery Dataset (D1 Staged/Enforced)
```
The GCS bucket, the Pub/Sub topic, and the BigQuery dataset/table are real resources created by Terraform. The batch load job and streaming subscription are conceptual only — no code in this submission builds them. Flow 1 and Flow 2 do not trigger each other; the Django app does not publish to the Pub/Sub topic. See the presentation deck for the annotated two-flow diagrams distinguishing solid (provisioned) from dashed/faded (conceptual) components.

**Flow 2 — Implemented and tested (Tasks 2 and 3):**
```
Developer commits code --> pushes to GitHub (trigger)
        |
        +--> Lint Gate (flake8, black) --+
        +--> Secret Scan Gate (gitleaks) -+--> both must pass
                                                        |
                                              Deployed to GCP App Engine
                                                        |
Client --> Django REST Framework API --> DCYN Validation --> SQLite (local database)
                                              |
                                    (rejects invalid payloads)
```

## Folder Structure

```
habotconnect-hiring-project/
├── README.md
├── .gitignore
├── requirements.txt
├── manage.py
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── terraform.tfvars.example
├── .github/
│   └── workflows/
│       └── poka-yoke-build-gate.yml
├── onboarding/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   ├── tests.py
│   └── migrations/
│       ├── __init__.py
│       └── 0001_initial.py
└── presentation/
    └── HabotConnect_Hiring_Project_AnuradhaIyer.pptx
```

## Project Setup

### Environment Setup

```bash
# From the project root
python3 -m venv venv
source venv/bin/activate      # Windows PowerShell: venv\Scripts\Activate.ps1

pip install django djangorestframework
pip freeze > requirements.txt
```

### Django Scaffolding

```bash
django-admin startproject config .
python manage.py startapp onboarding
```

`config/settings.py` must include:

```python
INSTALLED_APPS = [
    ...
    "rest_framework",
    "onboarding",
]
```

`config/urls.py` (root) must include:

```python
from django.urls import path, include

urlpatterns = [
    path("api/", include("onboarding.urls")),
]
```

### .gitignore

The `venv/` directory should never be committed — only `requirements.txt` is included, so the environment can be recreated with:

```bash
pip install -r requirements.txt
```

Minimum `.gitignore` contents:

```
venv/
__pycache__/
*.pyc
.env
db.sqlite3
```

## Task 1 — Terraform Secure Staging Provisioning

Location: `terraform/`

Provisions three resources as specified in the brief:

- **D0 Raw Landing** — a Google Cloud Storage bucket with uniform bucket-level access, versioning enabled, and an IAM condition restricting the ingestion service account to writes under the `incoming/` object prefix.
- **D1 Staged/Enforced** — a BigQuery dataset containing the `student_onboarding` table, with an IAM condition restricting the analytics reader group to business-hours access, and a Row-Level Security policy scoping visible rows by region.
- A Pub/Sub topic representing the intended streaming-sink entry point.

**Scope note:** Terraform provisions the storage layer only. The transformation step that would move and cleanse data from D0 into D1 (e.g. a Cloud Function or Dataflow job), and the streaming subscription that would connect the Pub/Sub topic to D1, are not implemented — they were not part of Task 1's stated deliverable. This is called out explicitly in the presentation's trade-offs slide.

To apply:

```bash
cd terraform
terraform init
terraform plan -var-file="terraform.tfvars"
terraform apply -var-file="terraform.tfvars"
```

## Task 2 — Poka-Yoke Automated CI/CD Build Gate

Location: `.github/workflows/poka-yoke-build-gate.yml`

A fail-closed GitHub Actions pipeline with two independent gates:

- **Lint gate** — runs `flake8` and `black --check` on Python code.
- **Secret scan gate** — runs `gitleaks` across the full commit history to detect hardcoded credentials.

The deploy job is only reachable if both gates pass (`needs: [lint, secret-scan]` combined with `if: success()`), so there is no path from a failing commit to a live deployment.

## Task 3 — Schema Mapping and DCYN Validation

Location: `onboarding/`

Implements a Django REST Framework serializer for the student onboarding payload, backed by a DCYN (binary Yes/No) validation library:

- `dcyn_is_valid_email`
- `dcyn_is_known_status`
- `dcyn_is_valid_region_code`
- `dcyn_is_nonempty_id`

Each validator returns a strict pass/fail against an explicit rule, with no fuzzy or implicit acceptance. An object-level rule additionally prevents a record from being marked `APPROVED` without an assigned `lsa_id`, directly addressing the schema-mismatch scenario described in the brief.

**Scope note:** Validated records are written to the local SQLite database (`db.sqlite3`) via the Django ORM — this is separate from the BigQuery dataset provisioned in Task 1. The two are not connected in this submission; see the Architecture Summary above.

Unit tests covering the DCYN validators and the object-level APPROVED/lsa_id rule live in `onboarding/tests.py` — both the accept and reject path are tested for each rule.

To run migrations after setup:

```bash
python manage.py makemigrations onboarding
python manage.py migrate
```

To run tests:

```bash
python manage.py test onboarding
```

### Testing the Endpoint Locally

Start the dev server:

```bash
python manage.py runserver
```

Then open the endpoint in a browser to use DRF's browsable API for testing payloads directly:

```
http://127.0.0.1:8000/api/onboarding/
```


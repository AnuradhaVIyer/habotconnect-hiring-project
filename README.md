# HabotConnect FZCO — Hiring Project Submission

**Candidate:** Anuradha Iyer

**Contact:** anuradha.v.iyer@gmail.com | +91 9892405079

**Position:** Junior Cloud & DevOps Engineer (GCP / Django / React)

**Submission Date:** 11 September 2026

---

## Overview

This project addresses the staging incident described in the Hiring Project Form: unencrypted API credentials pushed to the codebase, and a database schema mismatch that broke downstream analytics. The submission is organized into three parts corresponding to the three required tasks, plus a presentation covering the architecture and demonstrated fail-closed behavior.

## Architecture Summary

**Flow 1 — Implemented and tested (Tasks 2 and 3):**
```
Developer commits code --> pushes to GitHub (trigger)
        |
        +--> Lint Gate (flake8, black, eslint) --+
        +--> Secret Scan Gate (gitleaks) --------+--> both must pass
                                                        |
                                              Deployed to GCP App Engine
                                                        |
Client --> Django REST Framework API --> DCYN Validation --> SQLite (local database)
                                              |
                                    (rejects invalid payloads)
```

**Flow 2 — Provisioned infrastructure (Task 1), independent of Flow 1:**
```
terraform apply (run manually, not part of CI/CD)
        |
        +--> GCS Bucket (D0 Raw Landing) --> [batch load job, not built] --+
        |                                                                  |
        +--> Pub/Sub Topic (App event stream) --> [streaming sub, not built] --> BigQuery Dataset (D1 Staged/Enforced)
```
The GCS bucket, the Pub/Sub topic, and the BigQuery dataset/table are real resources created by Terraform. The batch load job and streaming subscription are conceptual only — no code in this submission builds them. Flow 1 and Flow 2 do not trigger each other; the Django app does not publish to the Pub/Sub topic. See the presentation deck for the annotated two-flow diagram distinguishing solid (provisioned) from dashed/faded (conceptual) components.

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

- **Lint gate** — runs `flake8` and `black --check` on Python code, and `eslint` on JavaScript/React code.
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

## Presentation

Location: `presentation/`

A 15-slide deck covering the architecture, the design rationale for each task, and a demonstration of the CI/CD pipeline succeeding on a compliant commit and failing closed on a non-compliant one.

**Slide 3 (Architecture Overview)** uses the annotated diagram, structured as two fully separate flows:
- **Flow 1 — Application CI/CD (Tasks 2 and 3):** Developer commits code → pushes to GitHub (the actual trigger) → fans out to the Lint Gate (flake8/black/eslint) and Secret Scan Gate (gitleaks) → both must pass → Deployed to GCP App Engine → Client sends requests to the running Django API → writes to SQLite
- A plain text note under Flow 1 states that Django does not publish to Flow 2's Pub/Sub topic — no line is drawn for this, since a line would wrongly imply a connection exists
- **Flow 2 — Infrastructure Provisioning (Task 1), independent of Flow 1:** triggered separately and manually by running `terraform apply`, which creates all three storage resources — the GCS bucket, the Pub/Sub topic, and the BigQuery dataset (all solid teal, actually provisioned)
- Faded, dashed teal boxes and arrows — conceptual, unbuilt steps within Flow 2 only (batch load job, streaming subscription) converging into the BigQuery dataset
- All purple boxes are implemented and tested; the horizontal divider and separate section labels make clear the two flows do not trigger each other

**Slide 13 — End-to-End Flow**
- Screenshot: `curl` / browsable API request with a valid payload → `201 ACCEPTED`
- Screenshot: request with an invalid payload → `400 REJECTED` with structured field errors
- Screenshot: `python manage.py test onboarding` — all tests passing
- Caption note: these writes go to the local SQLite database (Task 3), not to the BigQuery dataset provisioned in Task 1

**Slide 14 — Trade-offs & Design Boundaries**
- Terraform provisions all three storage resources (GCS bucket, Pub/Sub topic, BigQuery dataset) — but no code moves data between them. A batch load job (D0 → D1) and a streaming subscription (Pub/Sub → D1) would be needed in production; neither is built here, since Task 1's scope was storage provisioning only
- The Django app does not publish to the Pub/Sub topic — Task 1 and Task 3 are provisioned and demonstrated independently, per the brief's task scoping
- SQLite (Task 3's actual write target) and BigQuery (Task 1's provisioned dataset) are two separate databases with no code path connecting them
- The Row-Level Security filter and IAM conditions in Task 1 are illustrative; production would use a proper identity-to-region mapping and a security-pattern review for condition scope
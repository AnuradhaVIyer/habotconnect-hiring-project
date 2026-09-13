provider "google" {
  project = var.project_id
  region  = var.region
}

##############################################################
# D0: Raw Landing (GCS)
##############################################################

resource "google_storage_bucket" "d0_raw_landing" {
  name                        = "${var.project_id}-d0-raw-landing"
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = false

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }
}

resource "google_storage_bucket_iam_member" "d0_ingest_writer" {
  bucket = google_storage_bucket.d0_raw_landing.name
  role   = "roles/storage.objectCreator"
  member = "serviceAccount:${var.ingestion_service_account}"

  condition {
    title       = "restrict-to-incoming-prefix"
    description = "Ingestion SA may only write objects under the incoming/ prefix"
    expression  = "resource.name.startsWith(\"projects/_/buckets/${google_storage_bucket.d0_raw_landing.name}/objects/incoming/\")"
  }
}

##############################################################
# D1: Staged / Enforced (BigQuery)
##############################################################

resource "google_bigquery_dataset" "d1_staged_enforced" {
  dataset_id                  = "d1_staged_enforced"
  location                    = "US"
  default_table_expiration_ms = null

  labels = {
    layer = "staged-enforced"
    env   = "dev"
  }
}

resource "google_bigquery_table" "student_onboarding" {
  dataset_id = google_bigquery_dataset.d1_staged_enforced.dataset_id
  table_id   = "student_onboarding"

  schema = jsonencode([
    { name = "student_id", type = "STRING", mode = "REQUIRED" },
    { name = "lsa_id", type = "STRING", mode = "REQUIRED" },
    { name = "guardian_email", type = "STRING", mode = "REQUIRED" },
    { name = "onboarding_status", type = "STRING", mode = "REQUIRED" },
    { name = "region", type = "STRING", mode = "REQUIRED" }
  ])

  deletion_protection = true
}

resource "google_bigquery_dataset_iam_member" "d1_reader" {
  dataset_id = google_bigquery_dataset.d1_staged_enforced.dataset_id
  role       = "roles/bigquery.dataViewer"
  member     = "group:${var.analytics_reader_group}"

  condition {
    title       = "business-hours-only"
    description = "Analytics group may only read staged data during business hours (UTC)"
    expression  = "request.time.getHours(\"UTC\") >= 6 && request.time.getHours(\"UTC\") <= 18"
  }
}

resource "google_bigquery_row_access_policy" "region_scoped_access" {
  dataset_id        = google_bigquery_dataset.d1_staged_enforced.dataset_id
  table_id          = google_bigquery_table.student_onboarding.table_id
  policy_id         = "region_scoped_access"
  filter_predicate  = "region = SESSION_USER()"

  grantees = [
    "group:${var.analytics_reader_group}"
  ]
}

resource "google_pubsub_topic" "d1_streaming_sink" {
  name = "d1-staged-enforced-streaming-sink"

  labels = {
    feeds = "d1-staged-enforced"
  }
}
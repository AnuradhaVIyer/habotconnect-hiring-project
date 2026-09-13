output "d0_raw_landing_bucket_name" {
  description = "Name of the GCS raw landing bucket"
  value       = google_storage_bucket.d0_raw_landing.name
}

output "d0_raw_landing_bucket_url" {
  description = "gs:// URL of the raw landing bucket"
  value       = google_storage_bucket.d0_raw_landing.url
}

output "d1_staged_enforced_dataset_id" {
  description = "BigQuery dataset ID for staged/enforced data"
  value       = google_bigquery_dataset.d1_staged_enforced.dataset_id
}

output "student_onboarding_table_id" {
  description = "Fully qualified BigQuery table ID for student onboarding records"
  value       = "${google_bigquery_dataset.d1_staged_enforced.dataset_id}.${google_bigquery_table.student_onboarding.table_id}"
}

output "d1_streaming_sink_topic_name" {
  description = "Pub/Sub topic name feeding the D1 staged/enforced dataset"
  value       = google_pubsub_topic.d1_streaming_sink.name
}
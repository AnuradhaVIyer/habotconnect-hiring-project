variable "project_id" {
  description = "GCP project ID resources are provisioned into"
  type        = string
}

variable "region" {
  description = "Primary region for regional resources"
  type        = string
  default     = "us-central1"
}

variable "ingestion_service_account" {
  description = "Service account allowed to write into the raw landing bucket"
  type        = string
}

variable "analytics_reader_group" {
  description = "Group allowed to read staged/enforced data, scoped by row-level filter"
  type        = string
}
locals {
  cloud_function_url = "https://${var.region}-${var.project}.cloudfunctions.net/${var.function_name}"
}

resource "google_cloudfunctions2_function" "this" {
  name     = var.function_name
  project  = var.project
  location = var.region

  service_config {
    service_account_email = data.google_service_account.this.email
    environment_variables = {
      LOG_EXECUTION_ID         = "false" // recommended is true, however this breaks structured logging(no logs at all)
      TEAMS_WEBHOOK_URL        = var.teams_webhook_url
      PROJECT_ID               = var.project
      REGION                   = var.region
      REQUEST_PERIOD           = var.error_report_request_period
      RESPONSE_CODES_TO_FILTER = join(",", var.response_codes_to_filter)
      AI_MODEL_ID              = var.ai_model_id
    }
    available_memory   = var.recource_limits.memory
    available_cpu      = var.recource_limits.cpu
    min_instance_count = 1
    max_instance_count = 1
    timeout_seconds    = 600
  }

  build_config {
    runtime     = var.python_runtime
    entry_point = "main"
    source {
      storage_source {
        bucket = var.bucket_name
        object = google_storage_bucket_object.archive.name
      }
    }
  }
}

resource "google_cloud_scheduler_job" "this" {
  name      = "${var.function_name}-scheduler"
  project   = var.project
  region    = var.region
  schedule  = var.schedule
  time_zone = "Europe/Berlin"

  http_target {
    http_method = "GET"
    uri         = local.cloud_function_url
    oidc_token {
      service_account_email = data.google_service_account.this.email
      audience              = local.cloud_function_url
    }
  }
}

data "google_service_account" "this" {
  project    = var.project
  account_id = var.service_account
}

resource "google_cloud_run_service_iam_member" "run_invoker" {
  project  = var.project
  location = var.region
  role     = "roles/run.invoker"
  member   = "serviceAccount:${data.google_service_account.this.email}"
  service  = google_cloudfunctions2_function.this.name
}

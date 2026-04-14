variable "bucket_name" {
  type        = string
  description = "Bucket name where the app source will be uploaded for the Cloud Function to use it"
}

variable "service_account" {
  type        = string
  description = "Service account identifier"
}

variable "project" {
  type = string
}

variable "region" {
  type = string
}

variable "teams_webhook_url" {
  type = string
}

variable "function_name" {
  type    = string
  default = "error-report-teams-alert"
}

variable "python_runtime" {
  type    = string
  default = "python312"
}

variable "schedule" {
  type        = string
  description = "As a cron expression, see: https://crontab.guru/"
  default     = "0 3 * * *"
}

variable "recource_limits" {
  type = object({
    memory = string
    cpu    = string
  })
  default = {
    memory = "2G"
    cpu    = "1"
  }
}

variable "error_report_request_period" {
  type        = number
  description = "Google takes a period input based on an int: PERIOD_1_HOUR = 1, PERIOD_6_HOURS = 2, PERIOD_1_DAY = 3, PERIOD_1_WEEK = 4, PERIOD_30_DAYS = 5"
  validation {
    condition     = contains([1, 2, 3, 4, 5], var.error_report_request_period)
    error_message = "Allowed values: 1, 2, 3, 4, 5."
  }
}

variable "response_codes_to_filter" {
  type        = list(number)
  description = "A list of HTTP response codes to not include in the AI request. To filter error groups that do not contain a response code in the GCP Error Reporting page add '0' to the list"
  default     = []
}

variable "ai_model_id" {
  type        = string
  description = "Which Vertex AI model to use. See: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models"
  default     = "gemini-2.5-flash"
}

variable "bucket_name" {
  type        = string
  description = "Bucket name where the app source will be uploaded and the cache will be stored"
}

variable "service_account" {
  type        = string
  description = "Service account name (not email!)"
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

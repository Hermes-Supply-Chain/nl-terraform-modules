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

variable "evaluation_by_ai" {
  type        = bool
  description = <<-EOT
Select one of two possible ways to interpret the error report. 
If set to true, send the error report to an AI, which is prompted to decide whether a critical error worth of sending a notification is found or not. 
If set to false, new errors and errors exceeding the error_increase_threshold will be sent."
EOT
}

variable "error_increase_threshold" {
  type        = number
  description = "The factor of error increase, that will be seen as a spike, and be reported. Ex: 0.5 = 50% (and above) more errors than the day before will be reported"
  default     = 0.5
}

variable "error_report_request_period" {
  type        = number
  description = "Google takes a period input based on an int: PERIOD_1_HOUR = 1, PERIOD_6_HOURS = 2, PERIOD_1_DAY = 3, PERIOD_1_WEEK = 4, PERIOD_30_DAYS = 5"
  validation {
    condition     = contains([1, 2, 3, 4, 5], var.error_report_request_period)
    error_message = "Allowed values: 1, 2, 3, 4, 5."
  }
}

# Module: Source Zip
# This module creates a zip file from a source directory. The zip file is named with a UUID that is fixed to the file hashes.
# The resulting zip file can be used as a source for gcp cloud functions(must be dependent on the generated filename!), ensuring it is redeployed only on changes.
# This is a workaround for a major limitation of archive_file, which otherwise generates the zip file during the terraform plan phase only.

locals {
  filename  = "source-${random_uuid.this.result}.zip"
  all_files = fileset(var.source_dir, "**/*")
  filtered_files = toset([
    for file in local.all_files :
    file if alltrue([
      for substr in var.ignored_file_substr :
      !strcontains(file, substr)
    ])
  ])
}

resource "random_uuid" "this" {
  keepers = {
    for file in local.filtered_files :
    file => filemd5("${var.source_dir}/${file}")
  }
}

data "archive_file" "source" {
  type        = "zip"
  output_path = "${var.output_folder}/${local.filename}"
  source_dir  = var.source_dir
}

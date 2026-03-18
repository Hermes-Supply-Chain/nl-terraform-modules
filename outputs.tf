output "output_full_path" {
  description = "The full output path of the zipped file."
  value       = data.archive_file.source.output_path
}

output "output_file_name" {
  description = "The name of the zipped file, without folder path."
  value       = local.filename
}

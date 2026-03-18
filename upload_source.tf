module "source_zip" {
  source        = "github.com/Hermes-Supply-Chain/nl-terraform-modules?ref=source_zip/v1.0.0"
  output_folder = "${path.module}/tmp/source"
  source_dir    = "${path.module}/src"
}

resource "google_storage_bucket_object" "archive" {
  name   = "source/${module.source_zip.output_file_name}"
  bucket = var.bucket_name
  source = module.source_zip.output_full_path
}

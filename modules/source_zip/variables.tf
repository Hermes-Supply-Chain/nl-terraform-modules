variable "source_dir" {
  type        = string
  description = "The source directory of the code to be zipped"
}

variable "output_folder" {
  type        = string
  description = "The output folder of the zipped file. (random filename will be generated)"
}
variable "ignored_file_substr" {
  type        = set(string)
  description = "Substrings to ignore when checking whether to create a new zip"
  default = [
    "__pycache__",
    ".mypy_cache",
  ]
}

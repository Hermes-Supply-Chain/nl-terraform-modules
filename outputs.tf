output "instance_id" {
  value = google_compute_instance.nat_instance.id
}

output "nat_instance" {
  value = google_compute_instance.nat_instance
}

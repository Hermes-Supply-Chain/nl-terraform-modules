locals {
  name_addition   = var.name_addition != null ? "-${var.name_addition}" : ""
  nat_router_name = "${var.nat_router_source.subnet_name}-to-${var.nat_router_destination.subnet_name}-nat-router${local.name_addition}"
}

# Create a Compute Engine instance with two network interfaces and specific IP addresses
resource "google_compute_instance" "nat_instance" {
  name                    = local.nat_router_name
  project                 = var.project
  zone                    = var.zone
  machine_type            = var.machine_type
  can_ip_forward          = true
  metadata_startup_script = local.metadata_startup_script

  boot_disk {
    initialize_params {
      image = var.image
    }
  }

  # First network interface in the first VPC with a specific IP
  network_interface {
    network    = var.nat_router_source.network_name
    subnetwork = var.nat_router_source.subnet_name
    network_ip = var.nat_router_source.interface_ip
  }

  # Second network interface in the second VPC with a specific IP
  network_interface {
    network    = var.nat_router_destination.network_name
    subnetwork = var.nat_router_destination.subnet_name
    network_ip = var.nat_router_destination.interface_ip
  }

  instance_encryption_key {
    kms_key_self_link = var.cmek
  }

  # required to enable Ops Agent
  metadata = {
    enable-osconfig = "TRUE"
  }

  # required to enable Ops Agent
  service_account {
    scopes = [
      "https://www.googleapis.com/auth/cloud-platform",
    ]
  }
}

resource "google_compute_route" "source_to_dest" {
  for_each = { for route in var.routes : route.name => route }
  # adhere to max router name length and make sure name doesnt end in "-" since it's also not allowed
  name              = trimsuffix(substr("${local.nat_router_name}-route-${each.value.name}", 0, 63), "-")
  network           = var.nat_router_source.network_name
  dest_range        = each.value.destination_ip_range
  next_hop_instance = google_compute_instance.nat_instance.self_link
  priority          = each.value.priority
}

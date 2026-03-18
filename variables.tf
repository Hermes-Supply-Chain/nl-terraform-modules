variable "project" {
  type = string
}

variable "region" {
  type = string
}

variable "zone" {
  type = string
}

variable "nat_router_source" {
  type = object({
    network_name = string
    subnet_name  = string
    interface_ip = string
  })
  description = "Set the source network interface for the NAT router VM"
}

variable "nat_router_destination" {
  type = object({
    network_name = string
    subnet_name  = string
    interface_ip = string
  })
  description = "Set the destination network interface for the NAT router VM"
}

variable "preroutings" {
  type = list(object({
    source_port      = number
    destination_ip   = string
    destination_port = number
  }))
  description = "Prerouting commands to be included in the startup script"
  default     = []
}

variable "routes" {
  type = list(object({
    name                 = string
    destination_ip_range = string
    via_ip               = string
    priority             = optional(number, 1000)
  }))
  description = "Routes to add to the NAT router. destination_ip_range = The range of IP addresses which are supposed to be routed through the destination network"
  default     = []
}

variable "name_addition" {
  type        = string
  description = "Optional addition to the name if two NAT are neccessary between the same networks"
  default     = null
}

variable "cmek" {
  type        = string
  description = "cmek for instance encryption"
}

variable "machine_type" {
  type        = string
  description = "Which kind of machine type the NAT router VM should use"
  default     = "e2-small"
}

variable "image" {
  type        = string
  description = "Which image the NAT router VM should use"
  default     = "debian-cloud/debian-12"
}

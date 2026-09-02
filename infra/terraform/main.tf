locals {
  labels = {
    service     = var.service_name
    environment = var.environment
    managed_by  = "terraform-plan-only"
  }
}

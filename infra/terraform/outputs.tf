output "service_name" {
  description = "Logical service name for deployment handoff."
  value       = var.service_name
}

output "container_image" {
  description = "Container image expected by the deployment runtime."
  value       = var.container_image
}

output "container_port" {
  description = "FastAPI container port."
  value       = var.container_port
}

output "labels" {
  description = "Plan-only labels a downstream module/provider can apply."
  value       = local.labels
}

output "memory_url" {
  description = "Memory endpoint configured for the service."
  value       = var.memory_url
  sensitive   = true
}

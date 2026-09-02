variable "environment" {
  type        = string
  description = "Deployment environment name (e.g. dev, staging, prod)."
  default     = "dev"
}

variable "service_name" {
  type        = string
  description = "Logical service name used by downstream deployment tooling."
  default     = "openai-interview-control-plane"
}

variable "container_image" {
  type        = string
  description = "Container image tag produced by scripts/docker_check.sh or CI."
  default     = "openai-interview-control-plane:local"
}

variable "container_port" {
  type        = number
  description = "HTTP port exposed by the FastAPI container."
  default     = 8080
}

variable "memory_url" {
  type        = string
  description = "Memory service URL injected into the container by the runtime environment."
  default     = "http://127.0.0.1:8601"
}

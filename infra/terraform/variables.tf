# All input variables for the root module.
# Every variable gets a type and a description; defaults only when safe.

variable "environment" {
  type        = string
  description = "Deployment environment name (e.g. dev, staging, prod)."
}

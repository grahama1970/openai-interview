terraform {
  required_version = ">= 1.5.0"

  required_providers {
    # Pin every provider you use. Example:
    # aws = {
    #   source  = "hashicorp/aws"
    #   version = "~> 5.0"
    # }
  }

  # Configure a remote backend before team use. Example:
  # backend "s3" {}
}

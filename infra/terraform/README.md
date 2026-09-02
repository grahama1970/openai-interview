# terraform

Terraform root module scaffolded by the /terraform skill using the standard
HashiCorp module structure.

## Layout

- `main.tf` — resources and child module calls (composition only)
- `variables.tf` — all input variables, typed and described
- `outputs.tf` — all outputs, described
- `versions.tf` — Terraform + provider version pins, backend config
- `providers.tf` — provider blocks (no credentials)
- `envs/` — per-environment `*.tfvars` files (gitignored; commit `.example` only)
- `modules/` — reusable child modules, each with its own main/variables/outputs

## Workflow

This module is a deployment handoff, not an apply script. Use it to prove the
service has typed deployment inputs/outputs after the Docker check passes.

```bash
terraform init
terraform fmt -recursive
terraform validate
terraform plan -var-file=envs/dev.tfvars -out=dev.tfplan
```

Do not run `terraform apply` without an explicit human deployment decision.

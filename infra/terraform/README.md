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

```bash
terraform init
terraform fmt -recursive
terraform validate
terraform plan -var-file=envs/dev.tfvars -out=dev.tfplan
terraform apply dev.tfplan
```

locals {
  common_tags        = merge({ "managed-by" = "terraform" })
  current_region     = data.aws_region.current.name
  current_account_id = data.aws_caller_identity.current.account_id
  full_name          = "ecr-create-on-push-${local.name_suffix}"
  repo_tags          = merge(var.REPO_TAGS)
  name_suffix        = var.name != "" ? "-${var.name}" : ""
}
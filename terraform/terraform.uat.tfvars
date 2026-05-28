aws_region             = "ap-southeast-2"
project_name           = "granthrive"
environment            = "uat"
domain_name            = "grantthrive.com"
api_subdomain          = "api"
uat_api_subdomain      = "api.uat"
route53_zone_id        = "Z09860173N0NGB56RP1JJ"
alb_certificate_arn    = "arn:aws:acm:ap-southeast-2:547154049278:certificate/1f66fa1a-f0da-4c2b-8189-c052f65ec79b"

# Keep both image values present to avoid accidental rollback.
# First deploy: leave empty to fail, then update after ECR repo is created
backend_image          = "547154049278.dkr.ecr.ap-southeast-2.amazonaws.com/granthrive-uat/backend:prod-latest"
uat_backend_image      = "547154049278.dkr.ecr.ap-southeast-2.amazonaws.com/granthrive-uat/backend:uat-latest"

desired_count          = 0
uat_desired_count      = 1

frontend_base_url      = "https://app.uat.grantthrive.com"
marketing_base_url     = "https://www.grantthrive.com"
aws_s3_bucket          = "grantthrive-documents-uat"
aws_s3_use_local_fallback = false
aws_ses_enabled        = true
aws_ses_region         = "ap-southeast-2"
aws_ses_from_email     = "hello@grantthrive.com"
mail_server            = "email-smtp.ap-southeast-2.amazonaws.com"
mail_port              = 587
mail_use_tls           = true
mail_username          = ""
mail_password          = ""
mail_default_sender    = "GrantThrive <noreply@grantthrive.com>"

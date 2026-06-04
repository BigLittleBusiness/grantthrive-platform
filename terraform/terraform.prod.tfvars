aws_region          = "ap-southeast-2"
project_name        = "granthrive"
environment         = "prod"
domain_name         = "grantthrive.com"
api_subdomain       = "api"
uat_api_subdomain   = "api.uat"
route53_zone_id     = "Z09860173N0NGB56RP1JJ"
alb_certificate_arn = "arn:aws:acm:ap-southeast-2:547154049278:certificate/d4ad5f44-ff5c-4623-9b20-ad579d457320"

backend_image     = "547154049278.dkr.ecr.ap-southeast-2.amazonaws.com/granthrive-prod/backend:prod-latest"
uat_backend_image = "547154049278.dkr.ecr.ap-southeast-2.amazonaws.com/granthrive-prod/backend:uat-latest"

desired_count     = 1
uat_desired_count = 1

db_name     = "granthrive"
uat_db_name = "granthrive_uat"

task_cpu    = 256
task_memory = 512

frontend_base_url         = "https://app.grantthrive.com"
marketing_base_url        = "https://www.grantthrive.com"
aws_s3_bucket             = "grantthrive-documents-prod"
aws_s3_use_local_fallback = false
aws_ses_enabled           = true
aws_ses_region            = "ap-southeast-2"
aws_ses_from_email        = "hello@grantthrive.com"
mail_server               = "email-smtp.ap-southeast-2.amazonaws.com"
mail_port                 = 587
mail_use_tls              = true
mail_username             = ""
mail_password             = ""
mail_default_sender       = "GrantThrive <noreply@grantthrive.com>"

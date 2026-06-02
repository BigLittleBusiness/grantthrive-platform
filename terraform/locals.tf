data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  is_prod            = var.environment == "prod"
  is_uat             = var.environment == "uat"
  use_shared_rds_alb = local.is_prod
  name_prefix        = "${var.project_name}-${var.environment}"
  shared_name_prefix = "${var.project_name}-${var.shared_infra_owner_environment}"
  azs                = slice(data.aws_availability_zones.available.names, 0, 2)
  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Repository  = "grantthrive-platform"
  }

  api_hostname     = "${var.api_subdomain}.${var.domain_name}"
  uat_api_hostname = "${var.uat_api_subdomain}.${var.domain_name}"
  env_api_hostname = local.is_prod ? local.api_hostname : local.uat_api_hostname

  # RDS reference - prod reuses UAT-owned shared instance.
  rds_instance_address = local.use_shared_rds_alb ? data.aws_db_instance.shared_rds[0].address : aws_db_instance.backend[0].address
  rds_instance_port    = local.use_shared_rds_alb ? data.aws_db_instance.shared_rds[0].port : aws_db_instance.backend[0].port

  # ALB reference - prod reuses UAT-owned shared ALB.
  alb_arn            = local.use_shared_rds_alb ? data.aws_lb.shared_alb[0].arn : aws_lb.backend[0].arn
  alb_dns_name       = local.use_shared_rds_alb ? data.aws_lb.shared_alb[0].dns_name : aws_lb.backend[0].dns_name
  alb_zone_id        = local.use_shared_rds_alb ? data.aws_lb.shared_alb[0].zone_id : aws_lb.backend[0].zone_id
  vpc_id             = local.use_shared_rds_alb ? data.aws_lb.shared_alb[0].vpc_id : aws_vpc.this[0].id
  private_subnet_ids = local.use_shared_rds_alb ? data.aws_db_subnet_group.shared_rds[0].subnet_ids : aws_subnet.private[*].id

  redis_url                  = "redis://${aws_elasticache_cluster.redis.cache_nodes[0].address}:${aws_elasticache_cluster.redis.port}/0"
  shared_prod_secret_payload = local.use_shared_rds_alb ? jsondecode(data.aws_secretsmanager_secret_version.shared_prod_app_config[0].secret_string) : {}
  managed_prod_database_url  = "postgresql://${var.db_username}:${random_password.db_password.result}@${local.rds_instance_address}:${local.rds_instance_port}/${var.db_name}"
  prod_database_url          = local.use_shared_rds_alb ? local.shared_prod_secret_payload.DATABASE_URL : local.managed_prod_database_url
  uat_database_url           = "postgresql://${var.db_username}:${random_password.db_password.result}@${local.rds_instance_address}:${local.rds_instance_port}/${var.uat_db_name}"

  prod_secret_payload = {
    SECRET_KEY           = random_password.prod_secret_key.result
    FIELD_ENCRYPTION_KEY = base64encode(random_password.prod_field_encryption_key.result)
    FIELD_HMAC_KEY       = base64encode(random_password.prod_field_hmac_key.result)
    DATABASE_URL         = local.prod_database_url
    REDIS_URL            = local.redis_url
    MAIL_SERVER          = var.mail_server
    MAIL_PORT            = tostring(var.mail_port)
    MAIL_USE_TLS         = tostring(var.mail_use_tls)
    MAIL_USERNAME        = var.mail_username
    MAIL_PASSWORD        = var.mail_password
    MAIL_DEFAULT_SENDER  = var.mail_default_sender
  }

  uat_secret_payload = {
    SECRET_KEY           = random_password.uat_secret_key.result
    FIELD_ENCRYPTION_KEY = base64encode(random_password.uat_field_encryption_key.result)
    FIELD_HMAC_KEY       = base64encode(random_password.uat_field_hmac_key.result)
    DATABASE_URL         = local.uat_database_url
    REDIS_URL            = local.redis_url
    MAIL_SERVER          = var.mail_server
    MAIL_PORT            = tostring(var.mail_port)
    MAIL_USE_TLS         = tostring(var.mail_use_tls)
    MAIL_USERNAME        = var.mail_username
    MAIL_PASSWORD        = var.mail_password
    MAIL_DEFAULT_SENDER  = var.mail_default_sender
  }
}

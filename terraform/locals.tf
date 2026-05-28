data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  name_prefix = "${var.project_name}-${var.environment}"
  azs         = slice(data.aws_availability_zones.available.names, 0, 2)
  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Repository  = "grantthrive-platform"
  }

  api_hostname      = "${var.api_subdomain}.${var.domain_name}"
  uat_api_hostname  = "${var.uat_api_subdomain}.${var.domain_name}"
  redis_url         = "redis://${aws_elasticache_cluster.redis.cache_nodes[0].address}:${aws_elasticache_cluster.redis.port}/0"
  prod_database_url = "postgresql://${var.db_username}:${random_password.db_password.result}@${aws_db_instance.backend.address}:${aws_db_instance.backend.port}/${var.db_name}"
  uat_database_url  = "postgresql://${var.db_username}:${random_password.db_password.result}@${aws_db_instance.backend.address}:${aws_db_instance.backend.port}/${var.uat_db_name}"

  prod_secret_payload = {
    SECRET_KEY           = random_password.prod_secret_key.result
    FIELD_ENCRYPTION_KEY = random_password.prod_field_encryption_key.result
    FIELD_HMAC_KEY       = random_password.prod_field_hmac_key.result
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
    FIELD_ENCRYPTION_KEY = random_password.uat_field_encryption_key.result
    FIELD_HMAC_KEY       = random_password.uat_field_hmac_key.result
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
output "api_url" {
  value       = "https://${local.api_hostname}"
  description = "Production backend base URL."
}

output "uat_api_url" {
  value       = "https://${local.uat_api_hostname}"
  description = "UAT backend base URL."
}

output "ecr_repository_url" {
  value       = aws_ecr_repository.backend.repository_url
  description = "Backend ECR repository URL."
}

output "ecs_cluster_name" {
  value       = aws_ecs_cluster.this.name
  description = "ECS cluster name."
}

output "prod_service_name" {
  value       = aws_ecs_service.prod.name
  description = "Production ECS service name."
}

output "uat_service_name" {
  value       = aws_ecs_service.uat.name
  description = "UAT ECS service name."
}

output "rds_endpoint" {
  value       = aws_db_instance.backend.address
  description = "RDS endpoint."
}

output "redis_endpoint" {
  value       = aws_elasticache_cluster.redis.cache_nodes[0].address
  description = "Redis endpoint."
}
resource "random_password" "db_password" {
  length  = 24
  special = false
}

resource "random_password" "prod_secret_key" {
  length  = 48
  special = false
}

resource "random_password" "uat_secret_key" {
  length  = 48
  special = false
}

resource "random_password" "prod_field_encryption_key" {
  length  = 44
  special = false
}

resource "random_password" "uat_field_encryption_key" {
  length  = 44
  special = false
}

resource "random_password" "prod_field_hmac_key" {
  length  = 44
  special = false
}

resource "random_password" "uat_field_hmac_key" {
  length  = 44
  special = false
}

resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true
}

resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id
}

resource "aws_subnet" "public" {
  count                   = 2
  vpc_id                  = aws_vpc.this.id
  cidr_block              = var.public_subnet_cidrs[count.index]
  availability_zone       = local.azs[count.index]
  map_public_ip_on_launch = true
}

resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.this.id
  cidr_block        = var.private_subnet_cidrs[count.index]
  availability_zone = local.azs[count.index]
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id
}

resource "aws_route" "public_default" {
  route_table_id         = aws_route_table.public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.this.id
}

resource "aws_route_table_association" "public" {
  count          = 2
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_eip" "nat" {
  domain = "vpc"
}

resource "aws_nat_gateway" "this" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public[0].id
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.this.id
}

resource "aws_route" "private_default" {
  route_table_id         = aws_route_table.private.id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.this.id
}

resource "aws_route_table_association" "private" {
  count          = 2
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}

resource "aws_security_group" "alb" {
  name        = "${local.name_prefix}-alb"
  description = "Public access to the backend ALB"
  vpc_id      = aws_vpc.this.id

  lifecycle {
    create_before_destroy = true
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = var.allowed_cidrs
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = var.allowed_cidrs
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "ecs" {
  name        = "${local.name_prefix}-ecs"
  description = "Backend ECS tasks"
  vpc_id      = aws_vpc.this.id

  lifecycle {
    create_before_destroy = true
  }

  ingress {
    from_port       = 5000
    to_port         = 5000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "db" {
  name        = "${var.project_name}-prod-db"
  description = "RDS access from ECS"
  vpc_id      = aws_vpc.this.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "redis" {
  name        = "${local.name_prefix}-redis"
  description = "Redis access from ECS"
  vpc_id      = aws_vpc.this.id

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_ecr_repository" "backend" {
  name                 = "${local.name_prefix}/backend"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_cloudwatch_log_group" "backend" {
  name              = "/ecs/${local.name_prefix}/backend"
  retention_in_days = 30
}

resource "aws_db_subnet_group" "backend" {
  name       = "${var.project_name}-prod-db"
  subnet_ids = aws_subnet.private[*].id
}

resource "aws_db_instance" "backend" {
  identifier                 = "${var.project_name}-prod-db"
  engine                     = "postgres"
  engine_version             = "16"
  instance_class             = var.db_instance_class
  allocated_storage          = var.db_allocated_storage
  storage_type               = "gp3"
  db_name                    = var.db_name
  username                   = var.db_username
  password                   = random_password.db_password.result
  publicly_accessible        = false
  multi_az                   = false
  storage_encrypted          = true
  backup_retention_period    = var.db_backup_retention_days
  deletion_protection        = var.enable_deletion_protection
  skip_final_snapshot        = true
  db_subnet_group_name       = aws_db_subnet_group.backend.name
  vpc_security_group_ids     = [aws_security_group.db.id]
  apply_immediately          = true
  auto_minor_version_upgrade = true
}

resource "aws_elasticache_subnet_group" "redis" {
  name       = "${local.name_prefix}-redis"
  subnet_ids = aws_subnet.private[*].id
}

resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "${local.name_prefix}-redis"
  engine               = "redis"
  node_type            = var.redis_node_type
  num_cache_nodes      = 1
  port                 = 6379
  parameter_group_name = "default.redis7"
  subnet_group_name    = aws_elasticache_subnet_group.redis.name
  security_group_ids   = [aws_security_group.redis.id]
}

resource "aws_iam_role" "ecs_task_execution" {
  name = "${local.name_prefix}-ecs-task-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy" "ecs_task_execution_secrets" {
  name = "${local.name_prefix}-ecs-task-execution-secrets"
  role = aws_iam_role.ecs_task_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = [
          aws_secretsmanager_secret.prod.arn,
          aws_secretsmanager_secret.uat.arn
        ]
      }
    ]
  })
}

resource "aws_iam_role" "ecs_task" {
  name = "${local.name_prefix}-ecs-task"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "ecs_task_ses" {
  name = "${local.name_prefix}-ecs-task-ses"
  role = aws_iam_role.ecs_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "ses:SendEmail",
        "ses:SendRawEmail",
        "ses:GetSendQuota",
        "ses:GetSendStatistics"
      ]
      Resource = "*"
    }]
  })
}

resource "aws_iam_role_policy" "ecs_task_s3" {
  name = "${local.name_prefix}-ecs-task-s3"
  role = aws_iam_role.ecs_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = "arn:aws:s3:::${var.aws_s3_bucket}"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = "arn:aws:s3:::${var.aws_s3_bucket}/*"
      }
    ]
  })
}

resource "aws_ecs_cluster" "this" {
  name = "${local.name_prefix}-cluster"
}

resource "aws_secretsmanager_secret" "prod" {
  name = "${local.name_prefix}/prod/app-config"
}

resource "aws_secretsmanager_secret_version" "prod" {
  secret_id     = aws_secretsmanager_secret.prod.id
  secret_string = jsonencode(local.prod_secret_payload)
}

resource "aws_secretsmanager_secret" "uat" {
  name = "${local.name_prefix}/uat/app-config"
}

resource "aws_secretsmanager_secret_version" "uat" {
  secret_id     = aws_secretsmanager_secret.uat.id
  secret_string = jsonencode(local.uat_secret_payload)
}

resource "aws_lb" "backend" {
  name               = substr("${local.name_prefix}-alb", 0, 32)
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id
}

resource "aws_lb_target_group" "prod" {
  name        = substr("${local.name_prefix}-prod", 0, 32)
  port        = 5000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.this.id
  target_type = "ip"

  health_check {
    path                = "/api/health"
    protocol            = "HTTP"
    matcher             = "200"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 2
  }
}

resource "aws_lb_target_group" "uat" {
  name        = substr("${local.name_prefix}-uat", 0, 32)
  port        = 5000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.this.id
  target_type = "ip"

  health_check {
    path                = "/api/health"
    protocol            = "HTTP"
    matcher             = "200"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 2
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.backend.arn
  port              = 80
  protocol          = "HTTP"

  dynamic "default_action" {
    for_each = var.alb_certificate_arn != "" ? [1] : []
    content {
      type = "redirect"

      redirect {
        port        = "443"
        protocol    = "HTTPS"
        status_code = "HTTP_301"
      }
    }
  }

  dynamic "default_action" {
    for_each = var.alb_certificate_arn == "" ? [1] : []
    content {
      type             = "forward"
      target_group_arn = aws_lb_target_group.prod.arn
    }
  }
}

resource "aws_lb_listener" "https" {
  count             = var.alb_certificate_arn != "" ? 1 : 0
  load_balancer_arn = aws_lb.backend.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = var.alb_certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.prod.arn
  }
}

resource "aws_lb_listener_rule" "uat" {
  count        = 1
  listener_arn = var.alb_certificate_arn != "" ? aws_lb_listener.https[0].arn : aws_lb_listener.http.arn
  priority     = 10

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.uat.arn
  }

  condition {
    host_header {
      values = [local.uat_api_hostname]
    }
  }
}

resource "aws_ecs_task_definition" "prod" {
  family                   = "${local.name_prefix}-prod"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = tostring(var.task_cpu)
  memory                   = tostring(var.task_memory)
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "backend"
      image     = var.backend_image
      essential = true
      portMappings = [
        {
          containerPort = 5000
          hostPort      = 5000
          protocol      = "tcp"
        }
      ]
      environment = [
        { name = "FLASK_ENV", value = "production" },
        { name = "PORT", value = "5000" },
        { name = "AWS_REGION", value = var.aws_region },
        { name = "AWS_S3_BUCKET", value = var.aws_s3_bucket },
        { name = "AWS_S3_USE_LOCAL_FALLBACK", value = tostring(var.aws_s3_use_local_fallback) },
        { name = "AWS_SES_ENABLED", value = tostring(var.aws_ses_enabled) },
        { name = "AWS_SES_REGION", value = var.aws_ses_region },
        { name = "AWS_SES_FROM_EMAIL", value = var.aws_ses_from_email },
        { name = "FRONTEND_BASE_URL", value = var.frontend_base_url },
        { name = "MARKETING_BASE_URL", value = var.marketing_base_url }
      ]
      secrets = [
        { name = "SECRET_KEY", valueFrom = "${aws_secretsmanager_secret.prod.arn}:SECRET_KEY::" },
        { name = "FIELD_ENCRYPTION_KEY", valueFrom = "${aws_secretsmanager_secret.prod.arn}:FIELD_ENCRYPTION_KEY::" },
        { name = "FIELD_HMAC_KEY", valueFrom = "${aws_secretsmanager_secret.prod.arn}:FIELD_HMAC_KEY::" },
        { name = "DATABASE_URL", valueFrom = "${aws_secretsmanager_secret.prod.arn}:DATABASE_URL::" },
        { name = "REDIS_URL", valueFrom = "${aws_secretsmanager_secret.prod.arn}:REDIS_URL::" },
        { name = "MAIL_SERVER", valueFrom = "${aws_secretsmanager_secret.prod.arn}:MAIL_SERVER::" },
        { name = "MAIL_PORT", valueFrom = "${aws_secretsmanager_secret.prod.arn}:MAIL_PORT::" },
        { name = "MAIL_USE_TLS", valueFrom = "${aws_secretsmanager_secret.prod.arn}:MAIL_USE_TLS::" },
        { name = "MAIL_USERNAME", valueFrom = "${aws_secretsmanager_secret.prod.arn}:MAIL_USERNAME::" },
        { name = "MAIL_PASSWORD", valueFrom = "${aws_secretsmanager_secret.prod.arn}:MAIL_PASSWORD::" },
        { name = "MAIL_DEFAULT_SENDER", valueFrom = "${aws_secretsmanager_secret.prod.arn}:MAIL_DEFAULT_SENDER::" }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.backend.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "prod"
        }
      }
    }
  ])
}

resource "aws_ecs_task_definition" "uat" {
  family                   = "${local.name_prefix}-uat"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = tostring(var.task_cpu)
  memory                   = tostring(var.task_memory)
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "backend"
      image     = var.uat_backend_image != "" ? var.uat_backend_image : var.backend_image
      essential = true
      portMappings = [
        {
          containerPort = 5000
          hostPort      = 5000
          protocol      = "tcp"
        }
      ]
      environment = [
        { name = "FLASK_ENV", value = "production" },
        { name = "PORT", value = "5000" },
        { name = "AWS_REGION", value = var.aws_region },
        { name = "AWS_S3_BUCKET", value = var.aws_s3_bucket },
        { name = "AWS_S3_USE_LOCAL_FALLBACK", value = tostring(var.aws_s3_use_local_fallback) },
        { name = "AWS_SES_ENABLED", value = tostring(var.aws_ses_enabled) },
        { name = "AWS_SES_REGION", value = var.aws_ses_region },
        { name = "AWS_SES_FROM_EMAIL", value = var.aws_ses_from_email },
        { name = "FRONTEND_BASE_URL", value = var.frontend_base_url },
        { name = "MARKETING_BASE_URL", value = var.marketing_base_url }
      ]
      secrets = [
        { name = "SECRET_KEY", valueFrom = "${aws_secretsmanager_secret.uat.arn}:SECRET_KEY::" },
        { name = "FIELD_ENCRYPTION_KEY", valueFrom = "${aws_secretsmanager_secret.uat.arn}:FIELD_ENCRYPTION_KEY::" },
        { name = "FIELD_HMAC_KEY", valueFrom = "${aws_secretsmanager_secret.uat.arn}:FIELD_HMAC_KEY::" },
        { name = "DATABASE_URL", valueFrom = "${aws_secretsmanager_secret.uat.arn}:DATABASE_URL::" },
        { name = "REDIS_URL", valueFrom = "${aws_secretsmanager_secret.uat.arn}:REDIS_URL::" },
        { name = "MAIL_SERVER", valueFrom = "${aws_secretsmanager_secret.uat.arn}:MAIL_SERVER::" },
        { name = "MAIL_PORT", valueFrom = "${aws_secretsmanager_secret.uat.arn}:MAIL_PORT::" },
        { name = "MAIL_USE_TLS", valueFrom = "${aws_secretsmanager_secret.uat.arn}:MAIL_USE_TLS::" },
        { name = "MAIL_USERNAME", valueFrom = "${aws_secretsmanager_secret.uat.arn}:MAIL_USERNAME::" },
        { name = "MAIL_PASSWORD", valueFrom = "${aws_secretsmanager_secret.uat.arn}:MAIL_PASSWORD::" },
        { name = "MAIL_DEFAULT_SENDER", valueFrom = "${aws_secretsmanager_secret.uat.arn}:MAIL_DEFAULT_SENDER::" }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.backend.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "uat"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "prod" {
  name            = "${local.name_prefix}-prod"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.prod.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.prod.arn
    container_name   = "backend"
    container_port   = 5000
  }

  depends_on = [aws_lb_listener.http]
}

resource "aws_ecs_service" "uat" {
  name            = "${local.name_prefix}-uat"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.uat.arn
  desired_count   = var.uat_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.uat.arn
    container_name   = "backend"
    container_port   = 5000
  }

  depends_on = [aws_lb_listener.http]
}

resource "aws_route53_record" "api" {
  count   = var.route53_zone_id == "" ? 0 : 1
  zone_id = var.route53_zone_id
  name    = local.api_hostname
  type    = "A"

  alias {
    name                   = aws_lb.backend.dns_name
    zone_id                = aws_lb.backend.zone_id
    evaluate_target_health = true
  }
}

resource "aws_route53_record" "uat_api" {
  count   = var.route53_zone_id == "" ? 0 : 1
  zone_id = var.route53_zone_id
  name    = local.uat_api_hostname
  type    = "A"

  alias {
    name                   = aws_lb.backend.dns_name
    zone_id                = aws_lb.backend.zone_id
    evaluate_target_health = true
  }
}
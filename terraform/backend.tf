terraform {
  backend "s3" {
    bucket         = "grantthrive-terraform-state-backend-547154049278"
    key            = "terraform.tfstate"
    region         = "ap-southeast-2"
    encrypt        = "true"
    dynamodb_table = "grantthrive-terraform-locks"
  }
}

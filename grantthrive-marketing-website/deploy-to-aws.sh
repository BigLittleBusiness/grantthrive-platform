#!/bin/bash

# GrantThrive Marketing Website - AWS Deployment Script
# Usage: ./deploy-to-aws.sh [bucket-name]

set -e

# Configuration
BUCKET_NAME=${1:-"grantthrive-marketing-website"}
REGION="ap-southeast-2"  # Sydney region
PROFILE="default"        # AWS CLI profile

echo "🚀 Starting GrantThrive Marketing Website Deployment to AWS"
echo "=================================================="
echo "Bucket: $BUCKET_NAME"
echo "Region: $REGION"
echo "Profile: $PROFILE"
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed. Please install it first."
    echo "   https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
    exit 1
fi

# Check if AWS credentials are configured
if ! aws sts get-caller-identity --profile $PROFILE &> /dev/null; then
    echo "❌ AWS credentials not configured. Please run 'aws configure'"
    exit 1
fi

echo "✅ AWS CLI configured and credentials verified"

# Install dependencies and build
echo "📦 Installing dependencies..."
npm install

echo "🔨 Building production version..."
npm run build

# Check if bucket exists, create if not
echo "🪣 Checking S3 bucket..."
if aws s3 ls "s3://$BUCKET_NAME" --profile $PROFILE 2>&1 | grep -q 'NoSuchBucket'; then
    echo "📝 Creating S3 bucket: $BUCKET_NAME"
    aws s3 mb "s3://$BUCKET_NAME" --region $REGION --profile $PROFILE
    
    echo "🌐 Configuring bucket for static website hosting..."
    aws s3 website "s3://$BUCKET_NAME" \
        --index-document index.html \
        --error-document index.html \
        --profile $PROFILE
    
    echo "🔓 Setting bucket policy for public access..."
    aws s3api put-bucket-policy \
        --bucket $BUCKET_NAME \
        --policy file://s3-bucket-policy.json \
        --profile $PROFILE
else
    echo "✅ S3 bucket already exists: $BUCKET_NAME"
fi

# Upload files to S3
echo "📤 Uploading files to S3..."
aws s3 sync dist/ "s3://$BUCKET_NAME" \
    --delete \
    --profile $PROFILE \
    --cache-control "max-age=31536000" \
    --exclude "*.html" \
    --exclude "*.json"

# Upload HTML files with no-cache headers
aws s3 sync dist/ "s3://$BUCKET_NAME" \
    --profile $PROFILE \
    --cache-control "no-cache" \
    --include "*.html" \
    --include "*.json"

# Get website URL
WEBSITE_URL="http://$BUCKET_NAME.s3-website-$REGION.amazonaws.com"

echo ""
echo "🎉 Deployment completed successfully!"
echo "=================================================="
echo "Website URL: $WEBSITE_URL"
echo ""
echo "📋 Next Steps:"
echo "1. Test the website: $WEBSITE_URL"
echo "2. Set up CloudFront for HTTPS and custom domain"
echo "3. Configure Route 53 for custom domain"
echo "4. Set up monitoring and alerts"
echo ""
echo "💡 For HTTPS and custom domain, use the CloudFormation template:"
echo "   aws cloudformation create-stack --stack-name grantthrive-website --template-body file://cloudformation-template.yaml --parameters ParameterKey=DomainName,ParameterValue=yourdomain.com"


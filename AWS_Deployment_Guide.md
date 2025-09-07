# GrantThrive Marketing Website - AWS Deployment Guide

## 📦 **Package Contents**

This package contains everything needed to deploy the GrantThrive marketing website to AWS:

### **Source Code Structure:**
```
grantthrive-marketing-website/
├── src/                          # React source code
│   ├── App.jsx                   # Main application component
│   ├── App.css                   # Styling and branding
│   └── components/               # Reusable components
├── public/                       # Static assets
│   ├── GrantThrive_Brochure.pdf  # Updated marketing brochure
│   └── index.html                # HTML template
├── dist/                         # Production build (ready for deployment)
│   ├── index.html                # Built HTML
│   ├── assets/                   # Optimized CSS/JS bundles
│   └── GrantThrive_Brochure.pdf  # Marketing materials
├── package.json                  # Dependencies and scripts
├── vite.config.js               # Build configuration
└── tailwind.config.js           # Styling configuration
```

## 🚀 **AWS Deployment Options**

### **Option 1: AWS S3 + CloudFront (Recommended)**

#### **Benefits:**
- **Cost-effective**: ~$1-5/month for typical traffic
- **High performance**: Global CDN with CloudFront
- **Scalable**: Handles traffic spikes automatically
- **SSL included**: Free SSL certificates
- **Easy updates**: Simple file uploads

#### **Deployment Steps:**

1. **Create S3 Bucket:**
```bash
aws s3 mb s3://grantthrive-marketing-website
```

2. **Configure S3 for Static Website Hosting:**
```bash
aws s3 website s3://grantthrive-marketing-website \
  --index-document index.html \
  --error-document index.html
```

3. **Upload Built Files:**
```bash
cd grantthrive-marketing-website/dist
aws s3 sync . s3://grantthrive-marketing-website --delete
```

4. **Set Public Read Permissions:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::grantthrive-marketing-website/*"
    }
  ]
}
```

5. **Create CloudFront Distribution:**
- Origin: S3 bucket website endpoint
- Default root object: index.html
- Error pages: 404 → /index.html (for React routing)
- SSL certificate: Request free certificate via ACM

### **Option 2: AWS Amplify (Easiest)**

#### **Benefits:**
- **One-click deployment**: Connect GitHub repository
- **Automatic builds**: Builds on every commit
- **Branch deployments**: Staging and production environments
- **Built-in SSL**: Automatic HTTPS
- **Custom domains**: Easy domain configuration

#### **Deployment Steps:**

1. **Push code to GitHub repository**
2. **Connect to AWS Amplify:**
   - Go to AWS Amplify Console
   - Click "New app" → "Host web app"
   - Connect GitHub repository
   - Select branch (main/master)

3. **Build Settings (amplify.yml):**
```yaml
version: 1
frontend:
  phases:
    preBuild:
      commands:
        - npm ci
    build:
      commands:
        - npm run build
  artifacts:
    baseDirectory: dist
    files:
      - '**/*'
  cache:
    paths:
      - node_modules/**/*
```

### **Option 3: AWS EC2 + Nginx (Advanced)**

#### **Benefits:**
- **Full control**: Complete server management
- **Custom configuration**: Advanced routing and caching
- **Multiple applications**: Host multiple sites
- **Server-side capabilities**: Add backend features later

#### **Deployment Steps:**

1. **Launch EC2 Instance:**
   - Ubuntu 22.04 LTS
   - t3.micro (free tier eligible)
   - Security group: HTTP (80), HTTPS (443), SSH (22)

2. **Install Dependencies:**
```bash
sudo apt update
sudo apt install nginx nodejs npm
```

3. **Configure Nginx:**
```nginx
server {
    listen 80;
    server_name grantthrive.com.au www.grantthrive.com.au;
    root /var/www/grantthrive;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

4. **Deploy Files:**
```bash
sudo mkdir -p /var/www/grantthrive
sudo cp -r dist/* /var/www/grantthrive/
sudo chown -R www-data:www-data /var/www/grantthrive
```

## 🔧 **Configuration Files Included**

### **1. package.json**
- All dependencies and build scripts
- Optimized for production deployment
- Includes development and build commands

### **2. vite.config.js**
- Production build optimization
- Asset bundling configuration
- Performance optimizations

### **3. tailwind.config.js**
- GrantThrive brand colors and styling
- Responsive design configuration
- Component styling framework

### **4. AWS-Specific Files (Created for you):**

#### **S3 Bucket Policy (s3-bucket-policy.json):**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::grantthrive-marketing-website/*"
    }
  ]
}
```

#### **CloudFormation Template (cloudformation-template.yaml):**
```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'GrantThrive Marketing Website Infrastructure'

Parameters:
  DomainName:
    Type: String
    Default: grantthrive.com.au
    Description: Domain name for the website

Resources:
  S3Bucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub '${DomainName}-marketing-website'
      WebsiteConfiguration:
        IndexDocument: index.html
        ErrorDocument: index.html
      PublicAccessBlockConfiguration:
        BlockPublicAcls: false
        BlockPublicPolicy: false
        IgnorePublicAcls: false
        RestrictPublicBuckets: false

  CloudFrontDistribution:
    Type: AWS::CloudFront::Distribution
    Properties:
      DistributionConfig:
        Origins:
          - DomainName: !GetAtt S3Bucket.RegionalDomainName
            Id: S3Origin
            CustomOriginConfig:
              HTTPPort: 80
              HTTPSPort: 443
              OriginProtocolPolicy: http-only
        Enabled: true
        DefaultRootObject: index.html
        DefaultCacheBehavior:
          TargetOriginId: S3Origin
          ViewerProtocolPolicy: redirect-to-https
          AllowedMethods:
            - GET
            - HEAD
          CachedMethods:
            - GET
            - HEAD
          Compress: true
        CustomErrorResponses:
          - ErrorCode: 404
            ResponseCode: 200
            ResponsePagePath: /index.html
        Aliases:
          - !Ref DomainName
          - !Sub 'www.${DomainName}'
```

## 📋 **Pre-Deployment Checklist**

### **Before Deploying:**
- [ ] Domain name registered and DNS configured
- [ ] AWS account set up with appropriate permissions
- [ ] SSL certificate requested (if using custom domain)
- [ ] Analytics tracking codes added (Google Analytics, etc.)
- [ ] Contact forms configured with backend service
- [ ] Performance testing completed

### **After Deployment:**
- [ ] Test all pages and functionality
- [ ] Verify mobile responsiveness
- [ ] Check ROI calculator functionality
- [ ] Test download links (brochure, etc.)
- [ ] Verify SSL certificate installation
- [ ] Set up monitoring and alerts

## 🔍 **Testing Instructions**

### **Local Testing:**
```bash
cd grantthrive-marketing-website
npm install
npm run dev
# Open http://localhost:5173
```

### **Production Build Testing:**
```bash
npm run build
npm run preview
# Open http://localhost:4173
```

### **Key Features to Test:**
1. **Homepage**: Hero section, statistics, call-to-action buttons
2. **ROI Calculator**: Input changes, calculations, results display
3. **Navigation**: All menu items and page routing
4. **Mobile**: Responsive design on various screen sizes
5. **Downloads**: Brochure PDF download functionality
6. **Forms**: Contact forms and demo requests

## 💰 **Cost Estimates**

### **AWS S3 + CloudFront:**
- **S3 Storage**: ~$0.50/month (for website files)
- **CloudFront**: ~$1-5/month (depending on traffic)
- **Route 53**: $0.50/month (hosted zone)
- **SSL Certificate**: Free (AWS Certificate Manager)
- **Total**: ~$2-6/month

### **AWS Amplify:**
- **Build minutes**: Free tier includes 1000 minutes/month
- **Hosting**: $0.15/GB stored + $0.15/GB served
- **Custom domain**: Free
- **SSL**: Free
- **Total**: ~$1-10/month (depending on traffic)

### **AWS EC2:**
- **t3.micro**: Free tier for 12 months, then ~$8.50/month
- **Elastic IP**: Free when attached to running instance
- **Data transfer**: First 1GB free, then $0.09/GB
- **Total**: ~$0-15/month

## 🚀 **Quick Start Commands**

### **For S3 Deployment:**
```bash
# Extract package
tar -xzf GrantThrive_Marketing_Website_AWS_Package.tar.gz
cd grantthrive-marketing-website

# Build for production
npm install
npm run build

# Deploy to S3 (replace bucket name)
aws s3 sync dist/ s3://your-bucket-name --delete
```

### **For Amplify Deployment:**
```bash
# Extract package
tar -xzf GrantThrive_Marketing_Website_AWS_Package.tar.gz

# Push to GitHub repository
git init
git add .
git commit -m "Initial GrantThrive marketing website"
git remote add origin https://github.com/yourusername/grantthrive-marketing.git
git push -u origin main

# Then connect repository in AWS Amplify Console
```

## 📞 **Support Information**

### **Included in Package:**
- Complete source code with comments
- Production-ready build files
- AWS deployment configurations
- Comprehensive documentation
- Testing instructions
- Cost optimization guidelines

### **Technical Specifications:**
- **Framework**: React 18 with Vite
- **Styling**: Tailwind CSS with custom GrantThrive branding
- **Components**: Shadcn/ui for professional UI components
- **Icons**: Lucide React for consistent iconography
- **Charts**: Recharts for ROI visualizations
- **Build**: Optimized for production with code splitting
- **SEO**: Meta tags and structured data included
- **Performance**: Lighthouse score optimized

This package provides everything needed for a professional AWS deployment of the GrantThrive marketing website with the updated pricing structure and enhanced value propositions.


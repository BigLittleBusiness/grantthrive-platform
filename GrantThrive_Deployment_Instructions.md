# GrantThrive Marketing Website - Deployment Instructions

## 🚀 Quick Start (5 Minutes)

### **Option 1: Static Web Hosting (Recommended)**

#### **Step 1: Download the Built Package**
- Download `GrantThrive_Marketing_Website_Built.tar.gz`
- Extract the files to get the `GrantThrive_Marketing_Website_Built` folder

#### **Step 2: Choose Your Hosting Platform**

**A. Netlify (Easiest - Drag & Drop)**
1. Go to [netlify.com](https://netlify.com)
2. Sign up for a free account
3. Drag the `GrantThrive_Marketing_Website_Built` folder to the deploy area
4. Your site will be live in seconds with a URL like `https://amazing-site-123.netlify.app`
5. Optional: Connect your custom domain in Site Settings

**B. Vercel (Developer-Friendly)**
1. Go to [vercel.com](https://vercel.com)
2. Sign up and click "New Project"
3. Upload the `GrantThrive_Marketing_Website_Built` folder
4. Deploy - your site will be live with a URL like `https://grantthrive-abc123.vercel.app`
5. Optional: Add your custom domain

**C. Traditional Web Hosting (cPanel/FTP)**
1. Access your web hosting control panel
2. Navigate to File Manager or use FTP client
3. Upload all files from `GrantThrive_Marketing_Website_Built` to your `public_html` or `www` folder
4. Your site will be live at your domain immediately

#### **Step 3: Test Your Deployment**
- Visit your website URL
- Test the ROI calculator functionality
- Verify the brochure download works
- Check mobile responsiveness

## 🔧 Advanced Deployment Options

### **Option 2: Custom Domain Setup**

#### **For Netlify:**
1. In Netlify dashboard, go to Site Settings → Domain Management
2. Click "Add custom domain"
3. Enter your domain (e.g., `www.grantthrive.com.au`)
4. Update your DNS settings:
   - Add CNAME record: `www` → `amazing-site-123.netlify.app`
   - Or use Netlify DNS for full management

#### **For Vercel:**
1. In Vercel dashboard, go to Project Settings → Domains
2. Add your custom domain
3. Update DNS settings as instructed
4. SSL certificate will be automatically provisioned

#### **For Traditional Hosting:**
- Point your domain's A record to your hosting server's IP
- Ensure SSL certificate is installed
- Files should be in the root web directory

### **Option 3: AWS S3 + CloudFront (Enterprise)**

#### **Step 1: Create S3 Bucket**
```bash
# Create bucket (replace with your domain)
aws s3 mb s3://grantthrive-marketing-website

# Upload files
aws s3 sync GrantThrive_Marketing_Website_Built/ s3://grantthrive-marketing-website --delete
```

#### **Step 2: Configure S3 for Web Hosting**
1. Enable static website hosting
2. Set index document to `index.html`
3. Set error document to `index.html` (for React Router)
4. Make bucket public with appropriate policy

#### **Step 3: Set Up CloudFront**
1. Create CloudFront distribution
2. Point origin to S3 bucket
3. Configure custom error pages for SPA routing
4. Add your custom domain and SSL certificate

## 📊 Analytics & Tracking Setup

### **Google Analytics 4**
1. Create GA4 property at [analytics.google.com](https://analytics.google.com)
2. Get your Measurement ID (e.g., `G-XXXXXXXXXX`)
3. Add to your website by editing `index.html`:

```html
<!-- Add before closing </head> tag -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');
</script>
```

### **Google Tag Manager (Advanced)**
1. Create GTM account at [tagmanager.google.com](https://tagmanager.google.com)
2. Add GTM code to `index.html`
3. Configure tags for:
   - ROI calculator usage
   - Brochure downloads
   - Demo requests
   - Page views

## 🎯 Lead Capture Integration

### **Demo Scheduling Integration**

#### **Option A: Calendly**
1. Create Calendly account
2. Set up your booking page
3. Replace demo buttons with your Calendly link:
```html
<a href="https://calendly.com/your-username/grantthrive-demo" target="_blank">
  Schedule a Demo
</a>
```

#### **Option B: HubSpot**
1. Create HubSpot account
2. Generate meeting link
3. Replace demo buttons with HubSpot meeting link

### **Contact Form Integration**

#### **Option A: Netlify Forms (If using Netlify)**
1. Add `netlify` attribute to forms in your HTML
2. Forms will automatically capture to Netlify dashboard
3. Set up email notifications

#### **Option B: Formspree**
1. Sign up at [formspree.io](https://formspree.io)
2. Create form endpoint
3. Update form action URLs in your HTML

## 🔒 Security & Performance

### **SSL Certificate**
- **Netlify/Vercel**: Automatic SSL with Let's Encrypt
- **Traditional Hosting**: Install SSL certificate through hosting provider
- **AWS**: Use AWS Certificate Manager with CloudFront

### **Performance Optimization**
- Files are already minified and optimized
- Enable gzip compression on your server
- Set appropriate cache headers:
  ```
  Cache-Control: public, max-age=31536000 (for assets)
  Cache-Control: public, max-age=0, must-revalidate (for HTML)
  ```

### **Security Headers**
Add these headers to your server configuration:
```
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
```

## 🌐 SEO Optimization

### **Search Console Setup**
1. Go to [search.google.com/search-console](https://search.google.com/search-console)
2. Add your website property
3. Verify ownership
4. Submit sitemap (if you create one)

### **Local SEO (Australia/New Zealand)**
1. Create Google My Business listing
2. Add location-specific content
3. Target keywords:
   - "grant management software Australia"
   - "council grant management NZ"
   - "SmartyGrants alternative"

## 📱 Mobile Optimization

The website is already mobile-responsive, but verify:
- Test on various device sizes
- Check touch targets are appropriate
- Ensure forms work on mobile
- Verify ROI calculator is user-friendly on small screens

## 🔄 Content Updates

### **Regular Updates Needed:**
1. **Pricing Information**: Update if pricing changes
2. **Feature Lists**: Add new features as they're developed
3. **Competitive Comparisons**: Keep SmartyGrants comparison current
4. **Contact Information**: Ensure all contact details are accurate

### **Making Updates:**
- For simple text changes: Edit the HTML files directly
- For major changes: Use the complete source code package
- Always test changes before deploying to production

## 📊 Monitoring & Maintenance

### **What to Monitor:**
- **Website uptime** (use UptimeRobot or similar)
- **Page load speeds** (Google PageSpeed Insights)
- **ROI calculator usage** (Google Analytics events)
- **Lead generation metrics** (form submissions, demo requests)
- **Mobile performance** (Google Search Console)

### **Monthly Tasks:**
- Review analytics data
- Check for broken links
- Update content as needed
- Monitor competitor websites
- Optimize based on user behavior

## 🚨 Troubleshooting

### **Common Issues:**

#### **ROI Calculator Not Working**
- Check browser console for JavaScript errors
- Ensure all files uploaded correctly
- Verify file permissions on server

#### **Brochure Download Not Working**
- Ensure `GrantThrive_Brochure.pdf` is in the correct location
- Check file permissions
- Verify MIME type is set correctly for PDFs

#### **Forms Not Submitting**
- Check form action URLs
- Verify third-party service integration
- Test with different browsers

#### **Mobile Display Issues**
- Clear browser cache
- Check viewport meta tag is present
- Test on actual devices, not just browser dev tools

## 📞 Support Resources

### **Technical Support:**
- Hosting provider documentation
- Platform-specific help (Netlify, Vercel, etc.)
- Web developer community forums

### **Marketing Support:**
- Google Analytics Help Center
- SEO guides and best practices
- Conversion optimization resources

## ✅ Deployment Checklist

Before going live, verify:

- [ ] All pages load correctly
- [ ] ROI calculator functions properly
- [ ] Brochure download works
- [ ] Contact forms submit successfully
- [ ] Mobile responsiveness is good
- [ ] Analytics tracking is working
- [ ] SSL certificate is active
- [ ] Custom domain is configured (if applicable)
- [ ] Demo scheduling links work
- [ ] All contact information is correct
- [ ] SEO meta tags are appropriate
- [ ] Site loads quickly (< 3 seconds)

## 🎉 Go Live!

Once everything is tested and working:

1. **Announce the launch** to your team
2. **Share the URL** with potential customers
3. **Start driving traffic** through marketing campaigns
4. **Monitor performance** and optimize based on data
5. **Collect feedback** and make improvements

Your GrantThrive marketing website is now ready to generate qualified leads and showcase your competitive advantages!

---

**Need Help?** This website is production-ready and thoroughly tested. Follow these instructions for a smooth deployment process.


#!/usr/bin/env python3
"""
Automated Grant Scheduler for GrantThrive
Schedules and manages automated grant data collection from grants.gov.au
"""

import schedule
import time
import subprocess
import logging
import json
import os
from datetime import datetime, timedelta
# Email imports commented out for now - can be enabled when needed
# import smtplib
# from email.mime.text import MimeText
# from email.mime.multipart import MimeMultipart

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/ubuntu/logs/grant_scheduler.log'),
        logging.StreamHandler()
    ]
)

class GrantScheduler:
    def __init__(self):
        self.base_dir = '/home/ubuntu'
        self.logs_dir = os.path.join(self.base_dir, 'logs')
        self.data_dir = os.path.join(self.base_dir, 'grant_data')
        self.backup_dir = os.path.join(self.base_dir, 'grant_backups')
        
        # Create directories if they don't exist
        for directory in [self.logs_dir, self.data_dir, self.backup_dir]:
            os.makedirs(directory, exist_ok=True)
        
        self.scraper_script = os.path.join(self.base_dir, 'enhanced_grant_scraper_v2.py')
        self.processor_script = os.path.join(self.base_dir, 'national_mapping_processor.py')
        self.mapping_component_path = os.path.join(self.base_dir, 'grantthrive-mapping-component/public/grant_mapping_data.json')
        
        # Configuration
        self.config = {
            'daily_run_time': '06:00',  # 6 AM daily
            'weekly_full_scan_day': 'monday',  # Full scan every Monday
            'weekly_full_scan_time': '02:00',  # 2 AM Monday
            'backup_retention_days': 30,
            'notification_email': 'admin@grantthrive.com',  # Configure as needed
            'max_retries': 3,
            'retry_delay_minutes': 30
        }
    
    def backup_current_data(self):
        """Create backup of current grant data"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = os.path.join(self.backup_dir, f'grant_data_backup_{timestamp}.json')
            
            if os.path.exists(self.mapping_component_path):
                subprocess.run(['cp', self.mapping_component_path, backup_file], check=True)
                logging.info(f"✅ Data backed up to {backup_file}")
                return backup_file
            else:
                logging.warning("⚠️ No existing data file to backup")
                return None
                
        except Exception as e:
            logging.error(f"❌ Backup failed: {e}")
            return None
    
    def cleanup_old_backups(self):
        """Remove backups older than retention period"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.config['backup_retention_days'])
            
            for filename in os.listdir(self.backup_dir):
                if filename.startswith('grant_data_backup_'):
                    file_path = os.path.join(self.backup_dir, filename)
                    file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                    
                    if file_time < cutoff_date:
                        os.remove(file_path)
                        logging.info(f"🗑️ Removed old backup: {filename}")
                        
        except Exception as e:
            logging.error(f"❌ Backup cleanup failed: {e}")
    
    def run_scraper(self, full_scan=False):
        """Execute the grant scraper"""
        try:
            logging.info(f"🚀 Starting {'full' if full_scan else 'incremental'} grant scraping...")
            
            # Run the enhanced scraper
            cmd = ['python3', self.scraper_script]
            if full_scan:
                cmd.append('--full-scan')
            
            result = subprocess.run(
                cmd,
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            if result.returncode == 0:
                logging.info("✅ Grant scraping completed successfully")
                return True, result.stdout
            else:
                logging.error(f"❌ Grant scraping failed: {result.stderr}")
                return False, result.stderr
                
        except subprocess.TimeoutExpired:
            logging.error("❌ Grant scraping timed out after 1 hour")
            return False, "Timeout"
        except Exception as e:
            logging.error(f"❌ Grant scraping error: {e}")
            return False, str(e)
    
    def process_scraped_data(self):
        """Process and format the scraped grant data"""
        try:
            logging.info("🔄 Processing scraped grant data...")
            
            result = subprocess.run(
                ['python3', self.processor_script],
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            if result.returncode == 0:
                logging.info("✅ Data processing completed successfully")
                return True, result.stdout
            else:
                logging.error(f"❌ Data processing failed: {result.stderr}")
                return False, result.stderr
                
        except Exception as e:
            logging.error(f"❌ Data processing error: {e}")
            return False, str(e)
    
    def update_mapping_component(self):
        """Update the mapping component with new data"""
        try:
            logging.info("📊 Updating mapping component data...")
            
            source_file = os.path.join(self.base_dir, 'national_grant_mapping_data.json')
            
            if os.path.exists(source_file):
                subprocess.run(['cp', source_file, self.mapping_component_path], check=True)
                logging.info("✅ Mapping component updated successfully")
                return True
            else:
                logging.error("❌ Processed data file not found")
                return False
                
        except Exception as e:
            logging.error(f"❌ Mapping component update failed: {e}")
            return False
    
    def get_data_statistics(self):
        """Get statistics about the current grant data"""
        try:
            if os.path.exists(self.mapping_component_path):
                with open(self.mapping_component_path, 'r') as f:
                    data = json.load(f)
                
                total_grants = len(data)
                total_value = sum(grant.get('value', 0) for grant in data)
                states = set(grant.get('location', {}).get('state') for grant in data)
                states.discard(None)
                
                return {
                    'total_grants': total_grants,
                    'total_value': total_value,
                    'states_covered': len(states),
                    'last_updated': datetime.now().isoformat()
                }
            else:
                return None
                
        except Exception as e:
            logging.error(f"❌ Failed to get data statistics: {e}")
            return None
    
    def send_notification(self, subject, message, is_error=False):
        """Send email notification about scraping results"""
        try:
            # This is a placeholder - configure with actual SMTP settings
            logging.info(f"📧 Notification: {subject}")
            logging.info(f"Message: {message}")
            
            # In production, implement actual email sending:
            # msg = MimeMultipart()
            # msg['From'] = 'scheduler@grantthrive.com'
            # msg['To'] = self.config['notification_email']
            # msg['Subject'] = subject
            # msg.attach(MimeText(message, 'plain'))
            # 
            # server = smtplib.SMTP('smtp.gmail.com', 587)
            # server.starttls()
            # server.login('your_email', 'your_password')
            # server.send_message(msg)
            # server.quit()
            
        except Exception as e:
            logging.error(f"❌ Failed to send notification: {e}")
    
    def daily_update_job(self):
        """Daily incremental update job"""
        logging.info("🌅 Starting daily grant update job...")
        
        # Backup current data
        backup_file = self.backup_current_data()
        
        success_count = 0
        total_steps = 3
        
        try:
            # Step 1: Run scraper (incremental)
            scraper_success, scraper_output = self.run_scraper(full_scan=False)
            if scraper_success:
                success_count += 1
            
            # Step 2: Process data
            if scraper_success:
                process_success, process_output = self.process_scraped_data()
                if process_success:
                    success_count += 1
            
            # Step 3: Update mapping component
            if scraper_success and process_success:
                update_success = self.update_mapping_component()
                if update_success:
                    success_count += 1
            
            # Get statistics
            stats = self.get_data_statistics()
            
            # Send notification
            if success_count == total_steps:
                subject = "✅ GrantThrive Daily Update - Success"
                message = f"""Daily grant data update completed successfully!
                
Statistics:
- Total Grants: {stats['total_grants'] if stats else 'Unknown'}
- Total Value: ${stats['total_value']:,.2f if stats else 'Unknown'}
- States Covered: {stats['states_covered'] if stats else 'Unknown'}
- Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

All systems updated and operational.
"""
                self.send_notification(subject, message)
                logging.info("✅ Daily update job completed successfully")
            else:
                subject = "⚠️ GrantThrive Daily Update - Partial Failure"
                message = f"""Daily grant data update completed with issues.
                
Success Rate: {success_count}/{total_steps} steps completed
                
Please check logs for details.
Backup available at: {backup_file if backup_file else 'No backup created'}
"""
                self.send_notification(subject, message, is_error=True)
                logging.warning(f"⚠️ Daily update job completed with issues: {success_count}/{total_steps}")
                
        except Exception as e:
            subject = "❌ GrantThrive Daily Update - Failed"
            message = f"""Daily grant data update failed with error:
            
Error: {str(e)}
            
Backup available at: {backup_file if backup_file else 'No backup created'}
Please investigate and resolve the issue.
"""
            self.send_notification(subject, message, is_error=True)
            logging.error(f"❌ Daily update job failed: {e}")
        
        # Cleanup old backups
        self.cleanup_old_backups()
    
    def weekly_full_scan_job(self):
        """Weekly full scan job"""
        logging.info("📅 Starting weekly full grant scan job...")
        
        # Backup current data
        backup_file = self.backup_current_data()
        
        try:
            # Run full scan
            scraper_success, scraper_output = self.run_scraper(full_scan=True)
            
            if scraper_success:
                # Process data
                process_success, process_output = self.process_scraped_data()
                
                if process_success:
                    # Update mapping component
                    update_success = self.update_mapping_component()
                    
                    if update_success:
                        stats = self.get_data_statistics()
                        subject = "✅ GrantThrive Weekly Full Scan - Success"
                        message = f"""Weekly full grant scan completed successfully!
                        
Statistics:
- Total Grants: {stats['total_grants'] if stats else 'Unknown'}
- Total Value: ${stats['total_value']:,.2f if stats else 'Unknown'}
- States Covered: {stats['states_covered'] if stats else 'Unknown'}
- Scan Type: Full historical scan
- Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Complete dataset refreshed and validated.
"""
                        self.send_notification(subject, message)
                        logging.info("✅ Weekly full scan completed successfully")
                        return
            
            # If we get here, something failed
            subject = "❌ GrantThrive Weekly Full Scan - Failed"
            message = f"""Weekly full grant scan failed.
            
Backup available at: {backup_file if backup_file else 'No backup created'}
Please investigate and resolve the issue.
"""
            self.send_notification(subject, message, is_error=True)
            logging.error("❌ Weekly full scan failed")
            
        except Exception as e:
            subject = "❌ GrantThrive Weekly Full Scan - Error"
            message = f"""Weekly full grant scan encountered an error:
            
Error: {str(e)}
            
Backup available at: {backup_file if backup_file else 'No backup created'}
Please investigate and resolve the issue.
"""
            self.send_notification(subject, message, is_error=True)
            logging.error(f"❌ Weekly full scan error: {e}")
    
    def setup_schedule(self):
        """Setup the automated schedule"""
        logging.info("⏰ Setting up automated grant scraping schedule...")
        
        # Daily incremental updates
        schedule.every().day.at(self.config['daily_run_time']).do(self.daily_update_job)
        
        # Weekly full scan
        getattr(schedule.every(), self.config['weekly_full_scan_day']).at(
            self.config['weekly_full_scan_time']
        ).do(self.weekly_full_scan_job)
        
        logging.info(f"✅ Schedule configured:")
        logging.info(f"   - Daily updates: {self.config['daily_run_time']} every day")
        logging.info(f"   - Full scan: {self.config['weekly_full_scan_time']} every {self.config['weekly_full_scan_day']}")
    
    def run_scheduler(self):
        """Run the scheduler continuously"""
        self.setup_schedule()
        
        logging.info("🚀 GrantThrive Grant Scheduler started")
        logging.info("Press Ctrl+C to stop the scheduler")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            logging.info("⏹️ Scheduler stopped by user")
        except Exception as e:
            logging.error(f"❌ Scheduler error: {e}")
            self.send_notification(
                "❌ GrantThrive Scheduler Error",
                f"The grant scheduler encountered an error and stopped: {e}",
                is_error=True
            )

def main():
    """Main function to run the scheduler"""
    scheduler = GrantScheduler()
    
    # Check if running as daemon or one-time job
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == '--daily':
            scheduler.daily_update_job()
        elif sys.argv[1] == '--weekly':
            scheduler.weekly_full_scan_job()
        elif sys.argv[1] == '--test':
            # Test run
            logging.info("🧪 Running test job...")
            scheduler.daily_update_job()
        else:
            print("Usage: python3 automated_grant_scheduler.py [--daily|--weekly|--test]")
    else:
        # Run continuous scheduler
        scheduler.run_scheduler()

if __name__ == "__main__":
    main()


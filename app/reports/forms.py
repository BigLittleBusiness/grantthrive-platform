from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField, DateField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Optional, ValidationError, Length
from datetime import datetime, timedelta

class ReportFilterForm(FlaskForm):
    """General report filtering form"""
    
    grant_id = SelectField('Grant Program', validators=[Optional()], coerce=int)
    
    date_from = DateField('From Date', validators=[Optional()], 
                         default=lambda: datetime.utcnow() - timedelta(days=365))
    
    date_to = DateField('To Date', validators=[Optional()], 
                       default=lambda: datetime.utcnow())
    
    status = SelectField('Status', validators=[Optional()], choices=[
        ('', 'All Statuses'),
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('reviewed', 'Reviewed'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('returned', 'Returned')
    ])
    
    submit = SubmitField('Apply Filters')
    
    def validate_date_to(self, field):
        """Validate that end date is after start date"""
        if self.date_from.data and field.data and field.data < self.date_from.data:
            raise ValidationError('End date must be after start date.')

class CustomReportForm(FlaskForm):
    """Custom report builder form"""
    
    report_name = StringField('Report Name', validators=[
        DataRequired(),
        Length(min=2, max=100, message='Report name must be between 2 and 100 characters')
    ])
    
    report_type = SelectField('Report Type', validators=[DataRequired()], choices=[
        ('', 'Select Report Type'),
        ('application_summary', 'Application Summary'),
        ('grant_performance', 'Grant Performance'),
        ('financial_analysis', 'Financial Analysis'),
        ('reviewer_analysis', 'Reviewer Analysis'),
        ('trend_analysis', 'Trend Analysis'),
        ('custom_query', 'Custom Query')
    ])
    
    data_sources = SelectField('Data Sources', validators=[DataRequired()], choices=[
        ('', 'Select Data Source'),
        ('applications', 'Applications'),
        ('grants', 'Grant Programs'),
        ('reviews', 'Reviews'),
        ('users', 'Users'),
        ('workflow_actions', 'Workflow Actions'),
        ('all', 'All Data Sources')
    ])
    
    date_range = SelectField('Date Range', validators=[DataRequired()], choices=[
        ('', 'Select Date Range'),
        ('last_30_days', 'Last 30 Days'),
        ('last_90_days', 'Last 90 Days'),
        ('last_6_months', 'Last 6 Months'),
        ('last_year', 'Last Year'),
        ('current_year', 'Current Year'),
        ('custom', 'Custom Range')
    ])
    
    date_from = DateField('Custom From Date', validators=[Optional()])
    
    date_to = DateField('Custom To Date', validators=[Optional()])
    
    grouping = SelectField('Group By', validators=[Optional()], choices=[
        ('', 'No Grouping'),
        ('grant', 'Grant Program'),
        ('status', 'Application Status'),
        ('month', 'Month'),
        ('quarter', 'Quarter'),
        ('year', 'Year'),
        ('reviewer', 'Reviewer'),
        ('organization', 'Organization')
    ])
    
    metrics = SelectField('Metrics to Include', validators=[DataRequired()], choices=[
        ('', 'Select Metrics'),
        ('count', 'Count'),
        ('sum_requested', 'Total Amount Requested'),
        ('sum_approved', 'Total Amount Approved'),
        ('avg_score', 'Average Score'),
        ('processing_time', 'Average Processing Time'),
        ('approval_rate', 'Approval Rate'),
        ('all', 'All Metrics')
    ])
    
    chart_type = SelectField('Chart Type', validators=[Optional()], choices=[
        ('', 'No Chart'),
        ('bar', 'Bar Chart'),
        ('line', 'Line Chart'),
        ('pie', 'Pie Chart'),
        ('area', 'Area Chart'),
        ('scatter', 'Scatter Plot')
    ])
    
    export_format = SelectField('Export Format', validators=[Optional()], choices=[
        ('html', 'HTML'),
        ('pdf', 'PDF'),
        ('csv', 'CSV'),
        ('excel', 'Excel'),
        ('json', 'JSON')
    ])
    
    include_charts = BooleanField('Include Charts in Export', default=True)
    
    schedule_report = BooleanField('Schedule Regular Report')
    
    schedule_frequency = SelectField('Frequency', validators=[Optional()], choices=[
        ('', 'Select Frequency'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly')
    ])
    
    email_recipients = TextAreaField('Email Recipients (one per line)', validators=[Optional()])
    
    submit = SubmitField('Generate Report')
    
    def validate_date_from(self, field):
        """Validate custom date range"""
        if self.date_range.data == 'custom' and not field.data:
            raise ValidationError('Custom from date is required when using custom date range.')
    
    def validate_date_to(self, field):
        """Validate custom date range"""
        if self.date_range.data == 'custom' and not field.data:
            raise ValidationError('Custom to date is required when using custom date range.')
        
        if (self.date_range.data == 'custom' and self.date_from.data and 
            field.data and field.data < self.date_from.data):
            raise ValidationError('End date must be after start date.')
    
    def validate_schedule_frequency(self, field):
        """Validate schedule frequency"""
        if self.schedule_report.data and not field.data:
            raise ValidationError('Frequency is required when scheduling reports.')

class ExportForm(FlaskForm):
    """Data export form"""
    
    export_type = SelectField('Export Type', validators=[DataRequired()], choices=[
        ('', 'Select Export Type'),
        ('applications', 'Applications Data'),
        ('grants', 'Grant Programs Data'),
        ('reviews', 'Reviews Data'),
        ('financial', 'Financial Data'),
        ('users', 'Users Data'),
        ('workflow', 'Workflow Data'),
        ('complete', 'Complete Database Export')
    ])
    
    format = SelectField('Format', validators=[DataRequired()], choices=[
        ('', 'Select Format'),
        ('csv', 'CSV'),
        ('excel', 'Excel'),
        ('json', 'JSON'),
        ('xml', 'XML'),
        ('pdf', 'PDF Report')
    ])
    
    date_from = DateField('From Date', validators=[Optional()])
    
    date_to = DateField('To Date', validators=[Optional()])
    
    grant_filter = SelectField('Grant Program Filter', validators=[Optional()], coerce=int)
    
    status_filter = SelectField('Status Filter', validators=[Optional()], choices=[
        ('', 'All Statuses'),
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('reviewed', 'Reviewed'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('returned', 'Returned')
    ])
    
    include_personal_data = BooleanField('Include Personal Data', 
                                       description='Include applicant personal information (requires admin access)')
    
    include_sensitive_data = BooleanField('Include Sensitive Data',
                                        description='Include review comments and internal notes (requires admin access)')
    
    compress_export = BooleanField('Compress Export File', default=True)
    
    email_export = BooleanField('Email Export File')
    
    email_address = StringField('Email Address', validators=[Optional()])
    
    submit = SubmitField('Export Data')
    
    def validate_email_address(self, field):
        """Validate email address when email export is selected"""
        if self.email_export.data and not field.data:
            raise ValidationError('Email address is required when emailing export.')

class DashboardConfigForm(FlaskForm):
    """Dashboard configuration form"""
    
    dashboard_name = StringField('Dashboard Name', validators=[
        DataRequired(),
        Length(min=2, max=100, message='Dashboard name must be between 2 and 100 characters')
    ])
    
    default_date_range = SelectField('Default Date Range', validators=[DataRequired()], choices=[
        ('last_30_days', 'Last 30 Days'),
        ('last_90_days', 'Last 90 Days'),
        ('last_6_months', 'Last 6 Months'),
        ('last_year', 'Last Year'),
        ('current_year', 'Current Year')
    ])
    
    widgets = SelectField('Dashboard Widgets', validators=[DataRequired()], choices=[
        ('', 'Select Widgets'),
        ('summary_cards', 'Summary Cards'),
        ('application_trends', 'Application Trends'),
        ('financial_overview', 'Financial Overview'),
        ('grant_performance', 'Grant Performance'),
        ('review_analytics', 'Review Analytics'),
        ('status_distribution', 'Status Distribution'),
        ('all', 'All Widgets')
    ])
    
    refresh_interval = SelectField('Auto Refresh Interval', validators=[Optional()], choices=[
        ('', 'No Auto Refresh'),
        ('5', '5 Minutes'),
        ('15', '15 Minutes'),
        ('30', '30 Minutes'),
        ('60', '1 Hour')
    ])
    
    is_default = BooleanField('Set as Default Dashboard')
    
    share_with_team = BooleanField('Share with Team Members')
    
    submit = SubmitField('Save Dashboard Configuration')

class ReportScheduleForm(FlaskForm):
    """Report scheduling form"""
    
    report_name = StringField('Report Name', validators=[
        DataRequired(),
        Length(min=2, max=100, message='Report name must be between 2 and 100 characters')
    ])
    
    report_type = SelectField('Report Type', validators=[DataRequired()], choices=[
        ('', 'Select Report Type'),
        ('dashboard_summary', 'Dashboard Summary'),
        ('grant_performance', 'Grant Performance'),
        ('application_analytics', 'Application Analytics'),
        ('financial_report', 'Financial Report'),
        ('reviewer_performance', 'Reviewer Performance'),
        ('custom', 'Custom Report')
    ])
    
    frequency = SelectField('Frequency', validators=[DataRequired()], choices=[
        ('', 'Select Frequency'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly')
    ])
    
    day_of_week = SelectField('Day of Week (for weekly)', validators=[Optional()], choices=[
        ('', 'Select Day'),
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday')
    ])
    
    day_of_month = SelectField('Day of Month (for monthly)', validators=[Optional()], choices=[
        ('', 'Select Day'),
        ('1', '1st'),
        ('15', '15th'),
        ('last', 'Last Day of Month')
    ])
    
    time_of_day = StringField('Time of Day (HH:MM)', validators=[Optional()],
                             default='09:00')
    
    email_recipients = TextAreaField('Email Recipients (one per line)', validators=[
        DataRequired(),
        Length(min=5, message='At least one email recipient is required')
    ])
    
    include_attachments = BooleanField('Include Report as Attachment', default=True)
    
    attachment_format = SelectField('Attachment Format', validators=[Optional()], choices=[
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV')
    ])
    
    is_active = BooleanField('Active Schedule', default=True)
    
    submit = SubmitField('Schedule Report')
    
    def validate_day_of_week(self, field):
        """Validate day of week for weekly reports"""
        if self.frequency.data == 'weekly' and not field.data:
            raise ValidationError('Day of week is required for weekly reports.')
    
    def validate_day_of_month(self, field):
        """Validate day of month for monthly reports"""
        if self.frequency.data == 'monthly' and not field.data:
            raise ValidationError('Day of month is required for monthly reports.')

class AnalyticsFilterForm(FlaskForm):
    """Advanced analytics filtering form"""
    
    metric = SelectField('Primary Metric', validators=[DataRequired()], choices=[
        ('', 'Select Metric'),
        ('application_count', 'Application Count'),
        ('approval_rate', 'Approval Rate'),
        ('average_score', 'Average Score'),
        ('total_requested', 'Total Amount Requested'),
        ('total_approved', 'Total Amount Approved'),
        ('processing_time', 'Average Processing Time'),
        ('reviewer_efficiency', 'Reviewer Efficiency')
    ])
    
    dimension = SelectField('Group By', validators=[DataRequired()], choices=[
        ('', 'Select Dimension'),
        ('grant', 'Grant Program'),
        ('status', 'Application Status'),
        ('organization_type', 'Organization Type'),
        ('amount_range', 'Amount Range'),
        ('score_range', 'Score Range'),
        ('time_period', 'Time Period'),
        ('reviewer', 'Reviewer')
    ])
    
    time_granularity = SelectField('Time Granularity', validators=[Optional()], choices=[
        ('', 'No Time Grouping'),
        ('day', 'Daily'),
        ('week', 'Weekly'),
        ('month', 'Monthly'),
        ('quarter', 'Quarterly'),
        ('year', 'Yearly')
    ])
    
    comparison_period = SelectField('Compare With', validators=[Optional()], choices=[
        ('', 'No Comparison'),
        ('previous_period', 'Previous Period'),
        ('previous_year', 'Previous Year'),
        ('baseline', 'Baseline Period')
    ])
    
    filters = TextAreaField('Additional Filters (JSON format)', validators=[Optional()],
                           description='Advanced filtering in JSON format')
    
    chart_type = SelectField('Visualization', validators=[DataRequired()], choices=[
        ('bar', 'Bar Chart'),
        ('line', 'Line Chart'),
        ('pie', 'Pie Chart'),
        ('area', 'Area Chart'),
        ('scatter', 'Scatter Plot'),
        ('heatmap', 'Heatmap'),
        ('table', 'Data Table')
    ])
    
    submit = SubmitField('Generate Analytics')

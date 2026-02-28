from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateTimeField, IntegerField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, ValidationError
from datetime import datetime, timedelta
from app.models import Grant

class VotingSessionForm(FlaskForm):
    """Form for creating and editing voting sessions"""
    
    grant_id = SelectField('Grant Program', 
                          coerce=int, 
                          validators=[DataRequired()],
                          choices=[])
    
    title = StringField('Session Title', 
                       validators=[DataRequired(), Length(min=5, max=200)],
                       render_kw={'placeholder': 'e.g., Community Choice Awards 2024'})
    
    description = TextAreaField('Description', 
                               validators=[DataRequired(), Length(min=20, max=1000)],
                               render_kw={'rows': 3, 'placeholder': 'Describe the purpose and goals of this voting session...'})
    
    voting_type = SelectField('Voting Type',
                             choices=[
                                 ('rating', 'Star Rating (1-5 stars)'),
                                 ('approval', 'Approval (Yes/No)'),
                                 ('priority', 'Priority Ranking')
                             ],
                             default='rating',
                             validators=[DataRequired()])
    
    min_vote_value = IntegerField('Minimum Vote Value',
                                 default=1,
                                 validators=[NumberRange(min=0, max=10)])
    
    max_vote_value = IntegerField('Maximum Vote Value',
                                 default=5,
                                 validators=[NumberRange(min=1, max=10)])
    
    voting_weight = IntegerField('Decision Influence (%)',
                                default=20,
                                validators=[NumberRange(min=0, max=100)],
                                render_kw={'step': 5})
    
    starts_at = DateTimeField('Start Date & Time',
                             validators=[DataRequired()],
                             format='%Y-%m-%dT%H:%M')
    
    ends_at = DateTimeField('End Date & Time',
                           validators=[DataRequired()],
                           format='%Y-%m-%dT%H:%M')
    
    allow_comments = BooleanField('Allow Comments', default=True)
    require_registration = BooleanField('Require Registration', default=False)
    
    # Submit buttons
    save_draft = SubmitField('Save as Draft')
    create_and_publish = SubmitField('Create & Publish')
    
    def __init__(self, *args, **kwargs):
        super(VotingSessionForm, self).__init__(*args, **kwargs)
        
        # Populate grant choices
        self.grant_id.choices = [(0, 'Select a grant program...')]
        grants = Grant.query.filter_by(is_published=True).order_by(Grant.title).all()
        for grant in grants:
            self.grant_id.choices.append((grant.id, f"{grant.title} ({grant.category})"))
    
    def validate_grant_id(self, field):
        """Validate that a valid grant is selected"""
        if field.data == 0:
            raise ValidationError('Please select a grant program.')
        
        grant = Grant.query.get(field.data)
        if not grant:
            raise ValidationError('Selected grant program does not exist.')
        
        if not grant.is_published:
            raise ValidationError('Selected grant program is not published.')
    
    def validate_starts_at(self, field):
        """Validate that start date is in the future"""
        if field.data and field.data <= datetime.utcnow():
            raise ValidationError('Start date must be in the future.')
    
    def validate_ends_at(self, field):
        """Validate that end date is after start date"""
        if field.data and self.starts_at.data:
            if field.data <= self.starts_at.data:
                raise ValidationError('End date must be after start date.')
            
            # Check minimum duration (1 day)
            duration = field.data - self.starts_at.data
            if duration < timedelta(days=1):
                raise ValidationError('Voting period must be at least 1 day.')
            
            # Warn about very long periods (90+ days)
            if duration > timedelta(days=90):
                # This is just a warning, not an error
                pass
    
    def validate_max_vote_value(self, field):
        """Validate that max value is greater than min value"""
        if field.data and self.min_vote_value.data:
            if field.data <= self.min_vote_value.data:
                raise ValidationError('Maximum vote value must be greater than minimum value.')


class VoteForm(FlaskForm):
    """Form for submitting votes"""
    
    application_id = IntegerField('Application ID', validators=[DataRequired()])
    vote_value = IntegerField('Vote Value', validators=[DataRequired()])
    comment = TextAreaField('Comment (Optional)', 
                           validators=[Length(max=500)],
                           render_kw={'rows': 3, 'placeholder': 'Share your thoughts about this application...'})
    
    def validate_vote_value(self, field):
        """Validate vote value is within allowed range"""
        # This will be validated against session parameters in the route
        if field.data is None:
            raise ValidationError('Please provide a vote value.')


class VotingSessionSearchForm(FlaskForm):
    """Form for searching and filtering voting sessions"""
    
    search = StringField('Search Sessions',
                        render_kw={'placeholder': 'Search by title, grant, or description...'})
    
    status = SelectField('Status',
                        choices=[
                            ('', 'All Statuses'),
                            ('draft', 'Draft'),
                            ('scheduled', 'Scheduled'),
                            ('open', 'Open'),
                            ('closed', 'Closed'),
                            ('paused', 'Paused')
                        ],
                        default='')
    
    grant_category = SelectField('Grant Category',
                                choices=[
                                    ('', 'All Categories'),
                                    ('Community Development', 'Community Development'),
                                    ('Infrastructure', 'Infrastructure'),
                                    ('Environment', 'Environment'),
                                    ('Arts & Culture', 'Arts & Culture'),
                                    ('Sports & Recreation', 'Sports & Recreation'),
                                    ('Economic Development', 'Economic Development'),
                                    ('Education', 'Education'),
                                    ('Health & Wellbeing', 'Health & Wellbeing'),
                                    ('Youth Programs', 'Youth Programs'),
                                    ('Senior Services', 'Senior Services'),
                                    ('Emergency Services', 'Emergency Services')
                                ],
                                default='')
    
    sort_by = SelectField('Sort By',
                         choices=[
                             ('created_desc', 'Newest First'),
                             ('created_asc', 'Oldest First'),
                             ('title_asc', 'Title A-Z'),
                             ('title_desc', 'Title Z-A'),
                             ('votes_desc', 'Most Votes'),
                             ('votes_asc', 'Least Votes')
                         ],
                         default='created_desc')


class VotingAnalyticsForm(FlaskForm):
    """Form for configuring analytics reports"""
    
    date_range = SelectField('Date Range',
                            choices=[
                                ('7', 'Last 7 days'),
                                ('30', 'Last 30 days'),
                                ('90', 'Last 90 days'),
                                ('365', 'Last year'),
                                ('all', 'All time')
                            ],
                            default='30')
    
    session_status = SelectField('Session Status',
                                choices=[
                                    ('all', 'All Sessions'),
                                    ('open', 'Open Sessions'),
                                    ('closed', 'Closed Sessions'),
                                    ('draft', 'Draft Sessions')
                                ],
                                default='all')
    
    export_format = SelectField('Export Format',
                               choices=[
                                   ('csv', 'CSV'),
                                   ('excel', 'Excel'),
                                   ('json', 'JSON'),
                                   ('pdf', 'PDF Report')
                               ],
                               default='csv')
    
    include_comments = BooleanField('Include Comments', default=True)
    include_voter_details = BooleanField('Include Voter Details', default=False)


class BulkVotingActionForm(FlaskForm):
    """Form for bulk actions on voting sessions"""
    
    action = SelectField('Action',
                        choices=[
                            ('', 'Select action...'),
                            ('publish', 'Publish Sessions'),
                            ('unpublish', 'Unpublish Sessions'),
                            ('activate', 'Activate Sessions'),
                            ('deactivate', 'Deactivate Sessions'),
                            ('delete', 'Delete Sessions')
                        ],
                        validators=[DataRequired()])
    
    session_ids = StringField('Session IDs', validators=[DataRequired()])
    confirm = BooleanField('I confirm this action', validators=[DataRequired()])
    
    def validate_session_ids(self, field):
        """Validate that session IDs are valid integers"""
        try:
            ids = [int(id.strip()) for id in field.data.split(',') if id.strip()]
            if not ids:
                raise ValidationError('Please select at least one session.')
        except ValueError:
            raise ValidationError('Invalid session IDs provided.')


class VotingReminderForm(FlaskForm):
    """Form for sending voting reminders"""
    
    reminder_type = SelectField('Reminder Type',
                               choices=[
                                   ('email', 'Email Notification'),
                                   ('sms', 'SMS Notification'),
                                   ('push', 'Push Notification'),
                                   ('all', 'All Methods')
                               ],
                               default='email',
                               validators=[DataRequired()])
    
    target_audience = SelectField('Target Audience',
                                 choices=[
                                     ('all', 'All Community Members'),
                                     ('registered', 'Registered Users Only'),
                                     ('non_voters', 'Non-Voters Only'),
                                     ('partial_voters', 'Partial Voters Only')
                                 ],
                                 default='non_voters',
                                 validators=[DataRequired()])
    
    custom_message = TextAreaField('Custom Message (Optional)',
                                  validators=[Length(max=500)],
                                  render_kw={'rows': 4, 'placeholder': 'Add a custom message to encourage participation...'})
    
    schedule_time = DateTimeField('Schedule Time (Optional)',
                                 format='%Y-%m-%dT%H:%M',
                                 render_kw={'placeholder': 'Leave blank to send immediately'})
    
    def validate_schedule_time(self, field):
        """Validate that scheduled time is in the future"""
        if field.data and field.data <= datetime.utcnow():
            raise ValidationError('Scheduled time must be in the future.')

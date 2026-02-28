"""
Admin Security Management for Voting System
Tools for administrators to monitor and manage voting security
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import func, desc, and_, or_
from app import db
from app.models import CommunityVote, VotingSession, User
from app.voting.security import security_manager
from app.utils import admin_required
import json

# Create security admin routes
def register_security_routes(voting_bp):
    """Register security management routes with the voting blueprint"""
    
    @voting_bp.route('/admin/security')
    @login_required
    @admin_required
    def security_dashboard():
        """Security monitoring dashboard for administrators"""
        
        # Get security statistics
        total_votes = CommunityVote.query.count()
        flagged_votes = CommunityVote.query.filter(CommunityVote.is_flagged == True).count()
        
        # Recent suspicious activity
        recent_flags = CommunityVote.query.filter(
            CommunityVote.is_flagged == True,
            CommunityVote.flagged_at >= datetime.utcnow() - timedelta(days=7)
        ).order_by(desc(CommunityVote.flagged_at)).limit(20).all()
        
        # IP address analysis
        ip_stats = db.session.query(
            CommunityVote.ip_address,
            func.count(CommunityVote.id).label('vote_count'),
            func.count(func.distinct(CommunityVote.voter_id)).label('unique_users')
        ).group_by(CommunityVote.ip_address).having(
            func.count(CommunityVote.id) > 10
        ).order_by(desc('vote_count')).limit(20).all()
        
        # User voting patterns
        user_stats = db.session.query(
            User.username,
            User.email,
            func.count(CommunityVote.id).label('vote_count'),
            func.max(CommunityVote.created_at).label('last_vote')
        ).join(CommunityVote).group_by(
            User.id, User.username, User.email
        ).having(
            func.count(CommunityVote.id) > 20
        ).order_by(desc('vote_count')).limit(20).all()
        
        stats = {
            'total_votes': total_votes,
            'flagged_votes': flagged_votes,
            'flagged_percentage': (flagged_votes / max(total_votes, 1)) * 100,
            'recent_flags_count': len(recent_flags),
            'high_volume_ips': len(ip_stats),
            'high_volume_users': len(user_stats)
        }
        
        return render_template('voting/security_dashboard.html',
                             stats=stats,
                             recent_flags=recent_flags,
                             ip_stats=ip_stats,
                             user_stats=user_stats,
                             title='Voting Security Dashboard')
    
    @voting_bp.route('/admin/security/session/<int:session_id>')
    @login_required
    @admin_required
    def session_security_report(session_id):
        """Detailed security report for a specific voting session"""
        
        session = VotingSession.query.get_or_404(session_id)
        
        # Generate comprehensive security analytics
        analytics = security_manager.get_voting_analytics(session_id)
        
        # Get flagged votes for this session
        flagged_votes = CommunityVote.query.filter(
            CommunityVote.voting_session_id == session_id,
            CommunityVote.is_flagged == True
        ).all()
        
        # Generate security report
        security_report = security_manager.generate_security_report(session_id)
        
        return render_template('voting/session_security.html',
                             session=session,
                             analytics=analytics,
                             flagged_votes=flagged_votes,
                             security_report=security_report,
                             title=f'Security Report: {session.title}')
    
    @voting_bp.route('/admin/security/vote/<int:vote_id>/review', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def review_flagged_vote(vote_id):
        """Review and take action on a flagged vote"""
        
        vote = CommunityVote.query.get_or_404(vote_id)
        
        if request.method == 'POST':
            action = request.form.get('action')
            admin_notes = request.form.get('admin_notes', '')
            
            if action == 'approve':
                vote.is_flagged = False
                vote.is_verified = True
                vote.admin_reviewed = True
                vote.admin_notes = admin_notes
                vote.reviewed_by = current_user.id
                vote.reviewed_at = datetime.utcnow()
                
                flash('Vote approved and verified.', 'success')
                
            elif action == 'reject':
                vote.is_verified = False
                vote.admin_reviewed = True
                vote.admin_notes = admin_notes
                vote.reviewed_by = current_user.id
                vote.reviewed_at = datetime.utcnow()
                
                flash('Vote rejected and marked as invalid.', 'warning')
                
            elif action == 'investigate':
                vote.flag_severity = 'high'
                vote.admin_notes = admin_notes
                vote.reviewed_by = current_user.id
                vote.reviewed_at = datetime.utcnow()
                
                flash('Vote marked for further investigation.', 'info')
            
            db.session.commit()
            return redirect(url_for('voting.security_dashboard'))
        
        # Get related votes for context
        related_votes = []
        if vote.voter_id:
            related_votes = CommunityVote.query.filter(
                CommunityVote.voter_id == vote.voter_id,
                CommunityVote.id != vote.id
            ).order_by(desc(CommunityVote.created_at)).limit(10).all()
        elif vote.ip_address:
            related_votes = CommunityVote.query.filter(
                CommunityVote.ip_address == vote.ip_address,
                CommunityVote.id != vote.id
            ).order_by(desc(CommunityVote.created_at)).limit(10).all()
        
        return render_template('voting/review_vote.html',
                             vote=vote,
                             related_votes=related_votes,
                             title=f'Review Vote #{vote.id}')
    
    @voting_bp.route('/admin/security/bulk-action', methods=['POST'])
    @login_required
    @admin_required
    def bulk_security_action():
        """Perform bulk actions on flagged votes"""
        
        data = request.get_json()
        vote_ids = data.get('vote_ids', [])
        action = data.get('action')
        
        if not vote_ids or not action:
            return jsonify({'error': 'Missing vote IDs or action'}), 400
        
        votes = CommunityVote.query.filter(CommunityVote.id.in_(vote_ids)).all()
        
        updated_count = 0
        for vote in votes:
            if action == 'approve_all':
                vote.is_flagged = False
                vote.is_verified = True
                vote.admin_reviewed = True
                vote.reviewed_by = current_user.id
                vote.reviewed_at = datetime.utcnow()
                updated_count += 1
                
            elif action == 'reject_all':
                vote.is_verified = False
                vote.admin_reviewed = True
                vote.reviewed_by = current_user.id
                vote.reviewed_at = datetime.utcnow()
                updated_count += 1
                
            elif action == 'unflag_all':
                vote.is_flagged = False
                vote.admin_reviewed = True
                vote.reviewed_by = current_user.id
                vote.reviewed_at = datetime.utcnow()
                updated_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{updated_count} votes updated successfully',
            'updated_count': updated_count
        })
    
    @voting_bp.route('/admin/security/export/<int:session_id>')
    @login_required
    @admin_required
    def export_security_data(session_id):
        """Export security data for a voting session"""
        
        session = VotingSession.query.get_or_404(session_id)
        
        # Get all votes for the session
        votes = CommunityVote.query.filter(
            CommunityVote.voting_session_id == session_id
        ).all()
        
        # Prepare export data
        export_data = []
        for vote in votes:
            export_data.append({
                'vote_id': vote.id,
                'application_id': vote.application_id,
                'voter_id': vote.voter_id,
                'voter_email': vote.voter_email,
                'vote_value': vote.vote_value,
                'ip_address': vote.ip_address,
                'user_agent': vote.user_agent,
                'created_at': vote.created_at.isoformat(),
                'is_flagged': vote.is_flagged,
                'flag_reason': vote.flag_reason,
                'flag_severity': vote.flag_severity,
                'is_verified': vote.is_verified,
                'admin_reviewed': vote.admin_reviewed,
                'fingerprint': vote.fingerprint
            })
        
        # Generate security analytics
        analytics = security_manager.get_voting_analytics(session_id)
        
        response_data = {
            'session_info': {
                'id': session.id,
                'title': session.title,
                'export_date': datetime.utcnow().isoformat(),
                'exported_by': current_user.username
            },
            'security_analytics': analytics,
            'votes': export_data
        }
        
        return jsonify(response_data)
    
    @voting_bp.route('/admin/security/patterns')
    @login_required
    @admin_required
    def suspicious_patterns():
        """Analyze and display suspicious voting patterns"""
        
        # Detect rapid voting patterns
        rapid_voters = db.session.query(
            CommunityVote.voter_id,
            User.username,
            func.count(CommunityVote.id).label('vote_count'),
            func.min(CommunityVote.created_at).label('first_vote'),
            func.max(CommunityVote.created_at).label('last_vote')
        ).join(User, CommunityVote.voter_id == User.id).filter(
            CommunityVote.created_at >= datetime.utcnow() - timedelta(hours=1)
        ).group_by(CommunityVote.voter_id, User.username).having(
            func.count(CommunityVote.id) > 10
        ).all()
        
        # Detect IP clustering
        ip_clusters = db.session.query(
            CommunityVote.ip_address,
            func.count(func.distinct(CommunityVote.voter_id)).label('unique_users'),
            func.count(CommunityVote.id).label('total_votes')
        ).group_by(CommunityVote.ip_address).having(
            and_(
                func.count(func.distinct(CommunityVote.voter_id)) > 5,
                func.count(CommunityVote.id) > 20
            )
        ).order_by(desc('total_votes')).all()
        
        # Detect identical voting patterns
        identical_patterns = []
        # This would require more complex analysis - simplified for now
        
        return render_template('voting/suspicious_patterns.html',
                             rapid_voters=rapid_voters,
                             ip_clusters=ip_clusters,
                             identical_patterns=identical_patterns,
                             title='Suspicious Voting Patterns')
    
    @voting_bp.route('/admin/security/settings', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def security_settings():
        """Configure voting security settings"""
        
        if request.method == 'POST':
            # Update security settings
            settings = {
                'max_votes_per_ip_per_hour': int(request.form.get('max_votes_per_ip_per_hour', 10)),
                'rapid_voting_threshold': int(request.form.get('rapid_voting_threshold', 30)),
                'suspicious_pattern_threshold': float(request.form.get('suspicious_pattern_threshold', 0.8)),
                'auto_flag_enabled': bool(request.form.get('auto_flag_enabled')),
                'require_email_verification': bool(request.form.get('require_email_verification')),
                'block_datacenter_ips': bool(request.form.get('block_datacenter_ips'))
            }
            
            # Update security manager settings
            security_manager.max_votes_per_ip_per_hour = settings['max_votes_per_ip_per_hour']
            security_manager.rapid_voting_threshold = settings['rapid_voting_threshold']
            security_manager.suspicious_pattern_threshold = settings['suspicious_pattern_threshold']
            
            flash('Security settings updated successfully.', 'success')
            return redirect(url_for('voting.security_settings'))
        
        # Get current settings
        current_settings = {
            'max_votes_per_ip_per_hour': security_manager.max_votes_per_ip_per_hour,
            'rapid_voting_threshold': security_manager.rapid_voting_threshold,
            'suspicious_pattern_threshold': security_manager.suspicious_pattern_threshold,
            'auto_flag_enabled': True,  # Default values
            'require_email_verification': False,
            'block_datacenter_ips': True
        }
        
        return render_template('voting/security_settings.html',
                             settings=current_settings,
                             title='Security Settings')


def create_security_templates():
    """Create security management templates"""
    
    # This would create the HTML templates for security management
    # For now, we'll just return the template names that need to be created
    
    templates_needed = [
        'voting/security_dashboard.html',
        'voting/session_security.html', 
        'voting/review_vote.html',
        'voting/suspicious_patterns.html',
        'voting/security_settings.html'
    ]
    
    return templates_needed

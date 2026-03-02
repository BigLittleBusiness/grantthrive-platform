"""
Voting Security and Fraud Prevention System
Comprehensive security measures to ensure voting integrity
"""

import hashlib
import json
from datetime import datetime, timedelta
from flask import request, current_app
from sqlalchemy import func, and_, or_
from app.models import CommunityVote, User, db
import re
from collections import defaultdict
from typing import Dict, List, Tuple, Optional

class VotingSecurityManager:
    """Manages all voting security and fraud prevention measures"""
    
    def __init__(self):
        self.max_votes_per_ip_per_hour = 10
        self.max_votes_per_user_per_session = 1
        self.suspicious_pattern_threshold = 0.8
        self.rapid_voting_threshold = 30  # seconds between votes
        
    def validate_vote_eligibility(self, user_id: int, application_id: int, 
                                 session_id: int, ip_address: str, 
                                 user_agent: str) -> Tuple[bool, str]:
        """
        Comprehensive vote eligibility validation
        Returns (is_eligible, reason_if_not)
        """
        
        # Check 1: User already voted on this application in this session
        existing_vote = CommunityVote.query.filter_by(
            user_id=user_id,
            application_id=application_id,
            voting_session_id=session_id
        ).first()
        
        if existing_vote:
            return False, "You have already voted on this application"
        
        # Check 2: IP address voting limits
        ip_eligible, ip_reason = self._check_ip_limits(ip_address, session_id)
        if not ip_eligible:
            return False, ip_reason
        
        # Check 3: Rapid voting detection
        rapid_eligible, rapid_reason = self._check_rapid_voting(user_id, ip_address)
        if not rapid_eligible:
            return False, rapid_reason
        
        # Check 4: Suspicious pattern detection
        pattern_eligible, pattern_reason = self._check_suspicious_patterns(
            user_id, ip_address, user_agent, session_id
        )
        if not pattern_eligible:
            return False, pattern_reason
        
        # Check 5: User account validation
        user_eligible, user_reason = self._check_user_account(user_id)
        if not user_eligible:
            return False, user_reason
        
        return True, "Vote eligible"
    
    def _check_ip_limits(self, ip_address: str, session_id: int) -> Tuple[bool, str]:
        """Check IP-based voting limits"""
        
        # Count votes from this IP in the last hour
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        recent_votes = CommunityVote.query.filter(
            and_(
                CommunityVote.ip_address == ip_address,
                CommunityVote.created_at >= one_hour_ago,
                CommunityVote.voting_session_id == session_id
            )
        ).count()
        
        if recent_votes >= self.max_votes_per_ip_per_hour:
            return False, f"Too many votes from this IP address. Limit: {self.max_votes_per_ip_per_hour} per hour"
        
        # Check for IP address patterns (e.g., sequential IPs)
        if self._detect_ip_patterns(ip_address, session_id):
            return False, "Suspicious IP address pattern detected"
        
        return True, "IP address eligible"
    
    def _check_rapid_voting(self, user_id: int, ip_address: str) -> Tuple[bool, str]:
        """Check for rapid voting patterns"""
        
        # Check user's last vote time
        last_user_vote = CommunityVote.query.filter_by(user_id=user_id)\
            .order_by(CommunityVote.created_at.desc()).first()
        
        if last_user_vote:
            time_since_last = (datetime.now(timezone.utc) - last_user_vote.created_at).total_seconds()
            if time_since_last < self.rapid_voting_threshold:
                return False, f"Please wait {self.rapid_voting_threshold - int(time_since_last)} seconds before voting again"
        
        # Check IP's last vote time
        last_ip_vote = CommunityVote.query.filter_by(ip_address=ip_address)\
            .order_by(CommunityVote.created_at.desc()).first()
        
        if last_ip_vote:
            time_since_last = (datetime.now(timezone.utc) - last_ip_vote.created_at).total_seconds()
            if time_since_last < 5:  # Stricter limit for IP
                return False, "Voting too rapidly. Please slow down"
        
        return True, "Voting speed acceptable"
    
    def _check_suspicious_patterns(self, user_id: int, ip_address: str, 
                                  user_agent: str, session_id: int) -> Tuple[bool, str]:
        """Detect suspicious voting patterns"""
        
        # Pattern 1: Same user agent from multiple IPs
        same_agent_votes = CommunityVote.query.filter(
            and_(
                CommunityVote.user_agent == user_agent,
                CommunityVote.voting_session_id == session_id,
                CommunityVote.ip_address != ip_address
            )
        ).count()
        
        if same_agent_votes > 5:
            return False, "Suspicious browser pattern detected"
        
        # Pattern 2: Identical voting patterns across users
        if self._detect_identical_voting_patterns(user_id, session_id):
            return False, "Suspicious voting pattern detected"
        
        # Pattern 3: Bot-like behavior detection
        if self._detect_bot_behavior(user_agent, ip_address):
            return False, "Automated voting detected"
        
        return True, "No suspicious patterns detected"
    
    def _check_user_account(self, user_id: int) -> Tuple[bool, str]:
        """Validate user account eligibility"""
        
        user = db.session.get(User, user_id)
        if not user:
            return False, "Invalid user account"
        
        # Check if account is too new (potential fake account)
        account_age = (datetime.now(timezone.utc) - user.created_at).days
        if account_age < 1:
            return False, "Account must be at least 1 day old to vote"
        
        # Check if user has suspicious activity
        if self._check_user_suspicious_activity(user_id):
            return False, "Account flagged for suspicious activity"
        
        return True, "User account eligible"
    
    def _detect_ip_patterns(self, ip_address: str, session_id: int) -> bool:
        """Detect suspicious IP address patterns"""
        
        # Get recent votes from similar IP ranges
        ip_parts = ip_address.split('.')
        if len(ip_parts) != 4:
            return False
        
        # Check for sequential IPs in the same subnet
        base_ip = '.'.join(ip_parts[:3])
        recent_votes = CommunityVote.query.filter(
            and_(
                CommunityVote.ip_address.like(f"{base_ip}.%"),
                CommunityVote.voting_session_id == session_id,
                CommunityVote.created_at >= datetime.now(timezone.utc) - timedelta(hours=1)
            )
        ).all()
        
        # Check for sequential pattern
        ips = [vote.ip_address.split('.')[-1] for vote in recent_votes]
        try:
            ip_numbers = sorted([int(ip) for ip in ips if ip.isdigit()])
            if len(ip_numbers) >= 5:
                # Check if IPs are sequential
                sequential_count = 0
                for i in range(1, len(ip_numbers)):
                    if ip_numbers[i] == ip_numbers[i-1] + 1:
                        sequential_count += 1
                
                if sequential_count >= 4:  # 5 sequential IPs
                    return True
        except ValueError:
            pass
        
        return False
    
    def _detect_identical_voting_patterns(self, user_id: int, session_id: int) -> bool:
        """Detect if user has identical voting patterns to other users"""
        
        # Get this user's votes in the session
        user_votes = CommunityVote.query.filter_by(
            user_id=user_id,
            voting_session_id=session_id
        ).all()
        
        if len(user_votes) < 3:  # Need at least 3 votes to detect pattern
            return False
        
        user_pattern = [(vote.application_id, vote.vote_value) for vote in user_votes]
        
        # Check other users' patterns
        other_users = db.session.query(CommunityVote.user_id).filter(
            and_(
                CommunityVote.voting_session_id == session_id,
                CommunityVote.user_id != user_id
            )
        ).distinct().all()
        
        for other_user_id, in other_users:
            other_votes = CommunityVote.query.filter_by(
                user_id=other_user_id,
                voting_session_id=session_id
            ).all()
            
            other_pattern = [(vote.application_id, vote.vote_value) for vote in other_votes]
            
            # Calculate pattern similarity
            similarity = self._calculate_pattern_similarity(user_pattern, other_pattern)
            if similarity > self.suspicious_pattern_threshold:
                return True
        
        return False
    
    def _detect_bot_behavior(self, user_agent: str, ip_address: str) -> bool:
        """Detect bot-like behavior"""
        
        # Check for common bot user agents
        bot_indicators = [
            'bot', 'crawler', 'spider', 'scraper', 'curl', 'wget',
            'python-requests', 'automated', 'script'
        ]
        
        user_agent_lower = user_agent.lower()
        for indicator in bot_indicators:
            if indicator in user_agent_lower:
                return True
        
        # Check for missing or suspicious user agent
        if not user_agent or len(user_agent) < 10:
            return True
        
        # Check for data center IP ranges (simplified check)
        if self._is_datacenter_ip(ip_address):
            return True
        
        return False
    
    def _check_user_suspicious_activity(self, user_id: int) -> bool:
        """Check if user has suspicious voting activity"""
        
        # Check voting frequency
        recent_votes = CommunityVote.query.filter(
            and_(
                CommunityVote.user_id == user_id,
                CommunityVote.created_at >= datetime.now(timezone.utc) - timedelta(days=1)
            )
        ).count()
        
        if recent_votes > 50:  # More than 50 votes in 24 hours
            return True
        
        # Check for voting on closed sessions
        closed_session_votes = db.session.query(CommunityVote).join(
            'voting_session'
        ).filter(
            and_(
                CommunityVote.user_id == user_id,
                CommunityVote.created_at >= datetime.now(timezone.utc) - timedelta(days=7)
            )
        ).count()
        
        return False
    
    def _calculate_pattern_similarity(self, pattern1: List[Tuple], pattern2: List[Tuple]) -> float:
        """Calculate similarity between two voting patterns"""
        
        if not pattern1 or not pattern2:
            return 0.0
        
        # Convert to sets for comparison
        set1 = set(pattern1)
        set2 = set(pattern2)
        
        # Calculate Jaccard similarity
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def _is_datacenter_ip(self, ip_address: str) -> bool:
        """Check if IP address belongs to a data center (simplified)"""
        
        # This is a simplified check - in production, you'd use a comprehensive database
        datacenter_ranges = [
            '54.', '52.', '34.', '35.',  # AWS
            '104.', '108.', '142.',      # Google Cloud
            '40.', '52.', '13.',         # Azure
            '167.', '165.', '198.'       # Other cloud providers
        ]
        
        for range_prefix in datacenter_ranges:
            if ip_address.startswith(range_prefix):
                return True
        
        return False
    
    def flag_suspicious_vote(self, vote_id: int, reason: str, severity: str = 'medium'):
        """Flag a vote as suspicious for admin review"""
        
        vote = db.session.get(CommunityVote, vote_id)
        if vote:
            vote.is_flagged = True
            vote.flag_reason = reason
            vote.flag_severity = severity
            vote.flagged_at = datetime.now(timezone.utc)
            db.session.commit()
            
            # Log the incident
            current_app.logger.warning(
                f"Vote {vote_id} flagged: {reason} (severity: {severity})"
            )
    
    def get_voting_analytics(self, session_id: int) -> Dict:
        """Get security analytics for a voting session"""
        
        votes = CommunityVote.query.filter_by(voting_session_id=session_id).all()
        
        analytics = {
            'total_votes': len(votes),
            'flagged_votes': len([v for v in votes if v.is_flagged]),
            'unique_ips': len(set(v.ip_address for v in votes)),
            'unique_users': len(set(v.user_id for v in votes)),
            'votes_per_ip': defaultdict(int),
            'votes_per_user': defaultdict(int),
            'suspicious_patterns': [],
            'security_score': 0.0
        }
        
        # Calculate distribution metrics
        for vote in votes:
            analytics['votes_per_ip'][vote.ip_address] += 1
            analytics['votes_per_user'][vote.user_id] += 1
        
        # Identify potential issues
        high_ip_votes = [(ip, count) for ip, count in analytics['votes_per_ip'].items() if count > 5]
        high_user_votes = [(user, count) for user, count in analytics['votes_per_user'].items() if count > 20]
        
        if high_ip_votes:
            analytics['suspicious_patterns'].append(f"High vote count from IPs: {high_ip_votes}")
        
        if high_user_votes:
            analytics['suspicious_patterns'].append(f"High vote count from users: {high_user_votes}")
        
        # Calculate security score (0-100, higher is better)
        flagged_ratio = analytics['flagged_votes'] / max(analytics['total_votes'], 1)
        ip_diversity = analytics['unique_ips'] / max(analytics['total_votes'], 1)
        user_diversity = analytics['unique_users'] / max(analytics['total_votes'], 1)
        
        analytics['security_score'] = max(0, 100 - (flagged_ratio * 50) + (ip_diversity * 25) + (user_diversity * 25))
        
        return analytics
    
    def generate_security_report(self, session_id: int) -> str:
        """Generate a comprehensive security report for a voting session"""
        
        analytics = self.get_voting_analytics(session_id)
        
        report = f"""
VOTING SECURITY REPORT
Session ID: {session_id}
Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}

OVERVIEW:
- Total Votes: {analytics['total_votes']}
- Flagged Votes: {analytics['flagged_votes']} ({analytics['flagged_votes']/max(analytics['total_votes'], 1)*100:.1f}%)
- Unique IP Addresses: {analytics['unique_ips']}
- Unique Users: {analytics['unique_users']}
- Security Score: {analytics['security_score']:.1f}/100

SECURITY ASSESSMENT:
"""
        
        if analytics['security_score'] >= 80:
            report += "✅ EXCELLENT - No significant security concerns detected\n"
        elif analytics['security_score'] >= 60:
            report += "⚠️  GOOD - Minor security concerns, monitoring recommended\n"
        elif analytics['security_score'] >= 40:
            report += "⚠️  MODERATE - Some security issues detected, review recommended\n"
        else:
            report += "🚨 POOR - Significant security concerns, immediate review required\n"
        
        if analytics['suspicious_patterns']:
            report += "\nSUSPICIOUS PATTERNS DETECTED:\n"
            for pattern in analytics['suspicious_patterns']:
                report += f"- {pattern}\n"
        
        return report


# Global security manager instance
security_manager = VotingSecurityManager()


def validate_vote_security(user_id: int, application_id: int, session_id: int) -> Tuple[bool, str]:
    """
    Convenience function to validate vote security
    """
    ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', ''))
    user_agent = request.environ.get('HTTP_USER_AGENT', '')
    
    return security_manager.validate_vote_eligibility(
        user_id, application_id, session_id, ip_address, user_agent
    )


def create_vote_fingerprint(user_id: int, ip_address: str, user_agent: str) -> str:
    """
    Create a unique fingerprint for vote tracking
    """
    fingerprint_data = f"{user_id}:{ip_address}:{user_agent}"
    return hashlib.sha256(fingerprint_data.encode()).hexdigest()


def log_vote_attempt(user_id: int, application_id: int, session_id: int, 
                    success: bool, reason: str = None):
    """
    Log vote attempts for security monitoring
    """
    ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', ''))
    user_agent = request.environ.get('HTTP_USER_AGENT', '')
    
    log_data = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'user_id': user_id,
        'application_id': application_id,
        'session_id': session_id,
        'ip_address': ip_address,
        'user_agent': user_agent,
        'success': success,
        'reason': reason
    }
    
    current_app.logger.info(f"Vote attempt: {json.dumps(log_data)}")

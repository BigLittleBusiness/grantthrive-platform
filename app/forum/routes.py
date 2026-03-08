"""
GrantThrive — Community Forum API
==================================
Endpoints for council staff to create and manage forums, and for
community members to read and post in public forums.

Endpoints:
  GET    /api/forums                      — List forums for current council
  POST   /api/forums                      — Create a forum (staff/admin)
  GET    /api/forums/<id>                 — Get forum detail + posts
  PATCH  /api/forums/<id>                 — Update forum (creator/admin)
  DELETE /api/forums/<id>                 — Deactivate forum (creator/admin)
  POST   /api/forums/<id>/join            — Staff joins a forum
  DELETE /api/forums/<id>/join            — Staff leaves a forum
  POST   /api/forums/<id>/posts           — Post a message
  PATCH  /api/forums/<id>/posts/<post_id> — Edit own post
  DELETE /api/forums/<id>/posts/<post_id> — Delete own post (or admin)
"""

import logging
from datetime import datetime, timezone

from flask import request, jsonify

from app import db
from app.forum import forum_bp
from app.models import Forum, ForumPost, ForumMember, User
from app.auth.routes import token_required

logger = logging.getLogger(__name__)

STAFF_ROLES = {'council_admin', 'council_staff'}
ALL_PORTAL_ROLES = {'council_admin', 'council_staff', 'community_member'}


def _forum_to_dict(forum, current_user=None):
    member_ids = {m.user_id for m in forum.members}
    is_member  = current_user and current_user.id in member_ids
    return {
        'id':          forum.id,
        'title':       forum.title,
        'description': forum.description,
        'is_public':   forum.is_public,
        'is_active':   forum.is_active,
        'created_by':  forum.created_by,
        'creator_name': forum.creator.full_name if forum.creator else None,
        'created_at':  forum.created_at.isoformat(),
        'post_count':  len(forum.posts),
        'member_count': len(forum.members),
        'is_member':   bool(is_member),
    }


def _post_to_dict(post):
    return {
        'id':         post.id,
        'forum_id':   post.forum_id,
        'author_id':  post.author_id,
        'author_name': post.author.full_name if post.author else 'Unknown',
        'author_role': post.author.role if post.author else None,
        'body':       post.body,
        'is_pinned':  post.is_pinned,
        'created_at': post.created_at.isoformat(),
        'updated_at': post.updated_at.isoformat() if post.updated_at else None,
    }


# ── List / create forums ──────────────────────────────────────────────────────

@forum_bp.route('/forums', methods=['GET'])
@token_required
def list_forums(current_user):
    """List all forums for the current user's council."""
    council_id = current_user.council_id
    if not council_id:
        return jsonify({'error': 'No council associated with this account.'}), 400

    role = current_user.role
    q = Forum.query.filter_by(council_id=council_id, is_active=True)

    # Community members only see public forums
    if role == 'community_member':
        q = q.filter_by(is_public=True)

    forums = q.order_by(Forum.created_at.desc()).all()
    return jsonify({
        'forums': [_forum_to_dict(f, current_user) for f in forums],
        'total':  len(forums),
    }), 200


@forum_bp.route('/forums', methods=['POST'])
@token_required
def create_forum(current_user):
    """Create a new forum. Council staff and admin only."""
    if current_user.role not in STAFF_ROLES:
        return jsonify({'error': 'Only council staff can create forums.'}), 403

    council_id = current_user.council_id
    if not council_id:
        return jsonify({'error': 'No council associated with this account.'}), 400

    data        = request.get_json(silent=True) or {}
    title       = (data.get('title') or '').strip()
    description = (data.get('description') or '').strip() or None
    is_public   = bool(data.get('is_public', True))

    if not title:
        return jsonify({'error': 'Forum title is required.'}), 400
    if len(title) > 200:
        return jsonify({'error': 'Title must be 200 characters or fewer.'}), 400

    forum = Forum(
        council_id  = council_id,
        title       = title,
        description = description,
        is_public   = is_public,
        created_by  = current_user.id,
    )
    db.session.add(forum)
    db.session.flush()

    # Creator automatically becomes a member
    member = ForumMember(forum_id=forum.id, user_id=current_user.id)
    db.session.add(member)
    db.session.commit()

    logger.info("Forum created: id=%d title=%r by user_id=%d", forum.id, title, current_user.id)
    return jsonify({'forum': _forum_to_dict(forum, current_user)}), 201


# ── Single forum ──────────────────────────────────────────────────────────────

@forum_bp.route('/forums/<int:forum_id>', methods=['GET'])
@token_required
def get_forum(current_user, forum_id):
    """Get forum details and all posts."""
    forum = db.session.get(Forum, forum_id)
    if not forum or forum.council_id != current_user.council_id:
        return jsonify({'error': 'Forum not found.'}), 404
    if not forum.is_active:
        return jsonify({'error': 'This forum has been closed.'}), 410
    if not forum.is_public and current_user.role == 'community_member':
        return jsonify({'error': 'This forum is not public.'}), 403

    return jsonify({
        'forum': _forum_to_dict(forum, current_user),
        'posts': [_post_to_dict(p) for p in forum.posts],
    }), 200


@forum_bp.route('/forums/<int:forum_id>', methods=['PATCH'])
@token_required
def update_forum(current_user, forum_id):
    """Update a forum. Creator or council_admin only."""
    forum = db.session.get(Forum, forum_id)
    if not forum or forum.council_id != current_user.council_id:
        return jsonify({'error': 'Forum not found.'}), 404

    is_creator = forum.created_by == current_user.id
    is_admin   = current_user.role == 'council_admin'
    if not is_creator and not is_admin:
        return jsonify({'error': 'Only the forum creator or an admin can edit this forum.'}), 403

    data = request.get_json(silent=True) or {}
    if 'title' in data:
        t = data['title'].strip()
        if not t:
            return jsonify({'error': 'Title cannot be empty.'}), 400
        forum.title = t
    if 'description' in data:
        forum.description = (data['description'] or '').strip() or None
    if 'is_public' in data:
        forum.is_public = bool(data['is_public'])
    if 'is_active' in data and is_admin:
        forum.is_active = bool(data['is_active'])

    forum.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify({'forum': _forum_to_dict(forum, current_user)}), 200


@forum_bp.route('/forums/<int:forum_id>', methods=['DELETE'])
@token_required
def deactivate_forum(current_user, forum_id):
    """Soft-delete (deactivate) a forum. Creator or council_admin only."""
    forum = db.session.get(Forum, forum_id)
    if not forum or forum.council_id != current_user.council_id:
        return jsonify({'error': 'Forum not found.'}), 404

    is_creator = forum.created_by == current_user.id
    is_admin   = current_user.role == 'council_admin'
    if not is_creator and not is_admin:
        return jsonify({'error': 'Only the forum creator or an admin can close this forum.'}), 403

    forum.is_active  = False
    forum.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify({'message': 'Forum closed.'}), 200


# ── Join / leave ──────────────────────────────────────────────────────────────

@forum_bp.route('/forums/<int:forum_id>/join', methods=['POST'])
@token_required
def join_forum(current_user, forum_id):
    """Staff member joins a forum."""
    if current_user.role not in STAFF_ROLES:
        return jsonify({'error': 'Only council staff can join forums.'}), 403

    forum = db.session.get(Forum, forum_id)
    if not forum or forum.council_id != current_user.council_id or not forum.is_active:
        return jsonify({'error': 'Forum not found.'}), 404

    existing = ForumMember.query.filter_by(
        forum_id=forum_id, user_id=current_user.id
    ).first()
    if existing:
        return jsonify({'message': 'Already a member.'}), 200

    member = ForumMember(forum_id=forum_id, user_id=current_user.id)
    db.session.add(member)
    db.session.commit()
    return jsonify({'message': f'Joined forum "{forum.title}".'}), 200


@forum_bp.route('/forums/<int:forum_id>/join', methods=['DELETE'])
@token_required
def leave_forum(current_user, forum_id):
    """Staff member leaves a forum."""
    member = ForumMember.query.filter_by(
        forum_id=forum_id, user_id=current_user.id
    ).first()
    if not member:
        return jsonify({'error': 'You are not a member of this forum.'}), 404

    db.session.delete(member)
    db.session.commit()
    return jsonify({'message': 'Left forum.'}), 200


# ── Posts ─────────────────────────────────────────────────────────────────────

@forum_bp.route('/forums/<int:forum_id>/posts', methods=['POST'])
@token_required
def create_post(current_user, forum_id):
    """Post a message in a forum."""
    forum = db.session.get(Forum, forum_id)
    if not forum or forum.council_id != current_user.council_id or not forum.is_active:
        return jsonify({'error': 'Forum not found.'}), 404
    if not forum.is_public and current_user.role == 'community_member':
        return jsonify({'error': 'This forum is not public.'}), 403

    data = request.get_json(silent=True) or {}
    body = (data.get('body') or '').strip()
    if not body:
        return jsonify({'error': 'Message body is required.'}), 400
    if len(body) > 5000:
        return jsonify({'error': 'Message must be 5,000 characters or fewer.'}), 400

    is_pinned = bool(data.get('is_pinned', False)) and current_user.role in STAFF_ROLES

    post = ForumPost(
        forum_id  = forum_id,
        author_id = current_user.id,
        body      = body,
        is_pinned = is_pinned,
    )
    db.session.add(post)
    db.session.commit()
    return jsonify({'post': _post_to_dict(post)}), 201


@forum_bp.route('/forums/<int:forum_id>/posts/<int:post_id>', methods=['PATCH'])
@token_required
def update_post(current_user, forum_id, post_id):
    """Edit a post. Author or council_admin only."""
    post = db.session.get(ForumPost, post_id)
    if not post or post.forum_id != forum_id:
        return jsonify({'error': 'Post not found.'}), 404

    is_author = post.author_id == current_user.id
    is_admin  = current_user.role == 'council_admin'
    if not is_author and not is_admin:
        return jsonify({'error': 'You can only edit your own posts.'}), 403

    data = request.get_json(silent=True) or {}
    if 'body' in data:
        body = (data['body'] or '').strip()
        if not body:
            return jsonify({'error': 'Message body cannot be empty.'}), 400
        post.body       = body
        post.updated_at = datetime.now(timezone.utc)
    if 'is_pinned' in data and is_admin:
        post.is_pinned = bool(data['is_pinned'])

    db.session.commit()
    return jsonify({'post': _post_to_dict(post)}), 200


@forum_bp.route('/forums/<int:forum_id>/posts/<int:post_id>', methods=['DELETE'])
@token_required
def delete_post(current_user, forum_id, post_id):
    """Delete a post. Author or council_admin only."""
    post = db.session.get(ForumPost, post_id)
    if not post or post.forum_id != forum_id:
        return jsonify({'error': 'Post not found.'}), 404

    is_author = post.author_id == current_user.id
    is_admin  = current_user.role == 'council_admin'
    if not is_author and not is_admin:
        return jsonify({'error': 'You can only delete your own posts.'}), 403

    db.session.delete(post)
    db.session.commit()
    return jsonify({'message': 'Post deleted.'}), 200

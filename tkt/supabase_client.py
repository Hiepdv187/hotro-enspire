"""
Supabase client configuration for notifications storage.
Replaces Redis for storing offline notifications.
Uses Supabase REST API for real-time notifications management.
"""
import os
from supabase import create_client, Client

# Supabase configuration from environment variables
SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '')

_supabase_client: Client = None


def get_supabase_client() -> Client:
    """Get or create Supabase client singleton."""
    global _supabase_client
    if _supabase_client is None and SUPABASE_URL and SUPABASE_KEY:
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase_client


# ============================================
# Online Users Management (replaces Redis set)
# ============================================

def add_online_user(user_id: int) -> bool:
    """Add user to online users list."""
    client = get_supabase_client()
    if not client:
        return False
    try:
        client.table('online_users').upsert({
            'user_id': user_id
        }, on_conflict='user_id').execute()
        return True
    except Exception as e:
        print(f"Error adding online user: {e}")
        return False


def remove_online_user(user_id: int) -> bool:
    """Remove user from online users list."""
    client = get_supabase_client()
    if not client:
        return False
    try:
        client.table('online_users').delete().eq('user_id', user_id).execute()
        return True
    except Exception as e:
        print(f"Error removing online user: {e}")
        return False


def is_user_online(user_id: int) -> bool:
    """Check if user is online."""
    client = get_supabase_client()
    if not client:
        return False
    try:
        result = client.table('online_users').select('user_id').eq('user_id', user_id).execute()
        return len(result.data) > 0
    except Exception as e:
        print(f"Error checking online user: {e}")
        return False


# ============================================
# Pending Notifications (replaces Redis list)
# ============================================

def store_pending_notification(user_id: int, notification_data: dict) -> bool:
    """Store a pending notification for offline user."""
    client = get_supabase_client()
    if not client:
        return False
    try:
        client.table('pending_notifications').insert({
            'user_id': user_id,
            'notification_id': notification_data.get('id'),
            'message': notification_data.get('message', ''),
            'read': notification_data.get('read', False),
            'timestamp': notification_data.get('timestamp'),
        }).execute()
        return True
    except Exception as e:
        print(f"Error storing pending notification: {e}")
        return False


def get_pending_notifications(user_id: int) -> list:
    """Get all pending notifications for a user."""
    client = get_supabase_client()
    if not client:
        return []
    try:
        result = client.table('pending_notifications').select('*').eq('user_id', user_id).order('created_at', desc=True).execute()
        return result.data
    except Exception as e:
        print(f"Error getting pending notifications: {e}")
        return []


def clear_pending_notifications(user_id: int) -> bool:
    """Clear all pending notifications for a user after they've been sent."""
    client = get_supabase_client()
    if not client:
        return False
    try:
        client.table('pending_notifications').delete().eq('user_id', user_id).execute()
        return True
    except Exception as e:
        print(f"Error clearing pending notifications: {e}")
        return False


# ============================================
# Unread Count Cache
# ============================================

def set_unread_count(user_id: int, count: int) -> bool:
    """Set unread notification count for a user."""
    client = get_supabase_client()
    if not client:
        return False
    try:
        client.table('notification_counts').upsert({
            'user_id': user_id,
            'unread_count': count
        }, on_conflict='user_id').execute()
        return True
    except Exception as e:
        print(f"Error setting unread count: {e}")
        return False


def get_unread_count(user_id: int) -> int:
    """Get unread notification count for a user."""
    client = get_supabase_client()
    if not client:
        return 0
    try:
        result = client.table('notification_counts').select('unread_count').eq('user_id', user_id).execute()
        if result.data:
            return result.data[0].get('unread_count', 0)
        return 0
    except Exception as e:
        print(f"Error getting unread count: {e}")
        return 0

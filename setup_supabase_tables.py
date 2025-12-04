"""
Script to automatically create Supabase tables for notifications system.
Run this script once to setup the database schema.

Usage:
    python setup_supabase_tables.py
"""

import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

# SQL queries to create tables
CREATE_TABLES_SQL = """
-- 1. Online Users Table
CREATE TABLE IF NOT EXISTS public.online_users (
    user_id INTEGER PRIMARY KEY,
    connected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_online_users_user_id ON public.online_users(user_id);

-- 2. Pending Notifications Table
CREATE TABLE IF NOT EXISTS public.pending_notifications (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    notification_id INTEGER,
    message TEXT NOT NULL,
    read BOOLEAN DEFAULT FALSE,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pending_notifications_user_id ON public.pending_notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_pending_notifications_created_at ON public.pending_notifications(created_at DESC);

-- 3. Notification Counts Table
CREATE TABLE IF NOT EXISTS public.notification_counts (
    user_id INTEGER PRIMARY KEY,
    unread_count INTEGER DEFAULT 0,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_notification_counts_user_id ON public.notification_counts(user_id);
"""


def setup_tables():
    """Create required tables in Supabase."""
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Error: SUPABASE_URL and SUPABASE_KEY must be set in .env file")
        print("\nAdd these to your .env file:")
        print("SUPABASE_URL=https://your-project.supabase.co")
        print("SUPABASE_KEY=your-anon-key")
        return False
    
    try:
        print("🔄 Connecting to Supabase...")
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        print("🔄 Creating tables...")
        
        # Note: Supabase Python client doesn't support direct SQL execution
        # You need to run the SQL in Supabase SQL Editor
        
        print("\n" + "="*60)
        print("⚠️  MANUAL SETUP REQUIRED")
        print("="*60)
        print("\nThe Supabase Python client doesn't support direct SQL execution.")
        print("Please follow these steps:\n")
        print("1. Go to https://app.supabase.com")
        print("2. Select your project")
        print("3. Go to SQL Editor")
        print("4. Create a new query")
        print("5. Copy and paste the content from 'supabase_setup.sql'")
        print("6. Click 'Run' to execute\n")
        print("="*60)
        
        # Test connection by trying to query a table
        print("\n🔄 Testing connection...")
        try:
            # Try to query online_users table
            result = client.table('online_users').select('*').limit(1).execute()
            print("✅ Table 'online_users' exists and is accessible")
            
            result = client.table('pending_notifications').select('*').limit(1).execute()
            print("✅ Table 'pending_notifications' exists and is accessible")
            
            result = client.table('notification_counts').select('*').limit(1).execute()
            print("✅ Table 'notification_counts' exists and is accessible")
            
            print("\n✅ All tables are set up correctly!")
            return True
            
        except Exception as e:
            error_msg = str(e)
            if "Could not find the table" in error_msg or "relation" in error_msg:
                print("\n❌ Tables not found. Please create them using the SQL script.")
                print("\nSee SUPABASE_SETUP.md for detailed instructions.")
            else:
                print(f"\n❌ Error testing tables: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def verify_setup():
    """Verify that all tables exist and are accessible."""
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Error: SUPABASE_URL and SUPABASE_KEY not configured")
        return False
    
    try:
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        tables = ['online_users', 'pending_notifications', 'notification_counts']
        all_exist = True
        
        print("\n🔍 Verifying tables...")
        for table in tables:
            try:
                client.table(table).select('*').limit(1).execute()
                print(f"  ✅ {table}")
            except Exception as e:
                print(f"  ❌ {table} - {str(e)[:50]}...")
                all_exist = False
        
        if all_exist:
            print("\n✅ All tables verified successfully!")
            return True
        else:
            print("\n❌ Some tables are missing. Please run the SQL setup script.")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying setup: {e}")
        return False


def test_operations():
    """Test basic operations on the tables."""
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Error: SUPABASE_URL and SUPABASE_KEY not configured")
        return False
    
    try:
        from tkt.supabase_client import (
            add_online_user,
            is_user_online,
            remove_online_user,
            store_pending_notification,
            get_pending_notifications,
            clear_pending_notifications,
            set_unread_count,
            get_unread_count
        )
        
        test_user_id = 99999  # Use a test user ID
        
        print("\n🧪 Testing operations...")
        
        # Test online users
        print("\n1. Testing online users...")
        add_online_user(test_user_id)
        if is_user_online(test_user_id):
            print("  ✅ Add/check online user works")
        else:
            print("  ❌ Online user check failed")
            return False
        
        remove_online_user(test_user_id)
        if not is_user_online(test_user_id):
            print("  ✅ Remove online user works")
        else:
            print("  ❌ Remove online user failed")
            return False
        
        # Test pending notifications
        print("\n2. Testing pending notifications...")
        test_notification = {
            'id': 12345,
            'message': 'Test notification',
            'read': False,
            'timestamp': '2024-12-04T12:00:00'
        }
        
        store_pending_notification(test_user_id, test_notification)
        notifications = get_pending_notifications(test_user_id)
        
        if len(notifications) > 0:
            print("  ✅ Store/get pending notifications works")
        else:
            print("  ❌ Pending notifications failed")
            return False
        
        clear_pending_notifications(test_user_id)
        notifications = get_pending_notifications(test_user_id)
        
        if len(notifications) == 0:
            print("  ✅ Clear pending notifications works")
        else:
            print("  ❌ Clear pending notifications failed")
            return False
        
        # Test notification counts
        print("\n3. Testing notification counts...")
        set_unread_count(test_user_id, 5)
        count = get_unread_count(test_user_id)
        
        if count == 5:
            print("  ✅ Set/get unread count works")
        else:
            print(f"  ❌ Unread count failed (expected 5, got {count})")
            return False
        
        # Cleanup
        set_unread_count(test_user_id, 0)
        
        print("\n✅ All operations tested successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error testing operations: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("="*60)
    print("Supabase Tables Setup Script")
    print("="*60)
    
    # Step 1: Setup (show instructions)
    setup_tables()
    
    # Step 2: Verify
    print("\n" + "="*60)
    if verify_setup():
        # Step 3: Test operations
        print("\n" + "="*60)
        test_operations()
    
    print("\n" + "="*60)
    print("Setup complete!")
    print("="*60)

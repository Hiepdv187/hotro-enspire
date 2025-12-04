-- ============================================
-- SIMPLE Supabase Setup (No RLS)
-- ============================================
-- Copy and paste this ENTIRE script into Supabase SQL Editor

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

-- Disable RLS for easier access
ALTER TABLE public.online_users DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.pending_notifications DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.notification_counts DISABLE ROW LEVEL SECURITY;

-- Grant full access
GRANT ALL ON public.online_users TO anon, authenticated;
GRANT ALL ON public.pending_notifications TO anon, authenticated;
GRANT ALL ON public.notification_counts TO anon, authenticated;
GRANT USAGE, SELECT ON SEQUENCE public.pending_notifications_id_seq TO anon, authenticated;

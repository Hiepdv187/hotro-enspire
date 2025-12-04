-- ============================================
-- Supabase Database Setup for Notifications
-- ============================================
-- Run this SQL in Supabase SQL Editor to create required tables

-- 1. Online Users Table
-- Tracks which users are currently connected via WebSocket
CREATE TABLE IF NOT EXISTS public.online_users (
    user_id INTEGER PRIMARY KEY,
    connected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_online_users_user_id ON public.online_users(user_id);

-- 2. Pending Notifications Table
-- Stores notifications for offline users
CREATE TABLE IF NOT EXISTS public.pending_notifications (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    notification_id INTEGER,
    message TEXT NOT NULL,
    read BOOLEAN DEFAULT FALSE,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_pending_notifications_user_id ON public.pending_notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_pending_notifications_created_at ON public.pending_notifications(created_at DESC);

-- 3. Notification Counts Table
-- Caches unread notification counts per user
CREATE TABLE IF NOT EXISTS public.notification_counts (
    user_id INTEGER PRIMARY KEY,
    unread_count INTEGER DEFAULT 0,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_notification_counts_user_id ON public.notification_counts(user_id);

-- ============================================
-- Enable Row Level Security (RLS) - Optional
-- ============================================

-- Enable RLS on tables
ALTER TABLE public.online_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.pending_notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notification_counts ENABLE ROW LEVEL SECURITY;

-- Create policies (adjust based on your authentication setup)
-- These policies allow authenticated users to access their own data

-- Online Users Policies
CREATE POLICY "Users can view their own online status"
    ON public.online_users FOR SELECT
    USING (auth.uid()::text::integer = user_id);

CREATE POLICY "Users can update their own online status"
    ON public.online_users FOR ALL
    USING (auth.uid()::text::integer = user_id);

-- Pending Notifications Policies
CREATE POLICY "Users can view their own pending notifications"
    ON public.pending_notifications FOR SELECT
    USING (auth.uid()::text::integer = user_id);

CREATE POLICY "System can manage pending notifications"
    ON public.pending_notifications FOR ALL
    USING (true);

-- Notification Counts Policies
CREATE POLICY "Users can view their own notification count"
    ON public.notification_counts FOR SELECT
    USING (auth.uid()::text::integer = user_id);

CREATE POLICY "System can manage notification counts"
    ON public.notification_counts FOR ALL
    USING (true);

-- ============================================
-- Functions for automatic timestamp updates
-- ============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for automatic timestamp updates
CREATE TRIGGER update_online_users_updated_at
    BEFORE UPDATE ON public.online_users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_notification_counts_updated_at
    BEFORE UPDATE ON public.notification_counts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- Cleanup old data (optional)
-- ============================================

-- Function to cleanup old pending notifications (older than 7 days)
CREATE OR REPLACE FUNCTION cleanup_old_pending_notifications()
RETURNS void AS $$
BEGIN
    DELETE FROM public.pending_notifications
    WHERE created_at < NOW() - INTERVAL '7 days';
END;
$$ LANGUAGE plpgsql;

-- You can schedule this function to run periodically using pg_cron extension
-- Or call it manually when needed

-- ============================================
-- Grant permissions (if needed)
-- ============================================

-- Grant permissions to authenticated users
GRANT SELECT, INSERT, UPDATE, DELETE ON public.online_users TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.pending_notifications TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.notification_counts TO authenticated;

-- Grant usage on sequences
GRANT USAGE, SELECT ON SEQUENCE public.pending_notifications_id_seq TO authenticated;

-- ============================================
-- Verification Queries
-- ============================================

-- Run these to verify tables were created successfully
-- SELECT * FROM public.online_users;
-- SELECT * FROM public.pending_notifications;
-- SELECT * FROM public.notification_counts;

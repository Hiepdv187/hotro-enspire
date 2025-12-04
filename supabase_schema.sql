-- ===========================================
-- SUPABASE SCHEMA FOR NOTIFICATIONS SYSTEM
-- ===========================================
-- Run this SQL in Supabase Dashboard > SQL Editor

-- Table: online_users
-- Tracks which users are currently online (connected via WebSocket)
CREATE TABLE IF NOT EXISTS online_users (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast lookup
CREATE INDEX IF NOT EXISTS idx_online_users_user_id ON online_users(user_id);

-- Table: pending_notifications
-- Stores notifications for users who are offline
CREATE TABLE IF NOT EXISTS pending_notifications (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    notification_id INTEGER,
    message TEXT NOT NULL,
    read BOOLEAN DEFAULT FALSE,
    timestamp TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast lookup by user_id
CREATE INDEX IF NOT EXISTS idx_pending_notifications_user_id ON pending_notifications(user_id);

-- Table: notification_counts
-- Caches unread notification count per user
CREATE TABLE IF NOT EXISTS notification_counts (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE,
    unread_count INTEGER DEFAULT 0,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast lookup
CREATE INDEX IF NOT EXISTS idx_notification_counts_user_id ON notification_counts(user_id);

-- Table: notifications_archive
-- Stores all notifications with auto-cleanup for read ones older than 1 week
CREATE TABLE IF NOT EXISTS notifications_archive (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    message TEXT NOT NULL,
    read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast lookup and cleanup
CREATE INDEX IF NOT EXISTS idx_notifications_archive_user_id ON notifications_archive(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_archive_read_created ON notifications_archive(read, created_at);

-- ===========================================
-- AUTO-CLEANUP FUNCTIONS
-- ===========================================

-- Function: Cleanup read notifications older than 1 week
CREATE OR REPLACE FUNCTION cleanup_old_read_notifications()
RETURNS void AS $$
BEGIN
    DELETE FROM notifications_archive WHERE read = TRUE AND created_at < NOW() - INTERVAL '7 days';
    DELETE FROM pending_notifications WHERE created_at < NOW() - INTERVAL '7 days';
END;
$$ LANGUAGE plpgsql;

-- Function: Cleanup stale online_users entries (older than 1 hour)
CREATE OR REPLACE FUNCTION cleanup_stale_online_users()
RETURNS void AS $$
BEGIN
    DELETE FROM online_users WHERE created_at < NOW() - INTERVAL '1 hour';
END;
$$ LANGUAGE plpgsql;

-- ===========================================
-- SCHEDULED JOBS (using pg_cron extension)
-- ===========================================
-- Supabase Pro plan supports pg_cron. Run these commands:

-- Enable pg_cron extension
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Schedule cleanup of read notifications every day at 3:00 AM UTC
SELECT cron.schedule('cleanup-old-notifications', '0 3 * * *', 'SELECT cleanup_old_read_notifications()');

-- Schedule cleanup of stale online users every hour
SELECT cron.schedule('cleanup-stale-users', '0 * * * *', 'SELECT cleanup_stale_online_users()');

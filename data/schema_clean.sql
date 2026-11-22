-- ==============================================================================
-- AUTOPILOT Production Clean Database Schema (SQLite / PostgreSQL Compatible)
-- Clean Environment Bootstrap File — Contains ZERO credentials or user rows.
-- ==============================================================================

-- Multi-Tenant Organizations
CREATE TABLE IF NOT EXISTS organizations (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    billing_email TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Multi-Tenant Workspaces
CREATE TABLE IF NOT EXISTS workspaces (
    id TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    slug TEXT NOT NULL,
    autopilot_mode TEXT DEFAULT 'assisted',
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Credit Accounts
CREATE TABLE IF NOT EXISTS credit_accounts (
    id TEXT PRIMARY KEY,
    organization_id TEXT UNIQUE NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    balance INTEGER DEFAULT 1000,
    lifetime_purchased INTEGER DEFAULT 1000,
    lifetime_used INTEGER DEFAULT 0,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Usage & Cost Ledger
CREATE TABLE IF NOT EXISTS usage_ledger (
    id TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    workspace_id TEXT,
    operation_type TEXT NOT NULL,
    units_consumed REAL NOT NULL,
    raw_cost_usd REAL NOT NULL,
    credits_debited INTEGER NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Video Processing Jobs
CREATE TABLE IF NOT EXISTS video_jobs (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL,
    video_id TEXT NOT NULL,
    job_type TEXT DEFAULT 'render_full',
    status TEXT DEFAULT 'queued',
    priority INTEGER DEFAULT 50,
    progress INTEGER DEFAULT 0,
    current_step TEXT,
    error_message TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Connected Social Media Accounts (Instagram, TikTok, Twitter)
CREATE TABLE IF NOT EXISTS platform_accounts (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    platform TEXT NOT NULL,
    external_account_id TEXT NOT NULL,
    username TEXT,
    display_name TEXT,
    profile_image_url TEXT,
    account_type TEXT DEFAULT 'BUSINESS',
    status TEXT DEFAULT 'connected',
    encrypted_access_token TEXT NOT NULL,
    token_expires_at TEXT,
    scopes TEXT,
    metadata_json TEXT DEFAULT '{}',
    last_synced_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- YouTube Channel OAuth Credentials (Encrypted via SecretVault AES-256-GCM)
CREATE TABLE IF NOT EXISTS channel_credentials (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id TEXT,
    platform TEXT NOT NULL,
    channel_name TEXT,
    channel_id TEXT,
    encrypted_token TEXT NOT NULL,
    token_expiry TEXT,
    is_active INTEGER DEFAULT 1,
    last_verified_at TEXT,
    scopes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Videos
CREATE TABLE IF NOT EXISTS videos (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id TEXT,
    title TEXT NOT NULL,
    description TEXT,
    tags TEXT,
    status TEXT DEFAULT 'draft',
    duration_sec REAL DEFAULT 0.0,
    video_url TEXT,
    yt_video_id TEXT,
    series_id TEXT,
    episode_num INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Episodic Series Franchises
CREATE TABLE IF NOT EXISTS series (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id TEXT,
    title TEXT NOT NULL,
    description TEXT,
    genre TEXT DEFAULT 'mystery',
    tone TEXT DEFAULT 'suspense',
    cast_json TEXT DEFAULT '{}',
    episode_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'active',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Series Episodes
CREATE TABLE IF NOT EXISTS episodes (
    id TEXT PRIMARY KEY,
    series_id TEXT NOT NULL REFERENCES series(id) ON DELETE CASCADE,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id TEXT,
    episode_num INTEGER NOT NULL,
    title TEXT NOT NULL,
    script_json TEXT,
    audio_path TEXT,
    video_path TEXT,
    yt_video_id TEXT,
    status TEXT DEFAULT 'draft',
    duration_sec REAL DEFAULT 0.0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Multi-Tenant Users
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    user_id TEXT UNIQUE,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    name TEXT,
    role TEXT DEFAULT 'user',
    tier TEXT DEFAULT 'starter',
    credits INTEGER DEFAULT 100,
    is_onboarded INTEGER DEFAULT 0,
    tour_completed INTEGER DEFAULT 0,
    preferences_json TEXT DEFAULT '{}',
    status TEXT DEFAULT 'active',
    block_reason TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    created_ts TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Activity Log
CREATE TABLE IF NOT EXISTS activity_log (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    action TEXT NOT NULL,
    details_json TEXT DEFAULT '{}',
    ip_address TEXT,
    user_agent TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Audit Log (Administrative Actions & Security Events)
CREATE TABLE IF NOT EXISTS audit_log (
    id TEXT PRIMARY KEY,
    actor_id TEXT NOT NULL,
    action TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_id TEXT NOT NULL,
    changes_json TEXT DEFAULT '{}',
    ip_address TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- System Notifications
CREATE TABLE IF NOT EXISTS notifications (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    type TEXT DEFAULT 'info',
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    link TEXT,
    read INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Ideas Repository
CREATE TABLE IF NOT EXISTS ideas (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    topic TEXT NOT NULL,
    hook TEXT,
    score REAL DEFAULT 0.0,
    status TEXT DEFAULT 'new',
    created_ts TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Scripts Repository
CREATE TABLE IF NOT EXISTS scripts (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    idea_id TEXT,
    title TEXT NOT NULL,
    content_json TEXT NOT NULL,
    status TEXT DEFAULT 'draft',
    created_ts TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Engine Background Jobs
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    task_type TEXT NOT NULL,
    status TEXT DEFAULT 'queued',
    error TEXT,
    result_json TEXT DEFAULT '{}',
    created_ts TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_ts TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indices for Fast Multi-Tenant Lookups
CREATE INDEX IF NOT EXISTS idx_workspaces_org ON workspaces(organization_id);
CREATE INDEX IF NOT EXISTS idx_videos_ws ON videos(workspace_id);
CREATE INDEX IF NOT EXISTS idx_videos_yt ON videos(yt_video_id);
CREATE INDEX IF NOT EXISTS idx_series_ws ON series(workspace_id);
CREATE INDEX IF NOT EXISTS idx_episodes_series ON episodes(series_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_platform_accounts_ws ON platform_accounts(workspace_id);
CREATE INDEX IF NOT EXISTS idx_channel_credentials_ws ON channel_credentials(workspace_id);
CREATE INDEX IF NOT EXISTS idx_activity_log_user ON activity_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_actor ON audit_log(actor_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id);

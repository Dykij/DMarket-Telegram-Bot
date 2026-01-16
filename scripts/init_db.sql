-- Initialize database for DMarket Bot
-- This script is automatically run when the PostgreSQL container starts

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS bot;
CREATE SCHEMA IF NOT EXISTS analytics;

-- Users table
CREATE TABLE IF NOT EXISTS bot.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    language_code VARCHAR(10) DEFAULT 'en',
    is_active BOOLEAN DEFAULT true,
    is_admin BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User settings
CREATE TABLE IF NOT EXISTS bot.user_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES bot.users(id) ON DELETE CASCADE,
    notifications_enabled BOOLEAN DEFAULT true,
    price_alerts_enabled BOOLEAN DEFAULT true,
    language VARCHAR(10) DEFAULT 'en',
    timezone VARCHAR(50) DEFAULT 'UTC',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Market data cache
CREATE TABLE IF NOT EXISTS analytics.market_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_id VARCHAR(255) NOT NULL,
    game VARCHAR(100) NOT NULL,
    item_name TEXT NOT NULL,
    price_usd DECIMAL(10, 4) NOT NULL,
    price_change_24h DECIMAL(5, 2),
    volume_24h INTEGER,
    market_cap DECIMAL(15, 4),
    data_source VARCHAR(50) DEFAULT 'dmarket',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(item_id, created_at::date)
);

-- Price alerts
CREATE TABLE IF NOT EXISTS bot.price_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES bot.users(id) ON DELETE CASCADE,
    item_id VARCHAR(255) NOT NULL,
    target_price DECIMAL(10, 4) NOT NULL,
    condition VARCHAR(10) NOT NULL CHECK (condition IN ('above', 'below')),
    is_active BOOLEAN DEFAULT true,
    triggered_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Bot commands log
CREATE TABLE IF NOT EXISTS bot.command_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES bot.users(id) ON DELETE SET NULL,
    command VARCHAR(100) NOT NULL,
    parameters JSONB,
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    execution_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Analytics events
CREATE TABLE IF NOT EXISTS analytics.events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES bot.users(id) ON DELETE SET NULL,
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB,
    session_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON bot.users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_users_active ON bot.users(is_active);
CREATE INDEX IF NOT EXISTS idx_market_data_item_date ON analytics.market_data(item_id, created_at::date);
CREATE INDEX IF NOT EXISTS idx_price_alerts_user_active ON bot.price_alerts(user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_command_log_user_time ON bot.command_log(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_events_type_time ON analytics.events(event_type, created_at);

-- Create functions for updating timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers
CREATE OR REPLACE TRIGGER update_users_updated_at
    BEFORE UPDATE ON bot.users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE OR REPLACE TRIGGER update_user_settings_updated_at
    BEFORE UPDATE ON bot.user_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create n8n database and user
-- n8n requires its own database for workflow and execution data
CREATE DATABASE n8n OWNER postgres;
CREATE USER n8n_user WITH ENCRYPTED PASSWORD 'n8n_password';
GRANT ALL PRIVILEGES ON DATABASE n8n TO n8n_user;
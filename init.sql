-- KPI Insight Bot Database Initialization Script

-- Create database and user if not exists
CREATE DATABASE IF NOT EXISTS kpi_bot;
CREATE USER IF NOT EXISTS 'kpi_user'@'%' IDENTIFIED BY 'kpi_password';
GRANT ALL PRIVILEGES ON kpi_bot.* TO 'kpi_user'@'%';
FLUSH PRIVILEGES;

-- Use the database
USE kpi_bot;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(255) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    role ENUM('admin', 'analyst', 'viewer') NOT NULL DEFAULT 'viewer',
    subscription_tier ENUM('basic', 'advanced', 'enterprise') NOT NULL DEFAULT 'basic',
    password_hash VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    is_active BOOLEAN DEFAULT TRUE,
    INDEX idx_email (email),
    INDEX idx_role (role),
    INDEX idx_subscription_tier (subscription_tier)
);

-- Chat sessions table
CREATE TABLE IF NOT EXISTS chat_sessions (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_last_activity (last_activity)
);

-- KPI queries table
CREATE TABLE IF NOT EXISTS kpi_queries (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255),
    query_text TEXT NOT NULL,
    intent VARCHAR(255),
    kpi_id VARCHAR(255),
    filters JSON,
    time_range JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processing_time DECIMAL(10,3),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_session_id (session_id),
    INDEX idx_created_at (created_at)
);

-- KPI results table
CREATE TABLE IF NOT EXISTS kpi_results (
    id VARCHAR(255) PRIMARY KEY,
    query_id VARCHAR(255) NOT NULL,
    kpi_id VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    value DECIMAL(20,4) NOT NULL,
    unit VARCHAR(50),
    currency VARCHAR(10),
    time_period VARCHAR(50),
    calculation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    variance_py DECIMAL(20,4),
    variance_plan DECIMAL(20,4),
    variance_fx_neutral DECIMAL(20,4),
    drill_down_url TEXT,
    metadata JSON,
    FOREIGN KEY (query_id) REFERENCES kpi_queries(id) ON DELETE CASCADE,
    INDEX idx_query_id (query_id),
    INDEX idx_kpi_id (kpi_id),
    INDEX idx_calculation_date (calculation_date)
);

-- Alert rules table
CREATE TABLE IF NOT EXISTS alert_rules (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    kpi_id VARCHAR(255) NOT NULL,
    alert_type ENUM('threshold', 'anomaly', 'trend') NOT NULL,
    threshold_value DECIMAL(20,4),
    comparison_operator VARCHAR(20),
    notification_channels JSON,
    is_active BOOLEAN DEFAULT TRUE,
    created_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_triggered TIMESTAMP NULL,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_kpi_id (kpi_id),
    INDEX idx_alert_type (alert_type),
    INDEX idx_is_active (is_active)
);

-- Alert instances table
CREATE TABLE IF NOT EXISTS alert_instances (
    id VARCHAR(255) PRIMARY KEY,
    rule_id VARCHAR(255) NOT NULL,
    kpi_id VARCHAR(255) NOT NULL,
    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    value DECIMAL(20,4) NOT NULL,
    threshold_value DECIMAL(20,4),
    severity ENUM('low', 'medium', 'high', 'critical') NOT NULL,
    message TEXT NOT NULL,
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by VARCHAR(255),
    acknowledged_at TIMESTAMP NULL,
    FOREIGN KEY (rule_id) REFERENCES alert_rules(id) ON DELETE CASCADE,
    FOREIGN KEY (acknowledged_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_rule_id (rule_id),
    INDEX idx_kpi_id (kpi_id),
    INDEX idx_triggered_at (triggered_at),
    INDEX idx_severity (severity),
    INDEX idx_acknowledged (acknowledged)
);

-- Audit logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(255) NOT NULL,
    details JSON,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_action (action),
    INDEX idx_resource_type (resource_type),
    INDEX idx_created_at (created_at)
);

-- Oracle connections table
CREATE TABLE IF NOT EXISTS oracle_connections (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    connection_type VARCHAR(50) NOT NULL,
    host VARCHAR(255) NOT NULL,
    port INT NOT NULL,
    service_name VARCHAR(100) NOT NULL,
    username VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_tested TIMESTAMP NULL,
    test_status VARCHAR(50),
    INDEX idx_connection_type (connection_type),
    INDEX idx_is_active (is_active)
);

-- Create default admin user
INSERT INTO users (id, email, name, role, subscription_tier, password_hash, created_at, is_active)
VALUES (
    'admin-001',
    'admin@company.com',
    'System Administrator',
    'admin',
    'enterprise',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBdXybJkRwOHJu', -- password: admin123
    NOW(),
    TRUE
) ON DUPLICATE KEY UPDATE email = email;

-- Create default analyst user
INSERT INTO users (id, email, name, role, subscription_tier, password_hash, created_at, is_active)
VALUES (
    'analyst-001',
    'analyst@company.com',
    'Financial Analyst',
    'analyst',
    'advanced',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBdXybJkRwOHJu', -- password: analyst123
    NOW(),
    TRUE
) ON DUPLICATE KEY UPDATE email = email;

-- Create performance monitoring views
CREATE OR REPLACE VIEW query_performance_stats AS
SELECT 
    DATE(created_at) as date,
    COUNT(*) as total_queries,
    AVG(processing_time) as avg_processing_time,
    MAX(processing_time) as max_processing_time,
    MIN(processing_time) as min_processing_time
FROM kpi_queries 
WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY DATE(created_at)
ORDER BY date DESC;

CREATE OR REPLACE VIEW user_activity_stats AS
SELECT 
    u.id,
    u.email,
    u.name,
    u.role,
    COUNT(q.id) as total_queries,
    MAX(q.created_at) as last_query_time,
    AVG(q.processing_time) as avg_processing_time
FROM users u
LEFT JOIN kpi_queries q ON u.id = q.user_id
WHERE u.is_active = TRUE
GROUP BY u.id, u.email, u.name, u.role;

CREATE OR REPLACE VIEW alert_summary AS
SELECT 
    DATE(triggered_at) as date,
    severity,
    COUNT(*) as count,
    SUM(CASE WHEN acknowledged = TRUE THEN 1 ELSE 0 END) as acknowledged_count
FROM alert_instances
WHERE triggered_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY DATE(triggered_at), severity
ORDER BY date DESC, severity;
-- Drop all tables if they exist
DROP TABLE IF EXISTS assessment_results;
DROP TABLE IF EXISTS period_dates;
DROP TABLE IF EXISTS symptom_logs;
DROP TABLE IF EXISTS users;

-- Recreate database
CREATE DATABASE IF NOT EXISTS defaultdb;
USE defaultdb;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    date_of_birth DATE,
    mobile_number VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Create symptom_logs table
CREATE TABLE IF NOT EXISTS symptom_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    selected_date DATE NOT NULL,
    had_period VARCHAR(10) DEFAULT 'No',
    cycle_phase VARCHAR(50) DEFAULT 'Follicular',
    symptoms_selected TEXT,
    other_symptom TEXT,
    mood_state VARCHAR(50),
    cramps BOOLEAN DEFAULT 0,
    fatigue BOOLEAN DEFAULT 0,
    nausea BOOLEAN DEFAULT 0,
    mood_swings BOOLEAN DEFAULT 0,
    acne BOOLEAN DEFAULT 0,
    back_pain BOOLEAN DEFAULT 0,
    flow_intensity INT DEFAULT 2,
    pain_level INT DEFAULT 2,
    cluster_result TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id, selected_date)
);

-- Create period_dates table
CREATE TABLE IF NOT EXISTS period_dates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    period_date DATE NOT NULL,
    period_length_days INT DEFAULT 5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id, period_date)
);

-- Create assessment_results table
CREATE TABLE IF NOT EXISTS assessment_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    assessment_type VARCHAR(100) NOT NULL,
    risk_percentage DECIMAL(5,2),
    risk_level VARCHAR(50),
    risk_factors TEXT,
    assessment_summary TEXT,
    recommendations TEXT,
    assessment_data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Verify tables created
SHOW TABLES;
DESCRIBE users;

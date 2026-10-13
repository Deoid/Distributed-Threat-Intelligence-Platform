-- Database initialization script for Threat Intelligence Platform

CREATE TABLE IF NOT EXISTS threat_events (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    source_ip VARCHAR(45) NOT NULL,
    honeypot_type VARCHAR(50) NOT NULL,
    protocol VARCHAR(20) NOT NULL,
    destination_port INTEGER NOT NULL,
    username VARCHAR(100),
    password VARCHAR(100),
    raw_payload TEXT,
    country VARCHAR(100) DEFAULT 'Unknown',
    country_code VARCHAR(10) DEFAULT 'XX',
    city VARCHAR(100) DEFAULT 'Unknown',
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    asn VARCHAR(100) DEFAULT 'Unknown',
    isp VARCHAR(150) DEFAULT 'Unknown',
    threat_score INTEGER DEFAULT 0,
    enriched BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ip_profiles (
    ip VARCHAR(45) PRIMARY KEY,
    total_events INTEGER DEFAULT 0,
    first_seen TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    targeted_ports_count INTEGER DEFAULT 0,
    targeted_ports_list TEXT,
    usernames_tried_count INTEGER DEFAULT 0,
    request_rate DOUBLE PRECISION DEFAULT 0.0,
    threat_score INTEGER DEFAULT 0,
    country VARCHAR(100) DEFAULT 'Unknown',
    country_code VARCHAR(10) DEFAULT 'XX',
    asn VARCHAR(100) DEFAULT 'Unknown',
    cluster_label INTEGER DEFAULT -1,
    cluster_name VARCHAR(100) DEFAULT 'Unassigned',
    is_blocked BOOLEAN DEFAULT FALSE,
    block_reason VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS blocklist (
    id SERIAL PRIMARY KEY,
    ip VARCHAR(45) UNIQUE NOT NULL,
    reason VARCHAR(255) NOT NULL,
    threat_score INTEGER NOT NULL,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    cluster_profile VARCHAR(100)
);

CREATE INDEX IF NOT EXISTS idx_events_timestamp ON threat_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_events_source_ip ON threat_events(source_ip);
CREATE INDEX IF NOT EXISTS idx_events_country ON threat_events(country_code);
CREATE INDEX IF NOT EXISTS idx_events_port ON threat_events(destination_port);
CREATE INDEX IF NOT EXISTS idx_events_enriched ON threat_events(enriched);
CREATE INDEX IF NOT EXISTS idx_profiles_score ON ip_profiles(threat_score DESC);

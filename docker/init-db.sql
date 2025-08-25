-- PostgreSQL initialization script
-- This runs when the database container is first created

-- Create database if not exists
SELECT 'CREATE DATABASE exam_portal'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'exam_portal')\gexec

-- Connect to the database
\c exam_portal;

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Create read-only user for backups
DO
$do$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles
      WHERE  rolname = 'exam_portal_readonly') THEN
      CREATE ROLE exam_portal_readonly LOGIN PASSWORD 'readonly_password_change_this';
   END IF;
END
$do$;

-- Grant permissions
GRANT CONNECT ON DATABASE exam_portal TO exam_portal_readonly;
GRANT USAGE ON SCHEMA public TO exam_portal_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO exam_portal_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO exam_portal_readonly;

-- Performance optimizations
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '7864kB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;
ALTER SYSTEM SET work_mem = '1310kB';
ALTER SYSTEM SET min_wal_size = '1GB';
ALTER SYSTEM SET max_wal_size = '4GB';
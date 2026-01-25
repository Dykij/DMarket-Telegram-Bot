#!/bin/sh
# ============================================================================
# PostgreSQL Initialization Script for DMarket Bot Development
# ============================================================================
# Creates additional databases and users for development environment
# ============================================================================

set -e

echo "Initializing PostgreSQL for DMarket Bot..."

# ============================================================================
# CREATE ADDITIONAL DATABASES
# ============================================================================

# Create test database
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<EOSQL
    -- Create test database for pytest
    CREATE DATABASE test_db;

    -- Create n8n database (for workflow automation)
    CREATE DATABASE n8n;
    CREATE USER n8n_user WITH ENCRYPTED PASSWORD 'n8n_password';
    GRANT ALL PRIVILEGES ON DATABASE n8n TO n8n_user;

    -- Grant permissions on test database
    GRANT ALL PRIVILEGES ON DATABASE test_db TO $POSTGRES_USER;

    -- Create extensions
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    CREATE EXTENSION IF NOT EXISTS "pg_trgm";

    -- Display success message
    SELECT 'DMarket Bot databases initialized successfully!' AS status;
EOSQL

echo "PostgreSQL initialization complete!"
echo "   - Database: $POSTGRES_DB"
echo "   - Test DB:  test_db"
echo "   - n8n DB:   n8n"

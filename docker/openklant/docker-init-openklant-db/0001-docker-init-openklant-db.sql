CREATE USER openklant;
CREATE DATABASE openklant;
GRANT ALL PRIVILEGES ON DATABASE openklant TO openklant;
-- On Postgres 15+, connect to the database and grant schema permissions.
-- GRANT USAGE, CREATE ON SCHEMA public TO openklant;

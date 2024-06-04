CREATE USER open_inwoner;
CREATE DATABASE open_inwoner;
GRANT ALL PRIVILEGES ON DATABASE open_inwoner TO open_inwoner;
\c open_inwoner;
CREATE EXTENSION postgis;
-- On Postgres 15+, connect to the database and grant schema permissions.
-- GRANT USAGE, CREATE ON SCHEMA public TO openforms;
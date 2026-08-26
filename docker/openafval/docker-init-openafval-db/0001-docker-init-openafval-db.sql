CREATE USER openafval;
CREATE DATABASE openafval;
GRANT ALL PRIVILEGES ON DATABASE openafval TO openafval;

-- Unlike this repo's other satellites, which default to Postgres 14 via the
-- postgis/postgis image, this one defaults to plain postgres:17 (see
-- docker-compose.openafval.yml) -- and Postgres 15+ restricts CREATE on the
-- public schema to the schema owner by default, so this grant (commented out
-- as a no-op hint in the other services' init scripts) actually has to run
-- here. `\connect` first: it needs to apply to the openafval database, not
-- whatever database this script's own connection defaults to.
\connect openafval
GRANT USAGE, CREATE ON SCHEMA public TO openafval;

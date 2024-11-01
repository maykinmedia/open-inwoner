-- create user + database 'open_inwoner' if they don't already exist
DO
$$
begin
    IF NOT EXISTS (SELECT * FROM pg_user WHERE usename = 'open_inwoner') THEN
        CREATE role open_inwoner WITH login;
    END IF;

    IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'open_inwoner') THEN
        CREATE EXTENSION IF NOT EXISTS dblink;
        PERFORM dblink_exec('dbname=' || current_database(), 'CREATE DATABASE open_inwoner');
    END IF;
END
$$
;

GRANT ALL PRIVILEGES ON DATABASE open_inwoner TO open_inwoner;

\c open_inwoner;
GRANT USAGE, CREATE ON SCHEMA public TO open_inwoner;

CREATE EXTENSION postgis;

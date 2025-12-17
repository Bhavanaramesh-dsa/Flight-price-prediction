-- Create airflow DB only if it doesn't exist
\connect postgres
SELECT 'CREATE DATABASE airflow WITH OWNER = postgres TEMPLATE template0 ENCODING ''UTF8'';'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'airflow')
\gexec

-- Create predictions DB only if it doesn't exist
SELECT 'CREATE DATABASE predictions WITH OWNER = postgres TEMPLATE template0 ENCODING ''UTF8'';'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'predictions')
\gexec
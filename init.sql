-- Example SQL commands to initialize the database
CREATE TABLE IF NOT EXISTS devices (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    status VARCHAR(50) NOT NULL,
    last_checked TIMESTAMP
);

CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    device_id INTEGER REFERENCES devices(id),
    event_type VARCHAR(50) NOT NULL,
    description TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE USER root WITH PASSWORD 'root';
GRANT ALL PRIVILEGES ON DATABASE monitoring_db TO root;
ALTER USER root WITH SUPERUSER;
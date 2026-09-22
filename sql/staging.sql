-- ============================================================
-- STAGING TABLE
-- Urban City Service Request
-- ============================================================

CREATE SCHEMA IF NOT EXISTS staging;


CREATE TABLE IF NOT EXISTS staging.urban_city_requests (

    request_id BIGINT,

    created_date TIMESTAMP,

    closed_date TIMESTAMP,

    agency VARCHAR(100),

    status VARCHAR(50),

    problem TEXT,

    problem_detail TEXT,

    location_type VARCHAR(100),

    incident_address TEXT,

    city VARCHAR(100),

    borough VARCHAR(100),

    latitude DOUBLE PRECISION,

    longitude DOUBLE PRECISION
);
-- ============================================================
-- URBAN CITY SERVICE REQUEST
-- GOLD LAYER - STAR SCHEMA
-- ============================================================
--
-- Grain of fact table:
-- One row = one urban service request
--
-- Source:
-- Silver layer
--
-- Consumers:
-- PostgreSQL / Power BI
-- ============================================================


-- ============================================================
-- 1. CREATE GOLD SCHEMA
-- ============================================================

CREATE SCHEMA IF NOT EXISTS gold;


-- ============================================================
-- 2. DATE DIMENSION
-- ============================================================

CREATE TABLE IF NOT EXISTS gold.dim_date (

    date_key INTEGER PRIMARY KEY,

    full_date DATE NOT NULL UNIQUE,

    year INTEGER NOT NULL,

    quarter INTEGER NOT NULL,

    month INTEGER NOT NULL,

    month_name VARCHAR(20) NOT NULL,

    day INTEGER NOT NULL,

    day_of_week INTEGER NOT NULL,

    day_name VARCHAR(20) NOT NULL
);


-- ============================================================
-- 3. AGENCY DIMENSION
-- ============================================================

CREATE TABLE IF NOT EXISTS gold.dim_agency (

    agency_key SERIAL PRIMARY KEY,

    agency_name VARCHAR(100) NOT NULL UNIQUE
);


-- ============================================================
-- 4. PROBLEM DIMENSION
-- ============================================================

CREATE TABLE IF NOT EXISTS gold.dim_problem (

    problem_key SERIAL PRIMARY KEY,

    problem VARCHAR(255) NOT NULL,

    problem_detail TEXT
);


-- ============================================================
-- 5. LOCATION DIMENSION
-- ============================================================

CREATE TABLE IF NOT EXISTS gold.dim_location (

    location_key SERIAL PRIMARY KEY,

    location_type VARCHAR(100),

    incident_address TEXT,

    city VARCHAR(100),

    borough VARCHAR(100),

    latitude DOUBLE PRECISION,

    longitude DOUBLE PRECISION
);


-- ============================================================
-- 6. SERVICE REQUEST FACT TABLE
-- ============================================================

CREATE TABLE IF NOT EXISTS gold.fact_service_request (

    -- Business key
    request_id BIGINT PRIMARY KEY,


    -- Date dimension keys
    created_date_key INTEGER NOT NULL,

    closed_date_key INTEGER,


    -- Dimension foreign keys
    agency_key INTEGER,

    problem_key INTEGER,

    location_key INTEGER,


    -- Request status
    status VARCHAR(50) NOT NULL,


    -- Measures / derived attributes
    resolution_hours DOUBLE PRECISION,

    is_closed BOOLEAN NOT NULL,


    -- ========================================================
    -- Foreign keys
    -- ========================================================

    CONSTRAINT fk_fact_created_date

        FOREIGN KEY (created_date_key)

        REFERENCES gold.dim_date(date_key),


    CONSTRAINT fk_fact_closed_date

        FOREIGN KEY (closed_date_key)

        REFERENCES gold.dim_date(date_key),


    CONSTRAINT fk_fact_agency

        FOREIGN KEY (agency_key)

        REFERENCES gold.dim_agency(agency_key),


    CONSTRAINT fk_fact_problem

        FOREIGN KEY (problem_key)

        REFERENCES gold.dim_problem(problem_key),


    CONSTRAINT fk_fact_location

        FOREIGN KEY (location_key)

        REFERENCES gold.dim_location(location_key)
);


-- ============================================================
-- 7. INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_fact_service_request_created_date

ON gold.fact_service_request(created_date_key);


CREATE INDEX IF NOT EXISTS idx_fact_service_request_closed_date

ON gold.fact_service_request(closed_date_key);


CREATE INDEX IF NOT EXISTS idx_fact_service_request_agency

ON gold.fact_service_request(agency_key);


CREATE INDEX IF NOT EXISTS idx_fact_service_request_problem

ON gold.fact_service_request(problem_key);


CREATE INDEX IF NOT EXISTS idx_fact_service_request_location

ON gold.fact_service_request(location_key);


CREATE INDEX IF NOT EXISTS idx_fact_service_request_status

ON gold.fact_service_request(status);


-- ============================================================
-- END OF GOLD MODEL
-- ============================================================
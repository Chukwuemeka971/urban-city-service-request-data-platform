INSERT INTO gold.fact_service_request (
    request_id,
    created_date_key,
    closed_date_key,
    agency_key,
    problem_key,
    location_key,
    status,
    resolution_hours,
    is_closed
)
SELECT
    s.request_id,

    TO_CHAR(s.created_date::DATE, 'YYYYMMDD')::INTEGER
        AS created_date_key,

    CASE
        WHEN s.closed_date IS NOT NULL
        THEN TO_CHAR(s.closed_date::DATE, 'YYYYMMDD')::INTEGER
        ELSE NULL
    END AS closed_date_key,

    a.agency_key,

    p.problem_key,

    l.location_key,

    s.status,

    CASE
        WHEN s.closed_date IS NOT NULL
        THEN EXTRACT(
            EPOCH FROM (s.closed_date - s.created_date)
        ) / 3600.0
        ELSE NULL
    END AS resolution_hours,

    CASE
        WHEN s.status = 'Closed'
        THEN TRUE
        ELSE FALSE
    END AS is_closed

FROM staging.urban_city_requests s

LEFT JOIN gold.dim_agency a
    ON a.agency_name = s.agency

LEFT JOIN gold.dim_problem p
    ON p.problem = s.problem
   AND p.problem_detail IS NOT DISTINCT FROM s.problem_detail

LEFT JOIN gold.dim_location l
    ON l.location_type IS NOT DISTINCT FROM s.location_type
   AND l.incident_address IS NOT DISTINCT FROM s.incident_address
   AND l.city IS NOT DISTINCT FROM s.city
   AND l.borough IS NOT DISTINCT FROM s.borough
   AND l.latitude IS NOT DISTINCT FROM s.latitude
   AND l.longitude IS NOT DISTINCT FROM s.longitude

WHERE NOT EXISTS (
    SELECT 1
    FROM gold.fact_service_request f
    WHERE f.request_id = s.request_id
);
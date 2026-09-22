INSERT INTO gold.dim_location (
    location_type,
    incident_address,
    city,
    borough,
    latitude,
    longitude
)
SELECT DISTINCT
    location_type,
    incident_address,
    city,
    borough,
    latitude,
    longitude
FROM staging.urban_city_requests s
WHERE NOT EXISTS (
    SELECT 1
    FROM gold.dim_location d
    WHERE d.location_type IS NOT DISTINCT FROM s.location_type
      AND d.incident_address IS NOT DISTINCT FROM s.incident_address
      AND d.city IS NOT DISTINCT FROM s.city
      AND d.borough IS NOT DISTINCT FROM s.borough
      AND d.latitude IS NOT DISTINCT FROM s.latitude
      AND d.longitude IS NOT DISTINCT FROM s.longitude
);
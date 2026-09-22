INSERT INTO gold.dim_agency (agency_name)
SELECT DISTINCT
    agency
FROM staging.urban_city_requests
WHERE agency IS NOT NULL
  AND NOT EXISTS (
      SELECT 1
      FROM gold.dim_agency d
      WHERE d.agency_name = staging.urban_city_requests.agency
  );
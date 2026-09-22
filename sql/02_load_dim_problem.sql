INSERT INTO gold.dim_problem (
    problem,
    problem_detail
)
SELECT DISTINCT
    problem,
    problem_detail
FROM staging.urban_city_requests
WHERE problem IS NOT NULL
  AND NOT EXISTS (
      SELECT 1
      FROM gold.dim_problem d
      WHERE d.problem = staging.urban_city_requests.problem
        AND d.problem_detail IS NOT DISTINCT FROM staging.urban_city_requests.problem_detail
  );
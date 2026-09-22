INSERT INTO gold.dim_date (
    date_key,
    full_date,
    year,
    quarter,
    month,
    month_name,
    day,
    day_of_week,
    day_name
)
SELECT DISTINCT
    TO_CHAR(request_date, 'YYYYMMDD')::INTEGER AS date_key,
    request_date AS full_date,
    EXTRACT(YEAR FROM request_date)::INTEGER AS year,
    EXTRACT(QUARTER FROM request_date)::INTEGER AS quarter,
    EXTRACT(MONTH FROM request_date)::INTEGER AS month,
    TO_CHAR(request_date, 'Month') AS month_name,
    EXTRACT(DAY FROM request_date)::INTEGER AS day,
    EXTRACT(ISODOW FROM request_date)::INTEGER AS day_of_week,
    TO_CHAR(request_date, 'Day') AS day_name
FROM (
    SELECT created_date::DATE AS request_date
    FROM staging.urban_city_requests
    WHERE created_date IS NOT NULL

    UNION

    SELECT closed_date::DATE AS request_date
    FROM staging.urban_city_requests
    WHERE closed_date IS NOT NULL
) dates
WHERE NOT EXISTS (
    SELECT 1
    FROM gold.dim_date d
    WHERE d.full_date = dates.request_date
);
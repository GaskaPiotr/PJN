-- Tabela o pełnym rozmiarze. Benchmark wykonuje analogiczne zapytania na trzech tabelach.
-- Do pomiaru Execution Time poprzedź SELECT poleceniem EXPLAIN (ANALYZE, BUFFERS, TIMING OFF).

-- Q1: pojedyncze słowo i jego odmiany
SELECT count(*) FROM field_notes_500000
WHERE year BETWEEN 2000 AND 2024 AND search_vector @@ to_tsquery('english', 'restore');

-- Q2: sąsiedztwo i kolejność leksemów
SELECT count(*) FROM field_notes_500000
WHERE year BETWEEN 2000 AND 2024 AND search_vector @@ phraseto_tsquery('english', 'solar panel');

-- Q3: koniunkcja, alternatywa i negacja
SELECT count(*) FROM field_notes_500000
WHERE year BETWEEN 2000 AND 2024
  AND search_vector @@ to_tsquery('english', 'habitat & (wetland | marsh) & !invasive');

-- LIKE dla Q1
SELECT count(*) FROM field_notes_500000
WHERE year BETWEEN 2000 AND 2024 AND (lower(title) LIKE '%restore%' OR lower(body) LIKE '%restore%');

-- Ranking Q1. Dla Q2 i Q3 użyj wyrażeń tsquery z odpowiednich zapytań.
WITH query AS (SELECT to_tsquery('english', 'restore') AS expression)
SELECT id, title, category, region, year, ts_rank_cd(search_vector, expression) AS score
FROM field_notes_500000 CROSS JOIN query
WHERE year BETWEEN 2000 AND 2024 AND search_vector @@ expression
ORDER BY score DESC, id ASC LIMIT 10;

-- Trzy agregacje badania facetów Q3
SELECT category, count(*) FROM field_notes_500000
WHERE year BETWEEN 2000 AND 2024 AND search_vector @@ to_tsquery('english', 'habitat & (wetland | marsh) & !invasive')
GROUP BY 1 ORDER BY 1;
SELECT region, count(*) FROM field_notes_500000
WHERE year BETWEEN 2000 AND 2024 AND search_vector @@ to_tsquery('english', 'habitat & (wetland | marsh) & !invasive')
GROUP BY 1 ORDER BY 1;
SELECT 2000 + 5 * ((year - 2000) / 5) AS bucket, count(*) FROM field_notes_500000
WHERE year BETWEEN 2000 AND 2024 AND search_vector @@ to_tsquery('english', 'habitat & (wetland | marsh) & !invasive')
GROUP BY 1 ORDER BY 1;

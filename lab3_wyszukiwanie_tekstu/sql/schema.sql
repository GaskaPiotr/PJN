CREATE TABLE {table} (
    id integer PRIMARY KEY,
    title text NOT NULL,
    body text NOT NULL,
    category text NOT NULL,
    region text NOT NULL,
    year smallint NOT NULL,
    search_vector tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('english', title), 'A')
        || to_tsvector('simple', 'documentsectionboundary')
        || setweight(to_tsvector('english', body), 'D')
    ) STORED
);

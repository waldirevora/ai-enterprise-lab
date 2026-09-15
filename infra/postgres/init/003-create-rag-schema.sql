CREATE TABLE IF NOT EXISTS rag_documents (
    id BIGSERIAL PRIMARY KEY,

    title TEXT NOT NULL,
    source TEXT NOT NULL,
    source_uri TEXT,

    classification TEXT NOT NULL DEFAULT 'internal'
        CHECK (
            classification IN (
                'public',
                'internal',
                'confidential'
            )
        ),

    content_hash TEXT NOT NULL,

    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (source, content_hash)
);


CREATE TABLE IF NOT EXISTS rag_document_chunks (
    id BIGSERIAL PRIMARY KEY,

    document_id BIGINT NOT NULL
        REFERENCES rag_documents(id)
        ON DELETE CASCADE,

    chunk_index INTEGER NOT NULL
        CHECK (chunk_index >= 0),

    content TEXT NOT NULL,

    token_count INTEGER
        CHECK (
            token_count IS NULL
            OR token_count >= 0
        ),

    embedding VECTOR(1024) NOT NULL,

    embedding_model TEXT NOT NULL,

    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (
        document_id,
        chunk_index
    )
);


CREATE INDEX IF NOT EXISTS idx_rag_documents_classification
    ON rag_documents (classification);


CREATE INDEX IF NOT EXISTS idx_rag_documents_source
    ON rag_documents (source);


CREATE INDEX IF NOT EXISTS idx_rag_chunks_document_id
    ON rag_document_chunks (document_id);


CREATE INDEX IF NOT EXISTS idx_rag_chunks_embedding_hnsw
    ON rag_document_chunks
    USING hnsw (
        embedding vector_cosine_ops
    );
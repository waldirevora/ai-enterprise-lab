CREATE TABLE IF NOT EXISTS organizations (
    id BIGSERIAL PRIMARY KEY,

    slug TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,

    status TEXT NOT NULL DEFAULT 'active'
        CHECK (
            status IN (
                'active',
                'disabled'
            )
        ),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


CREATE TABLE IF NOT EXISTS principals (
    id BIGSERIAL PRIMARY KEY,

    kind TEXT NOT NULL
        CHECK (
            kind IN (
                'user',
                'service'
            )
        ),

    display_name TEXT NOT NULL,

    auth_provider TEXT,
    external_subject TEXT,

    status TEXT NOT NULL DEFAULT 'active'
        CHECK (
            status IN (
                'active',
                'disabled'
            )
        ),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


CREATE UNIQUE INDEX IF NOT EXISTS idx_principals_external_identity
    ON principals (
        auth_provider,
        external_subject
    )
    WHERE external_subject IS NOT NULL;


CREATE TABLE IF NOT EXISTS organization_memberships (
    organization_id BIGINT NOT NULL
        REFERENCES organizations(id)
        ON DELETE CASCADE,

    principal_id BIGINT NOT NULL
        REFERENCES principals(id)
        ON DELETE CASCADE,

    role TEXT NOT NULL
        CHECK (
            role IN (
                'owner',
                'admin',
                'member',
                'service'
            )
        ),

    max_classification TEXT NOT NULL DEFAULT 'public'
        CHECK (
            max_classification IN (
                'public',
                'internal',
                'confidential'
            )
        ),

    status TEXT NOT NULL DEFAULT 'active'
        CHECK (
            status IN (
                'active',
                'disabled'
            )
        ),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (
        organization_id,
        principal_id
    )
);


CREATE INDEX IF NOT EXISTS idx_memberships_principal
    ON organization_memberships (
        principal_id
    );


CREATE TABLE IF NOT EXISTS api_credentials (
    id BIGSERIAL PRIMARY KEY,

    organization_id BIGINT NOT NULL,
    principal_id BIGINT NOT NULL,

    name TEXT NOT NULL,

    key_prefix TEXT NOT NULL,

    secret_hash CHAR(64) NOT NULL UNIQUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    last_used_at TIMESTAMPTZ,

    FOREIGN KEY (
        organization_id,
        principal_id
    )
    REFERENCES organization_memberships (
        organization_id,
        principal_id
    )
    ON DELETE CASCADE
);


CREATE INDEX IF NOT EXISTS idx_api_credentials_prefix
    ON api_credentials (
        key_prefix
    );


CREATE INDEX IF NOT EXISTS idx_api_credentials_active
    ON api_credentials (
        organization_id,
        principal_id
    )
    WHERE revoked_at IS NULL;


-- Organização inicial do laboratório.
-- Nenhuma credencial ou usuário administrador é criado
-- automaticamente pela migration.
INSERT INTO organizations (
    slug,
    name
)
VALUES (
    'lab-default',
    'AI Enterprise Lab'
)
ON CONFLICT (slug)
DO NOTHING;


-- Todo documento RAG passa a ter um proprietário organizacional.
ALTER TABLE rag_documents
    ADD COLUMN IF NOT EXISTS organization_id BIGINT;


UPDATE rag_documents
SET organization_id = (
    SELECT id
    FROM organizations
    WHERE slug = 'lab-default'
)
WHERE organization_id IS NULL;


ALTER TABLE rag_documents
    ALTER COLUMN organization_id SET NOT NULL;


DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'rag_documents_organization_id_fkey'
    ) THEN
        ALTER TABLE rag_documents
            ADD CONSTRAINT rag_documents_organization_id_fkey
            FOREIGN KEY (organization_id)
            REFERENCES organizations(id)
            ON DELETE RESTRICT;
    END IF;
END
$$;


CREATE INDEX IF NOT EXISTS idx_rag_documents_organization
    ON rag_documents (
        organization_id
    );


-- A deduplicação anterior era global.
-- Em ambiente multiempresa ela precisa ser por organização.
ALTER TABLE rag_documents
    DROP CONSTRAINT IF EXISTS rag_documents_source_content_hash_key;


CREATE UNIQUE INDEX IF NOT EXISTS idx_rag_documents_org_source_hash
    ON rag_documents (
        organization_id,
        source,
        content_hash
    );


ALTER TABLE rag_documents
    ADD COLUMN IF NOT EXISTS created_by_principal_id BIGINT;


DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'rag_documents_created_by_principal_id_fkey'
    ) THEN
        ALTER TABLE rag_documents
            ADD CONSTRAINT rag_documents_created_by_principal_id_fkey
            FOREIGN KEY (created_by_principal_id)
            REFERENCES principals(id)
            ON DELETE SET NULL;
    END IF;
END
$$;
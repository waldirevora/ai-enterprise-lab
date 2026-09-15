BEGIN;


-- ============================================================
-- Organizational Units
-- ============================================================

CREATE TABLE organizational_units (
    id BIGSERIAL PRIMARY KEY,

    organization_id BIGINT NOT NULL,

    parent_unit_id BIGINT NULL,

    slug TEXT NOT NULL,

    name TEXT NOT NULL,

    status TEXT NOT NULL
        DEFAULT 'active',

    created_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT organizational_units_status_check
        CHECK (
            status IN (
                'active',
                'disabled'
            )
        ),

    CONSTRAINT organizational_units_slug_not_blank
        CHECK (
            btrim(slug) <> ''
        ),

    CONSTRAINT organizational_units_name_not_blank
        CHECK (
            btrim(name) <> ''
        ),

    CONSTRAINT organizational_units_parent_not_self
        CHECK (
            parent_unit_id IS NULL
            OR parent_unit_id <> id
        ),

    CONSTRAINT organizational_units_organization_fk
        FOREIGN KEY (
            organization_id
        )
        REFERENCES organizations(id)
        ON DELETE CASCADE,

    CONSTRAINT organizational_units_org_slug_key
        UNIQUE (
            organization_id,
            slug
        ),

    -- Necessário para FKs compostas que também
    -- garantem isolamento por organization.
    CONSTRAINT organizational_units_org_id_id_key
        UNIQUE (
            organization_id,
            id
        ),

    -- Um parent sempre deve pertencer à mesma
    -- organização da unidade filha.
    CONSTRAINT organizational_units_parent_same_org_fk
        FOREIGN KEY (
            organization_id,
            parent_unit_id
        )
        REFERENCES organizational_units (
            organization_id,
            id
        )
        ON DELETE RESTRICT
);


CREATE INDEX idx_organizational_units_organization
    ON organizational_units (
        organization_id
    );


CREATE INDEX idx_organizational_units_parent
    ON organizational_units (
        organization_id,
        parent_unit_id
    )
    WHERE parent_unit_id IS NOT NULL;


-- ============================================================
-- Principal memberships inside organizational units
-- ============================================================

CREATE TABLE principal_unit_memberships (
    organization_id BIGINT NOT NULL,

    organizational_unit_id BIGINT NOT NULL,

    principal_id BIGINT NOT NULL,

    role TEXT NOT NULL
        DEFAULT 'member',

    max_classification TEXT NOT NULL
        DEFAULT 'public',

    status TEXT NOT NULL
        DEFAULT 'active',

    created_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT principal_unit_memberships_pkey
        PRIMARY KEY (
            organization_id,
            organizational_unit_id,
            principal_id
        ),

    CONSTRAINT principal_unit_memberships_role_check
        CHECK (
            role IN (
                'manager',
                'member',
                'service'
            )
        ),

    CONSTRAINT principal_unit_memberships_classification_check
        CHECK (
            max_classification IN (
                'public',
                'internal',
                'confidential'
            )
        ),

    CONSTRAINT principal_unit_memberships_status_check
        CHECK (
            status IN (
                'active',
                'disabled'
            )
        ),

    -- Garante que a unidade pertence à mesma organization.
    CONSTRAINT principal_unit_memberships_unit_fk
        FOREIGN KEY (
            organization_id,
            organizational_unit_id
        )
        REFERENCES organizational_units (
            organization_id,
            id
        )
        ON DELETE CASCADE,

    -- Garante que o principal já pertence à mesma organization.
    CONSTRAINT principal_unit_memberships_org_membership_fk
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


CREATE INDEX idx_principal_unit_memberships_principal
    ON principal_unit_memberships (
        principal_id,
        organization_id
    );


CREATE INDEX idx_principal_unit_memberships_unit
    ON principal_unit_memberships (
        organization_id,
        organizational_unit_id
    );


-- ============================================================
-- RAG document organizational-unit scope
-- ============================================================

ALTER TABLE rag_documents
    ADD COLUMN organizational_unit_id BIGINT NULL;


-- Composite FK intentionally includes organization_id.
-- This prevents a document from organization A from being
-- associated with a unit belonging to organization B.
ALTER TABLE rag_documents
    ADD CONSTRAINT rag_documents_org_unit_fk
        FOREIGN KEY (
            organization_id,
            organizational_unit_id
        )
        REFERENCES organizational_units (
            organization_id,
            id
        )
        ON DELETE RESTRICT;


CREATE INDEX idx_rag_documents_org_unit
    ON rag_documents (
        organization_id,
        organizational_unit_id
    );


-- ============================================================
-- RAG deduplication rules
-- ============================================================

-- Previous tenant-only unique index.
DROP INDEX IF EXISTS
    idx_rag_documents_org_source_hash;


-- Corporate / organization-wide documents.
--
-- organizational_unit_id IS NULL means the document belongs
-- to the organization as a whole.
CREATE UNIQUE INDEX
    idx_rag_documents_corporate_source_hash
    ON rag_documents (
        organization_id,
        source,
        content_hash
    )
    WHERE organizational_unit_id IS NULL;


-- Unit-scoped documents.
--
-- The same content/source can legitimately exist in two
-- different units of the same organization without collision.
CREATE UNIQUE INDEX
    idx_rag_documents_unit_source_hash
    ON rag_documents (
        organization_id,
        organizational_unit_id,
        source,
        content_hash
    )
    WHERE organizational_unit_id IS NOT NULL;


COMMIT;
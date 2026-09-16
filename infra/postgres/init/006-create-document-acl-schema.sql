BEGIN;


-- ============================================================
-- Document ACL Foundation
-- ============================================================
--
-- Authorization hierarchy:
--
-- organization
--   ↓
-- organizational unit
--   ↓
-- classification
--   ↓
-- document ACL
--
-- A document ACL is an additional restriction layer.
-- It must never expand access denied by organization,
-- organizational unit or classification policies.
--
-- access_mode:
--
-- inherited
--   Existing organization/unit/classification rules apply.
--
-- restricted
--   Existing rules apply AND the authenticated principal
--   must have an active document ACL entry with read permission.
-- ============================================================


-- ============================================================
-- 1. Add document access mode
-- ============================================================

ALTER TABLE rag_documents
ADD COLUMN access_mode TEXT;


UPDATE rag_documents
SET access_mode = 'inherited'
WHERE access_mode IS NULL;


ALTER TABLE rag_documents
ALTER COLUMN access_mode
SET DEFAULT 'inherited';


ALTER TABLE rag_documents
ALTER COLUMN access_mode
SET NOT NULL;


ALTER TABLE rag_documents
ADD CONSTRAINT rag_documents_access_mode_check
CHECK (
    access_mode = ANY (
        ARRAY[
            'inherited'::text,
            'restricted'::text
        ]
    )
);


CREATE INDEX idx_rag_documents_org_access_mode
ON rag_documents (
    organization_id,
    access_mode
);


-- ============================================================
-- 2. Composite document identity
-- ============================================================
--
-- The composite UNIQUE constraint allows ACL entries to use
-- (organization_id, document_id) as a foreign key.
--
-- This makes cross-tenant ACL references impossible at the
-- database layer.
-- ============================================================

ALTER TABLE rag_documents
ADD CONSTRAINT rag_documents_org_id_key
UNIQUE (
    organization_id,
    id
);


-- ============================================================
-- 3. Document ACL entries
-- ============================================================
--
-- v1 subject:
--   principal
--
-- v1 permission:
--   read
--
-- status:
--   active
--   disabled
--
-- No explicit DENY rules in this foundation.
--
-- inherited document:
--   ACL table does not add a restriction.
--
-- restricted document:
--   active read ACL for the principal is required.
-- ============================================================

CREATE TABLE rag_document_acl_entries (
    id BIGSERIAL PRIMARY KEY,

    organization_id BIGINT NOT NULL,

    document_id BIGINT NOT NULL,

    principal_id BIGINT NOT NULL,

    permission TEXT NOT NULL
        DEFAULT 'read',

    status TEXT NOT NULL
        DEFAULT 'active',

    created_by_principal_id BIGINT,

    created_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT rag_document_acl_entries_permission_check
        CHECK (
            permission = 'read'
        ),

    CONSTRAINT rag_document_acl_entries_status_check
        CHECK (
            status = ANY (
                ARRAY[
                    'active'::text,
                    'disabled'::text
                ]
            )
        ),

    CONSTRAINT rag_document_acl_entries_organization_fk
        FOREIGN KEY (
            organization_id
        )
        REFERENCES organizations (
            id
        )
        ON DELETE CASCADE,

    CONSTRAINT rag_document_acl_entries_document_fk
        FOREIGN KEY (
            organization_id,
            document_id
        )
        REFERENCES rag_documents (
            organization_id,
            id
        )
        ON DELETE CASCADE,

    CONSTRAINT rag_document_acl_entries_membership_fk
        FOREIGN KEY (
            organization_id,
            principal_id
        )
        REFERENCES organization_memberships (
            organization_id,
            principal_id
        )
        ON DELETE CASCADE,

    CONSTRAINT rag_document_acl_entries_created_by_fk
        FOREIGN KEY (
            created_by_principal_id
        )
        REFERENCES principals (
            id
        )
        ON DELETE SET NULL,

    CONSTRAINT rag_document_acl_entries_unique
        UNIQUE (
            organization_id,
            document_id,
            principal_id,
            permission
        )
);


-- ============================================================
-- 4. Lookup indexes
-- ============================================================

CREATE INDEX idx_rag_document_acl_principal
ON rag_document_acl_entries (
    organization_id,
    principal_id,
    status
);


CREATE INDEX idx_rag_document_acl_document
ON rag_document_acl_entries (
    organization_id,
    document_id,
    status
);


COMMIT;
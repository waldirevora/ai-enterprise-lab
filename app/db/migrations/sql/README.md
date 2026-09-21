# Runtime SQL Migrations

Bootstrap versions `001` through `006` are historical PostgreSQL
initialization scripts and are not stored or executed from this directory.

Runtime migrations start at version `007`.

Filename format:

    007-short-description.sql
    008-next-change.sql

Rules:

- versions are contiguous;
- applied files are immutable;
- checksum changes after application are rejected;
- each migration is recorded only after its SQL succeeds;
- migrations execute under the deployment migration lock;
- destructive automatic down migrations are not supported.

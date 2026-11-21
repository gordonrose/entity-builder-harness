/** App-owned ordered migration source. Target composition supplies the PostgreSQL runner and checksum. */
export const testEntityMigration = {
  id: "v0003_entity_smoke_test_entity",
  statements: [
    { text: "CREATE TABLE IF NOT EXISTS __SCHEMA__.test_entity (id uuid PRIMARY KEY, integer_value bigint NOT NULL, uuid_value uuid NOT NULL, occurred_at timestamptz NOT NULL, label text NOT NULL, status text NOT NULL CHECK (status IN ('draft', 'active', 'closed')), enabled boolean NOT NULL, categories jsonb NOT NULL, notes jsonb NOT NULL, description text NULL, reviewed_at timestamptz NULL, secondary_categories jsonb NULL, visibility text NOT NULL CHECK (visibility IN ('active', 'archived')), lifecycle jsonb NOT NULL, created_at timestamptz NOT NULL, updated_at timestamptz NOT NULL)" },
    { text: "CREATE INDEX IF NOT EXISTS test_entity_status_created_at_idx ON __SCHEMA__.test_entity (status, created_at)" },
  ],
} as const;

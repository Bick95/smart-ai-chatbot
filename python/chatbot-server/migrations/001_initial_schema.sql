-- Full schema in one migration (fresh installs / dev resets).
-- Session variable app.current_subject must be set for chat RLS.
-- RLS helpers use SECURITY DEFINER + row_security off to avoid policy recursion.

-- -----------------------------------------------------------------------------
-- Auth (Postgres adapter)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS auth_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_auth_users_email ON auth_users(email);
CREATE INDEX IF NOT EXISTS idx_auth_users_username ON auth_users(username);

-- -----------------------------------------------------------------------------
-- Chats, folders, messages, sharing
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS chat_folders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_subject VARCHAR(64) NOT NULL,
    parent_id UUID REFERENCES chat_folders(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    system_prompt TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS chats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_subject VARCHAR(64) NOT NULL,
    folder_id UUID REFERENCES chat_folders(id) ON DELETE SET NULL,
    title VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_id UUID NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS chat_permissions (
    chat_id UUID NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
    subject VARCHAR(64) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('viewer', 'editor')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (chat_id, subject)
);

CREATE INDEX IF NOT EXISTS idx_chat_folders_owner ON chat_folders(owner_subject);
CREATE INDEX IF NOT EXISTS idx_chat_folders_parent ON chat_folders(parent_id);
CREATE INDEX IF NOT EXISTS idx_chats_owner ON chats(owner_subject);
CREATE INDEX IF NOT EXISTS idx_chats_folder ON chats(folder_id);
CREATE INDEX IF NOT EXISTS idx_chats_updated_at ON chats(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_chat_messages_chat_id ON chat_messages(chat_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(chat_id, created_at);
CREATE INDEX IF NOT EXISTS idx_chat_permissions_subject ON chat_permissions(subject);

-- -----------------------------------------------------------------------------
-- Row level security (enforce even for table owners)
-- -----------------------------------------------------------------------------
ALTER TABLE chat_folders ENABLE ROW LEVEL SECURITY;
ALTER TABLE chats ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_permissions ENABLE ROW LEVEL SECURITY;

ALTER TABLE chat_folders FORCE ROW LEVEL SECURITY;
ALTER TABLE chats FORCE ROW LEVEL SECURITY;
ALTER TABLE chat_messages FORCE ROW LEVEL SECURITY;
ALTER TABLE chat_permissions FORCE ROW LEVEL SECURITY;

-- -----------------------------------------------------------------------------
-- RLS helpers (no cross-table policy recursion)
-- -----------------------------------------------------------------------------
-- Folder visibility is owner-only. Chat shares do NOT grant access to chat_folders rows.
CREATE OR REPLACE FUNCTION rls_folder_visible(p_folder_id uuid)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
SET row_security = off
AS $$
  SELECT COALESCE(
    EXISTS (
      SELECT 1 FROM chat_folders f
      WHERE f.id = p_folder_id
        AND f.owner_subject = current_setting('app.current_subject', true)
    ),
    false
  );
$$;

CREATE OR REPLACE FUNCTION rls_folder_visible_for_update(p_folder_id uuid)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
SET row_security = off
AS $$
  SELECT COALESCE(
    EXISTS (
      SELECT 1 FROM chat_folders f
      WHERE f.id = p_folder_id
        AND f.owner_subject = current_setting('app.current_subject', true)
    ),
    false
  );
$$;

CREATE OR REPLACE FUNCTION rls_subject_can_read_chat(p_chat_id uuid)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
SET row_security = off
AS $$
  SELECT COALESCE(
    EXISTS (
      SELECT 1 FROM chats c
      WHERE c.id = p_chat_id
        AND (
          c.owner_subject = current_setting('app.current_subject', true)
          OR EXISTS (
            SELECT 1 FROM chat_permissions cp
            WHERE cp.chat_id = c.id
              AND cp.subject = current_setting('app.current_subject', true)
          )
        )
    ),
    false
  );
$$;

CREATE OR REPLACE FUNCTION rls_subject_can_write_message(p_chat_id uuid)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
SET row_security = off
AS $$
  SELECT COALESCE(
    EXISTS (
      SELECT 1 FROM chats c
      WHERE c.id = p_chat_id
        AND (
          c.owner_subject = current_setting('app.current_subject', true)
          OR EXISTS (
            SELECT 1 FROM chat_permissions cp
            WHERE cp.chat_id = c.id
              AND cp.subject = current_setting('app.current_subject', true)
              AND cp.role = 'editor'
          )
        )
    ),
    false
  );
$$;

CREATE OR REPLACE FUNCTION rls_is_chat_owner_of(p_chat_id uuid)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
SET row_security = off
AS $$
  SELECT COALESCE(
    EXISTS (
      SELECT 1 FROM chats c
      WHERE c.id = p_chat_id
        AND c.owner_subject = current_setting('app.current_subject', true)
    ),
    false
  );
$$;

-- -----------------------------------------------------------------------------
-- Policies
-- -----------------------------------------------------------------------------
-- Same pattern as chats_select: INSERT...RETURNING must not rely only on a helper
-- that SELECTs chat_folders by id (new row not visible in that subquery yet).
CREATE POLICY chat_folders_select ON chat_folders
    FOR SELECT USING (
        CASE
            WHEN owner_subject = current_setting('app.current_subject', true) THEN true
            ELSE rls_folder_visible(id)
        END
    );

CREATE POLICY chat_folders_insert ON chat_folders
    FOR INSERT WITH CHECK (
        owner_subject = current_setting('app.current_subject', true)
    );

CREATE POLICY chat_folders_update ON chat_folders
    FOR UPDATE USING (rls_folder_visible_for_update(id));

CREATE POLICY chat_folders_delete ON chat_folders
    FOR DELETE USING (
        owner_subject = current_setting('app.current_subject', true)
    );

-- Owner branch must not call rls_subject_can_read_chat(id): that function SELECTs
-- chats by id, which is not visible during INSERT...RETURNING for the same row.
-- Shared access still uses the SECURITY DEFINER helper (reads permissions with RLS off).
CREATE POLICY chats_select ON chats
    FOR SELECT USING (
        CASE
            WHEN owner_subject = current_setting('app.current_subject', true) THEN true
            ELSE rls_subject_can_read_chat(id)
        END
    );

CREATE POLICY chats_insert ON chats
    FOR INSERT WITH CHECK (
        owner_subject = current_setting('app.current_subject', true)
    );

CREATE POLICY chats_update ON chats
    FOR UPDATE USING (
        owner_subject = current_setting('app.current_subject', true)
    );

CREATE POLICY chats_delete ON chats
    FOR DELETE USING (
        owner_subject = current_setting('app.current_subject', true)
    );

CREATE POLICY chat_messages_select ON chat_messages
    FOR SELECT USING (rls_subject_can_read_chat(chat_id));

CREATE POLICY chat_messages_insert ON chat_messages
    FOR INSERT WITH CHECK (rls_subject_can_write_message(chat_id));

CREATE POLICY chat_messages_delete ON chat_messages
    FOR DELETE USING (rls_subject_can_write_message(chat_id));

CREATE POLICY chat_permissions_select ON chat_permissions
    FOR SELECT USING (rls_is_chat_owner_of(chat_id));

CREATE POLICY chat_permissions_insert ON chat_permissions
    FOR INSERT WITH CHECK (rls_is_chat_owner_of(chat_id));

CREATE POLICY chat_permissions_update ON chat_permissions
    FOR UPDATE USING (rls_is_chat_owner_of(chat_id));

CREATE POLICY chat_permissions_delete ON chat_permissions
    FOR DELETE USING (rls_is_chat_owner_of(chat_id));

-- -----------------------------------------------------------------------------
-- Triggers: only owner may change owner_subject
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION check_owner_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.owner_subject IS DISTINCT FROM NEW.owner_subject THEN
        IF current_setting('app.current_subject', true) IS NULL
           OR OLD.owner_subject != current_setting('app.current_subject', true) THEN
            RAISE EXCEPTION 'Only the owner can change ownership';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER chats_owner_change_check
    BEFORE UPDATE ON chats
    FOR EACH ROW EXECUTE FUNCTION check_owner_change();

CREATE TRIGGER chat_folders_owner_change_check
    BEFORE UPDATE ON chat_folders
    FOR EACH ROW EXECUTE FUNCTION check_owner_change();

-- -----------------------------------------------------------------------------
-- Least-privileged runtime role (password set from env after migrations; see migrations.py)
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'chatbot_app') THEN
        CREATE ROLE chatbot_app WITH LOGIN
            NOSUPERUSER
            NOBYPASSRLS
            NOCREATEDB
            NOCREATEROLE
            NOREPLICATION;
    END IF;
END$$;

DO $$
BEGIN
    EXECUTE format(
        'GRANT CONNECT ON DATABASE %I TO chatbot_app',
        current_database()
    );
END$$;

GRANT USAGE ON SCHEMA public TO chatbot_app;

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO chatbot_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO chatbot_app;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO chatbot_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO chatbot_app;

GRANT EXECUTE ON FUNCTION rls_folder_visible(uuid) TO chatbot_app;
GRANT EXECUTE ON FUNCTION rls_folder_visible_for_update(uuid) TO chatbot_app;
GRANT EXECUTE ON FUNCTION rls_subject_can_read_chat(uuid) TO chatbot_app;
GRANT EXECUTE ON FUNCTION rls_subject_can_write_message(uuid) TO chatbot_app;
GRANT EXECUTE ON FUNCTION rls_is_chat_owner_of(uuid) TO chatbot_app;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT EXECUTE ON FUNCTIONS TO chatbot_app;

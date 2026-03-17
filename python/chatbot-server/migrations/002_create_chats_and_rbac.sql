-- App data: chats, messages, folders, RBAC (subject-based authorization)
-- Session variables: app.current_subject_type, app.current_subject_id must be set before queries for RLS

-- Folders (nested: parent_id self-reference; NULL = root)
CREATE TABLE IF NOT EXISTS chat_folders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_subject_type VARCHAR(50) NOT NULL,
    owner_subject_id UUID NOT NULL,
    parent_id UUID REFERENCES chat_folders(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    system_prompt TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Chats table (folder_id NULL = uncategorized/root; title optional)
CREATE TABLE IF NOT EXISTS chats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_subject_type VARCHAR(50) NOT NULL,
    owner_subject_id UUID NOT NULL,
    folder_id UUID REFERENCES chat_folders(id) ON DELETE SET NULL,
    title VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Chat messages
CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_id UUID NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Sharing (RBAC)
CREATE TABLE IF NOT EXISTS chat_permissions (
    chat_id UUID NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
    subject_type VARCHAR(50) NOT NULL,
    subject_id UUID NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('viewer', 'editor')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (chat_id, subject_type, subject_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_chat_folders_owner ON chat_folders(owner_subject_type, owner_subject_id);
CREATE INDEX IF NOT EXISTS idx_chat_folders_parent ON chat_folders(parent_id);
CREATE INDEX IF NOT EXISTS idx_chats_owner ON chats(owner_subject_type, owner_subject_id);
CREATE INDEX IF NOT EXISTS idx_chats_folder ON chats(folder_id);
CREATE INDEX IF NOT EXISTS idx_chats_updated_at ON chats(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_chat_messages_chat_id ON chat_messages(chat_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(chat_id, created_at);
CREATE INDEX IF NOT EXISTS idx_chat_permissions_subject ON chat_permissions(subject_type, subject_id);

-- RLS: enable on all tables
ALTER TABLE chat_folders ENABLE ROW LEVEL SECURITY;
ALTER TABLE chats ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_permissions ENABLE ROW LEVEL SECURITY;

-- chat_folders: owner only for INSERT/DELETE; SELECT/UPDATE also for viewer/editor of chats in folder
CREATE POLICY chat_folders_select ON chat_folders
    FOR SELECT USING (
        (owner_subject_type = current_setting('app.current_subject_type', true)
         AND owner_subject_id = (current_setting('app.current_subject_id', true)::uuid))
        OR EXISTS (
            SELECT 1 FROM chats c
            JOIN chat_permissions cp ON cp.chat_id = c.id
            WHERE c.folder_id = chat_folders.id
            AND cp.subject_type = current_setting('app.current_subject_type', true)
            AND cp.subject_id = (current_setting('app.current_subject_id', true)::uuid)
        )
    );

CREATE POLICY chat_folders_insert ON chat_folders
    FOR INSERT WITH CHECK (
        owner_subject_type = current_setting('app.current_subject_type', true)
        AND owner_subject_id = (current_setting('app.current_subject_id', true)::uuid)
    );

CREATE POLICY chat_folders_update ON chat_folders
    FOR UPDATE USING (
        (owner_subject_type = current_setting('app.current_subject_type', true)
         AND owner_subject_id = (current_setting('app.current_subject_id', true)::uuid))
        OR EXISTS (
            SELECT 1 FROM chats c
            JOIN chat_permissions cp ON cp.chat_id = c.id
            WHERE c.folder_id = chat_folders.id
            AND cp.subject_type = current_setting('app.current_subject_type', true)
            AND cp.subject_id = (current_setting('app.current_subject_id', true)::uuid)
            AND cp.role = 'editor'
        )
    );

CREATE POLICY chat_folders_delete ON chat_folders
    FOR DELETE USING (
        owner_subject_type = current_setting('app.current_subject_type', true)
        AND owner_subject_id = (current_setting('app.current_subject_id', true)::uuid)
    );

-- chats: SELECT if owner or shared; INSERT/UPDATE/DELETE owner only
CREATE POLICY chats_select ON chats
    FOR SELECT USING (
        (owner_subject_type = current_setting('app.current_subject_type', true)
         AND owner_subject_id = (current_setting('app.current_subject_id', true)::uuid))
        OR EXISTS (
            SELECT 1 FROM chat_permissions cp
            WHERE cp.chat_id = chats.id
            AND cp.subject_type = current_setting('app.current_subject_type', true)
            AND cp.subject_id = (current_setting('app.current_subject_id', true)::uuid)
        )
    );

CREATE POLICY chats_insert ON chats
    FOR INSERT WITH CHECK (
        owner_subject_type = current_setting('app.current_subject_type', true)
        AND owner_subject_id = (current_setting('app.current_subject_id', true)::uuid)
    );

CREATE POLICY chats_update ON chats
    FOR UPDATE USING (
        owner_subject_type = current_setting('app.current_subject_type', true)
        AND owner_subject_id = (current_setting('app.current_subject_id', true)::uuid)
    );

CREATE POLICY chats_delete ON chats
    FOR DELETE USING (
        owner_subject_type = current_setting('app.current_subject_type', true)
        AND owner_subject_id = (current_setting('app.current_subject_id', true)::uuid)
    );

-- chat_messages: SELECT if chat accessible; INSERT/DELETE if owner or editor
CREATE POLICY chat_messages_select ON chat_messages
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM chats c
            WHERE c.id = chat_messages.chat_id
            AND (
                (c.owner_subject_type = current_setting('app.current_subject_type', true)
                 AND c.owner_subject_id = (current_setting('app.current_subject_id', true)::uuid))
                OR EXISTS (
                    SELECT 1 FROM chat_permissions cp
                    WHERE cp.chat_id = c.id
                    AND cp.subject_type = current_setting('app.current_subject_type', true)
                    AND cp.subject_id = (current_setting('app.current_subject_id', true)::uuid)
                )
            )
        )
    );

CREATE POLICY chat_messages_insert ON chat_messages
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM chats c
            WHERE c.id = chat_messages.chat_id
            AND (
                (c.owner_subject_type = current_setting('app.current_subject_type', true)
                 AND c.owner_subject_id = (current_setting('app.current_subject_id', true)::uuid))
                OR EXISTS (
                    SELECT 1 FROM chat_permissions cp
                    WHERE cp.chat_id = c.id
                    AND cp.subject_type = current_setting('app.current_subject_type', true)
                    AND cp.subject_id = (current_setting('app.current_subject_id', true)::uuid)
                    AND cp.role = 'editor'
                )
            )
        )
    );

CREATE POLICY chat_messages_delete ON chat_messages
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM chats c
            WHERE c.id = chat_messages.chat_id
            AND (
                (c.owner_subject_type = current_setting('app.current_subject_type', true)
                 AND c.owner_subject_id = (current_setting('app.current_subject_id', true)::uuid))
                OR EXISTS (
                    SELECT 1 FROM chat_permissions cp
                    WHERE cp.chat_id = c.id
                    AND cp.subject_type = current_setting('app.current_subject_type', true)
                    AND cp.subject_id = (current_setting('app.current_subject_id', true)::uuid)
                    AND cp.role = 'editor'
                )
            )
        )
    );

-- chat_permissions: owner only (to manage shares)
CREATE POLICY chat_permissions_select ON chat_permissions
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM chats c
            WHERE c.id = chat_permissions.chat_id
            AND c.owner_subject_type = current_setting('app.current_subject_type', true)
            AND c.owner_subject_id = (current_setting('app.current_subject_id', true)::uuid)
        )
    );

CREATE POLICY chat_permissions_insert ON chat_permissions
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM chats c
            WHERE c.id = chat_permissions.chat_id
            AND c.owner_subject_type = current_setting('app.current_subject_type', true)
            AND c.owner_subject_id = (current_setting('app.current_subject_id', true)::uuid)
        )
    );

CREATE POLICY chat_permissions_update ON chat_permissions
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM chats c
            WHERE c.id = chat_permissions.chat_id
            AND c.owner_subject_type = current_setting('app.current_subject_type', true)
            AND c.owner_subject_id = (current_setting('app.current_subject_id', true)::uuid)
        )
    );

CREATE POLICY chat_permissions_delete ON chat_permissions
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM chats c
            WHERE c.id = chat_permissions.chat_id
            AND c.owner_subject_type = current_setting('app.current_subject_type', true)
            AND c.owner_subject_id = (current_setting('app.current_subject_id', true)::uuid)
        )
    );

-- Trigger: only the owner can change owner_subject_type or owner_subject_id
CREATE OR REPLACE FUNCTION check_owner_change()
RETURNS TRIGGER AS $$
BEGIN
    IF (OLD.owner_subject_type IS DISTINCT FROM NEW.owner_subject_type
        OR OLD.owner_subject_id IS DISTINCT FROM NEW.owner_subject_id) THEN
        IF current_setting('app.current_subject_type', true) IS NULL
           OR current_setting('app.current_subject_id', true) IS NULL
           OR OLD.owner_subject_type != current_setting('app.current_subject_type', true)
           OR OLD.owner_subject_id != (current_setting('app.current_subject_id', true)::uuid) THEN
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

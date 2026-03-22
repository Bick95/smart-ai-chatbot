-- Folders are visible only to their owner. Revoke implicit folder access via shared chats.
-- (Replaces helpers from 001 for databases that already applied the initial migration.)

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

# SQL migrations

**`001_initial_schema.sql`** — full schema: auth, chats/folders/messages/permissions, RLS (including `chats_select` / `chat_folders_select` with an owner `CASE` branch so `INSERT … RETURNING` works), `chatbot_app` role, grants.

## Existing database from older migrations

If `_migrations` already lists removed filenames (`001_create_users_table.sql`, …), either:

- **Recreate the database** (simplest), or  
- Drop app objects / truncate and clear `_migrations`, then run migrations again.

Fresh Docker volumes or `docker compose down -v` + `up` work well for local dev.

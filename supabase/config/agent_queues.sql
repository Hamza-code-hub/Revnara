-- Sprint 8 (Agent Runtime Foundation, DB8.2): creates the agent_tasks
-- Supabase Queue (pgmq). Run this once against a real Supabase project's
-- database, as the project's admin/postgres role -- same one-time-
-- provisioning pattern as rag_queues.sql (pgmq.create() requires
-- ownership of the pgmq extension itself; revnara_app deliberately isn't
-- the extension owner).
--
-- Message format (Implementation Plan §11): references only (tenant_id,
-- agent_id, task_input, an opaque resource reference for the domain
-- record the run's output should be written back to) -- never prompts or
-- secrets in the message body, same rule as document_tasks/
-- embedding_tasks.

select pgmq.create('agent_tasks');

grant usage on schema pgmq to revnara_app;
grant create on schema pgmq to revnara_app;
grant all on all tables in schema pgmq to revnara_app;
grant all on all sequences in schema pgmq to revnara_app;
grant execute on all functions in schema pgmq to revnara_app;
alter default privileges in schema pgmq grant all on tables to revnara_app;
alter default privileges in schema pgmq grant execute on functions to revnara_app;

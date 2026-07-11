# Cloud Run Service Configs

Populated incrementally as workers come online: `agent-worker` config stub in Sprint 8, `document-worker`/`embedding-worker` stubs in Sprint 5 (done — `document-worker.yaml`, `embedding-worker.yaml`), full production configs for all five services (`revnara-api`, `revnara-agent-worker`, `revnara-connector-worker`, `revnara-document-worker`, `revnara-notification-worker`) in Sprint 15. All five share the backend's one Docker image with different startup commands (`docs/Revnara_Implementation_Plan.md` §14).

Requires a GCP project (§4 Environment Prerequisites) — not provisioned yet.

**Retry/backoff (DQ5.2):** both document/embedding queues get their retry behavior from pgmq's own visibility-timeout mechanism (`app/rag/queue.py`'s `read()`), not a Cloud Run-level retry config — a message a worker fails to finish processing simply becomes visible to the next `read()` call again once the timeout elapses, rather than being lost or needing a separate DLQ/backoff policy layered on top. See `docs/rag-pattern.md`'s idempotency section for how this combines with `knowledge_chunks`' unique-constraint upsert to avoid duplicate work on retry.
